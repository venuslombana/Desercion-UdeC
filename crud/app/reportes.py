"""Reportes con indicadores, exportación CSV/PDF, tablero real frente a simulado, cola de Bienestar y parámetros.

Aquí están los tres cambios que la simulación llevó al CRUD:
1. Alerta de capacidad de Bienestar (semáforo y cabecera X-Aviso al registrar alertas).
2. Ruta de permanencia integral: cola de casos priorizada con una regla pública y apoyo sugerido por etapa,
   en todos los semestres (antes las alertas solo cubrían los semestres 1 y 2).
3. Tablero que compara los indicadores reales con los proyectados por el escenario elegido.
"""
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from . import negocio, proyecciones, exportacion
from .crud import audit, ser
from .db import get_db
from .models import Alerta, Matricula, PeriodoAcademico, Parametro, TipoApoyo, ApoyoEstudiante, EstudianteFactor, FactorRiesgo
from .security import require

A, O, C = "administrador", "operador", "consulta"
TODOS = (A, O, C)
TASA_BASE = [.204, .117, .087, .076, .074, .060, .054, .033, .023, .024]   # perfil SPADIES usado en el modelo
CALIBRACION = 0.715                                                        # calibración estimada con el CRUD

PARAMETROS_DEFECTO = {
    "capacidad_bienestar": (negocio.CAPACIDAD_RECOMENDADA, "Casos que Bienestar atiende por semestre (escenario E3 recomendado)"),
    "meta_desercion_cohorte": (35.0, "Meta de deserción de cohorte a 10 semestres (%)"),
    "tolerancia_modelo": (negocio.TOLERANCIA_MODELO, "Desviación relativa aceptada entre lo real y lo simulado"),
}


def parametro(db: Session, clave: str) -> float:
    p = db.get(Parametro, clave)
    return p.valor if p else PARAMETROS_DEFECTO[clave][0]


# ------------------------------------------------------------------ reglas usadas por otros módulos
def periodo_en_curso(db: Session) -> PeriodoAcademico | None:
    return db.get(PeriodoAcademico, exportacion.ultimo_periodo_id(db))


def casos_periodo(db: Session, periodo_id: int) -> int:
    """Alertas sin atender del periodo (la cola de Bienestar)."""
    return db.scalar(select(func.count()).select_from(Alerta).join(Matricula, Matricula.id == Alerta.matricula_id)
                     .where(Matricula.periodo_id == periodo_id, Alerta.atendida.is_(False), Alerta.eliminado_en.is_(None))) or 0


def tipos_factor(db: Session, estudiante_id: int, periodo_id: int | None = None) -> list[str]:
    stmt = select(FactorRiesgo.tipo).join(EstudianteFactor, EstudianteFactor.factor_id == FactorRiesgo.id).where(
        EstudianteFactor.estudiante_id == estudiante_id)
    return sorted(set(db.scalars(stmt)))


def tipo_apoyo_para(db: Session, palanca: str) -> TipoApoyo | None:
    return db.scalar(select(TipoApoyo).where(TipoApoyo.palanca == palanca).order_by(TipoApoyo.id))


def despues_de_crear_alerta(db: Session, alerta: Alerta) -> dict:
    """Regla que se ejecuta al registrar una alerta: aviso de capacidad y apoyo sugerido (cambios 1 y 2)."""
    m = db.get(Matricula, alerta.matricula_id)
    est = negocio.estado_capacidad(casos_periodo(db, m.periodo_id), parametro(db, "capacidad_bienestar"))
    palanca = negocio.palanca_sugerida(m.nivel_semestre, tipos_factor(db, m.estudiante_id))
    tipo = tipo_apoyo_para(db, palanca)
    out = {"capacidad": est.__dict__, "palanca_sugerida": palanca, "apoyo_sugerido": tipo.nombre if tipo else None,
           "prioridad": negocio.prioridad(alerta.nivel, m.nivel_semestre, m.materias_basicas_perdidas)}
    if est.semaforo != "verde":
        out["aviso"] = est.mensaje
    return out


# ------------------------------------------------------------------ construcción de reportes
def _periodos_cerrados(db):
    return exportacion.datos(db, "matriculas_por_periodo")[1]


def reporte_desercion_periodo(db: Session) -> dict:
    filas = []
    for per, mat, des, gra in _periodos_cerrados(db):
        filas.append([per, mat, des, gra, round(100 * negocio.tasa(des, mat), 2)])
    tasas = [f[4] for f in filas]
    ult = filas[-1] if filas else [None] * 5
    return {"id": "desercion-periodo", "titulo": "Deserción y matrícula por periodo",
            "descripcion": "Matriculados, desertores y graduados de cada periodo cerrado. Tasa de deserción por periodo = desertores / matriculados (indicador SPADIES).",
            "columnas": ["Periodo", "Matriculados", "Desertan", "Se gradúan", "Deserción por periodo (%)"], "filas": filas,
            "indicadores": [
                {"nombre": "Deserción por periodo, último periodo cerrado", "valor": ult[4], "unidad": "%", "detalle": ult[0]},
                {"nombre": "Deserción por periodo, promedio 2020-1 a la fecha", "valor": round(sum(t for f, t in zip(filas, tasas) if f[0] >= "2020-1") / max(1, sum(1 for f in filas if f[0] >= "2020-1")), 2), "unidad": "%"},
                {"nombre": "Matriculados en el último periodo cerrado", "valor": ult[1], "unidad": "estudiantes"}]}


def reporte_desercion_nivel(db: Session) -> dict:
    filas, tasas = [], []
    for niv, mat, des, gra in exportacion.datos(db, "matriculas_por_nivel")[1]:
        t = negocio.tasa(des, mat)
        modelo = TASA_BASE[niv - 1] * CALIBRACION if niv <= 10 else None
        if niv <= 10:
            tasas.append(t)
        filas.append([niv, mat, des, gra, round(100 * t, 2), round(100 * modelo, 2) if modelo is not None else "—"])
    ret = negocio.retencion_cohorte(tasas)
    temp = 1 - (1 - tasas[0]) * (1 - tasas[1]) if len(tasas) >= 2 else 0
    return {"id": "desercion-nivel", "titulo": "Deserción por semestre que cursa el estudiante",
            "descripcion": "Tasa observada en el CRUD por nivel frente a la tasa del modelo calibrado (perfil SPADIES × 0,715). Los niveles 11 o más son rezago.",
            "columnas": ["Semestre", "Matrículas", "Desertan", "Se gradúan", "Tasa observada (%)", "Tasa del modelo (%)"], "filas": filas,
            "indicadores": [
                {"nombre": "Deserción de cohorte estimada a 10 semestres", "valor": round(100 * (1 - ret), 2), "unidad": "%"},
                {"nombre": "Pérdida en semestres 1 y 2 (fracción de la cohorte)", "valor": round(100 * temp, 2), "unidad": "%"},
                {"nombre": "Meta institucional", "valor": parametro(db, "meta_desercion_cohorte"), "unidad": "%"}]}


def reporte_bienestar(db: Session) -> dict:
    filas = []
    for per, mat12, ale, apo in exportacion.datos(db, "alertas_y_apoyos_por_periodo")[1]:
        filas.append([per, mat12, ale, apo, round(100 * negocio.tasa(ale, mat12), 2), round(100 * min(1, negocio.tasa(apo, ale)), 2)])
    n = max(1, len(filas))
    cap = parametro(db, "capacidad_bienestar")
    prom_ale = sum(f[2] for f in filas) / n
    prom_apo = sum(f[3] for f in filas) / n
    return {"id": "bienestar", "titulo": "Alertas tempranas y atención de Bienestar",
            "descripcion": "Alertas generadas y apoyos asignados por periodo. Cobertura = apoyos / alertas. Tasa de alerta = alertas / matriculados de semestres 1 y 2.",
            "columnas": ["Periodo", "Matriculados sem. 1-2", "Alertas", "Apoyos asignados", "Tasa de alerta (%)", "Cobertura (%)"], "filas": filas,
            "indicadores": [
                {"nombre": "Apoyos asignados por periodo (promedio)", "valor": round(prom_apo, 1), "unidad": "casos"},
                {"nombre": "Alertas por periodo (promedio)", "valor": round(prom_ale, 1), "unidad": "casos"},
                {"nombre": "Ocupación de la capacidad recomendada", "valor": round(100 * prom_ale / cap, 1) if cap else None, "unidad": "%", "detalle": f"capacidad {cap:g} casos/semestre"}]}


def reporte_cohortes(db: Session) -> dict:
    sql = text("""
        SELECT p.codigo, COUNT(DISTINCT e.id),
          COUNT(DISTINCT CASE WHEN m.resultado = 'DESERTA' THEN e.id END),
          COUNT(DISTINCT CASE WHEN m.resultado = 'GRADUA' THEN e.id END)
        FROM estudiante e JOIN cohorte co ON co.id = e.cohorte_id JOIN periodo_academico p ON p.id = co.periodo_ingreso_id
        LEFT JOIN matricula m ON m.estudiante_id = e.id AND m.eliminado_en IS NULL
        WHERE e.eliminado_en IS NULL GROUP BY p.codigo ORDER BY p.codigo""")
    filas = []
    for per, ing, des, gra in db.execute(sql):
        filas.append([per, ing, des, gra, ing - des - gra, round(100 * negocio.tasa(des, ing), 2)])
    completas = [f for f in filas if f[4] <= 0.1 * f[1]]          # cohortes casi cerradas: menos del 10 % sigue activo
    return {"id": "cohortes", "titulo": "Seguimiento de cohortes",
            "descripcion": "Estado de cada cohorte de ingreso: cuántos desertaron, se graduaron o siguen activos. Deserción acumulada = desertores / ingresantes.",
            "columnas": ["Cohorte", "Ingresan", "Desertaron", "Graduados", "Activos", "Deserción acumulada (%)"], "filas": filas,
            "indicadores": [
                {"nombre": "Cohortes con seguimiento", "valor": len(filas), "unidad": "cohortes"},
                {"nombre": "Deserción acumulada promedio de cohortes casi cerradas", "valor": round(sum(f[5] for f in completas) / len(completas), 2) if completas else None, "unidad": "%", "detalle": f"{len(completas)} cohortes con menos del 10 % activo"},
                {"nombre": "Estudiantes activos en total", "valor": sum(f[4] for f in filas), "unidad": "estudiantes"}]}


TITULOS = {"desercion-periodo": "Deserción y matrícula por periodo", "desercion-nivel": "Deserción por semestre",
           "bienestar": "Alertas tempranas y atención de Bienestar", "cohortes": "Seguimiento de cohortes"}
REPORTES = {"desercion-periodo": reporte_desercion_periodo, "desercion-nivel": reporte_desercion_nivel,
            "bienestar": reporte_bienestar, "cohortes": reporte_cohortes}


def a_pdf(rep: dict) -> bytes:
    """Reporte en PDF (tabla con indicadores) usando ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title=rep["titulo"], author="CRUD de seguimiento de la deserción · UdeC")
    st = getSampleStyleSheet()
    el = [Paragraph(rep["titulo"], st["Title"]),
          Paragraph(f"Ingeniería de Sistemas y Computación · Universidad de Cundinamarca, sede Fusagasugá · generado {datetime.now():%Y-%m-%d %H:%M}", st["Normal"]),
          Spacer(1, 6), Paragraph(rep["descripcion"], st["Normal"]), Spacer(1, 10), Paragraph("Indicadores", st["Heading2"])]
    for i in rep["indicadores"]:
        det = f" ({i['detalle']})" if i.get("detalle") else ""
        el.append(Paragraph(f"• <b>{i['nombre']}</b>: {i['valor']} {i['unidad']}{det}", st["Normal"]))
    el += [Spacer(1, 10), Paragraph("Detalle", st["Heading2"])]
    t = Table([rep["columnas"]] + [[str(x) for x in f] for f in rep["filas"]], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b5d3b")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef5f1")]),
                           ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c8d6ce"))]))
    el.append(t)
    doc.build(el)
    return buf.getvalue()


# ------------------------------------------------------------------ endpoints
router = APIRouter(prefix="/api", tags=["reportes"])


@router.get("/reportes")
def listar_reportes(u=Depends(require(*TODOS))):
    """Catálogo de reportes disponibles."""
    return [{"id": k, "titulo": t} for k, t in TITULOS.items()]


@router.get("/reportes/{rid}")
def ver_reporte(rid: str, formato: str = Query("json", pattern="^(json|csv|pdf)$"), db: Session = Depends(get_db), u=Depends(require(*TODOS))):
    """Reporte con indicadores. formato=csv o formato=pdf descarga el archivo."""
    if rid not in REPORTES:
        raise HTTPException(404, f"No existe el reporte «{rid}»")
    rep = REPORTES[rid](db)
    if formato == "csv":
        return Response(exportacion.a_csv(rep["columnas"], rep["filas"]).encode("utf-8-sig"), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="reporte_{rid}.csv"'})
    if formato == "pdf":
        return Response(a_pdf(rep), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="reporte_{rid}.pdf"'})
    return rep


@router.get("/exportacion/historicos")
def exportar_todo(db: Session = Depends(get_db), u=Depends(require(*TODOS))):
    """ZIP con las cinco series históricas que alimentan la simulación (excluye el periodo en curso)."""
    return Response(exportacion.zip_todo(db), media_type="application/zip",
                    headers={"Content-Disposition": 'attachment; filename="historicos_crud.zip"'})


@router.get("/exportacion/historicos/{nombre}")
def exportar_serie(nombre: str, db: Session = Depends(get_db), u=Depends(require(*TODOS))):
    """Una serie histórica en CSV: ingresos_por_cohorte, matriculas_por_nivel, desercion_sem1_por_cohorte,
    alertas_y_apoyos_por_periodo o matriculas_por_periodo."""
    try:
        cab, filas = exportacion.datos(db, nombre)
    except KeyError:
        raise HTTPException(404, f"No existe la serie «{nombre}». Opciones: {', '.join(exportacion.CONSULTAS)}")
    return Response(exportacion.a_csv(cab, filas), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre}.csv"'})


@router.get("/tablero")
def tablero(escenario: str = "E0 Base", db: Session = Depends(get_db), u=Depends(require(*TODOS))):
    """Indicadores reales del CRUD frente a los proyectados por la simulación para el escenario elegido."""
    proy = proyecciones.cargar()
    if proy and escenario not in proy:
        raise HTTPException(404, f"No hay proyecciones para «{escenario}». Disponibles: {', '.join(proy)}")
    sim = proy.get(escenario, {})
    real = {per: {"matriculados": mat, "desercion_periodo": negocio.tasa(des, mat), "graduados": gra}
            for per, mat, des, gra in _periodos_cerrados(db)}
    periodos = sorted(set(real) | set(sim))
    serie = [{"periodo": p, "real": real.get(p), "simulado": sim.get(p)} for p in periodos]
    tol = parametro(db, "tolerancia_modelo")
    tarjetas = []
    if real:
        ult = max(real)
        for clave, nombre in (("desercion_periodo", "Deserción por periodo"), ("matriculados", "Matriculados"), ("graduados", "Graduados")):
            r = real[ult][clave]
            s = sim.get(ult, {}).get(clave)
            tarjetas.append({"indicador": nombre, "clave": clave, "periodo": ult, "real": r, "simulado": s, **negocio.comparar(r, s, tol)})
    actual = periodo_en_curso(db)
    cap = negocio.estado_capacidad(casos_periodo(db, actual.id) if actual else 0, parametro(db, "capacidad_bienestar"))
    return {"escenario": escenario, "escenarios": list(proy), "periodo_en_curso": actual.codigo if actual else None,
            "capacidad": cap.__dict__, "tarjetas": tarjetas, "serie": serie, "tolerancia": tol}


@router.get("/cohortes-mapa")
def mapa_cohortes(semestres: int = Query(10, ge=2, le=14), db: Session = Depends(get_db), u=Depends(require(*TODOS))):
    """Mapa de calor de permanencia: para cada cohorte, porcentaje de ingresantes matriculados k semestres después del ingreso.

    El semestre 1 es el periodo de ingreso. Las celdas futuras (periodos que aún no existen) van en null.
    """
    periodos = [c for (c,) in db.execute(text("SELECT codigo FROM periodo_academico ORDER BY codigo"))]
    pos = {c: i for i, c in enumerate(periodos)}
    ingresan = dict(db.execute(text("""
        SELECT p.codigo, COUNT(e.id) FROM estudiante e JOIN cohorte co ON co.id = e.cohorte_id
        JOIN periodo_academico p ON p.id = co.periodo_ingreso_id WHERE e.eliminado_en IS NULL GROUP BY p.codigo""")).all())
    presentes: dict[tuple[str, int], int] = {}
    for coh, per, n in db.execute(text("""
        SELECT pi.codigo, pm.codigo, COUNT(DISTINCT m.estudiante_id)
        FROM matricula m JOIN estudiante e ON e.id = m.estudiante_id JOIN cohorte co ON co.id = e.cohorte_id
        JOIN periodo_academico pi ON pi.id = co.periodo_ingreso_id JOIN periodo_academico pm ON pm.id = m.periodo_id
        WHERE m.eliminado_en IS NULL AND e.eliminado_en IS NULL GROUP BY pi.codigo, pm.codigo""")):
        k = pos[per] - pos[coh] + 1
        if 1 <= k <= semestres:
            presentes[(coh, k)] = presentes.get((coh, k), 0) + n
    filas = []
    for coh in sorted(ingresan):
        celdas = []
        for k in range(1, semestres + 1):
            existe = pos[coh] + k - 1 < len(periodos)
            celdas.append(round(100 * presentes.get((coh, k), 0) / ingresan[coh], 1) if existe and ingresan[coh] else None)
        filas.append({"cohorte": coh, "ingresan": ingresan[coh], "permanencia": celdas})
    return {"semestres": semestres, "filas": filas}


@router.post("/proyecciones", status_code=201)
async def cargar_proyecciones(archivo: UploadFile = File(...), db: Session = Depends(get_db), u=Depends(require(A))):
    """Reemplaza las proyecciones del tablero con un CSV generado por el modelo (solo administrador)."""
    contenido = (await archivo.read()).decode("utf-8-sig", errors="replace")
    try:
        datos = proyecciones.guardar(contenido)
    except ValueError as e:
        raise HTTPException(422, str(e))
    audit(db, u, "proyecciones", 0, "ACTUALIZAR", {"archivo": archivo.filename, "escenarios": list(datos)})
    db.commit()
    return {"escenarios": list(datos), "periodos": max(len(v) for v in datos.values())}


@router.get("/bienestar/cola")
def cola(periodo_id: int | None = None, db: Session = Depends(get_db), u=Depends(require(*TODOS))):
    """Casos sin atender del periodo, ordenados por la regla de prioridad, con el apoyo sugerido por etapa."""
    per = db.get(PeriodoAcademico, periodo_id) if periodo_id else periodo_en_curso(db)
    if not per:
        raise HTTPException(404, "Periodo no encontrado")
    filas = db.execute(select(Alerta, Matricula).join(Matricula, Matricula.id == Alerta.matricula_id).where(
        Matricula.periodo_id == per.id, Alerta.atendida.is_(False), Alerta.eliminado_en.is_(None))).all()
    casos = []
    for a, m in filas:
        pal = negocio.palanca_sugerida(m.nivel_semestre, tipos_factor(db, m.estudiante_id))
        tipo = tipo_apoyo_para(db, pal)
        casos.append({"alerta_id": a.id, "estudiante_id": m.estudiante_id, "nivel_semestre": m.nivel_semestre,
                      "etapa": negocio.etapa(m.nivel_semestre), "nivel": a.nivel, "motivo": a.motivo,
                      "materias_basicas_perdidas": m.materias_basicas_perdidas, "promedio": m.promedio,
                      "prioridad": negocio.prioridad(a.nivel, m.nivel_semestre, m.materias_basicas_perdidas),
                      "palanca_sugerida": pal, "tipo_apoyo_sugerido_id": tipo.id if tipo else None,
                      "apoyo_sugerido": tipo.nombre if tipo else None, "creado_en": a.creado_en})
    casos.sort(key=lambda c: (-c["prioridad"], c["creado_en"] or datetime.min, c["alerta_id"]))
    cap = negocio.estado_capacidad(len(casos), parametro(db, "capacidad_bienestar"))
    return {"periodo": per.codigo, "capacidad": cap.__dict__, "casos": casos}


@router.post("/bienestar/cola/{alerta_id}/atender")
def atender(alerta_id: int, tipo_apoyo_id: int | None = None, db: Session = Depends(get_db), u=Depends(require(A, O))):
    """Atiende un caso: asigna el apoyo (el sugerido si no se indica otro) y marca la alerta como atendida."""
    a = db.get(Alerta, alerta_id)
    if not a or a.eliminado_en:
        raise HTTPException(404, f"La alerta {alerta_id} no existe")
    if a.atendida:
        raise HTTPException(409, "La alerta ya fue atendida")
    m = db.get(Matricula, a.matricula_id)
    if tipo_apoyo_id is None:
        tipo = tipo_apoyo_para(db, negocio.palanca_sugerida(m.nivel_semestre, tipos_factor(db, m.estudiante_id)))
        if not tipo:
            raise HTTPException(409, "No hay un tipo de apoyo configurado para la palanca sugerida")
        tipo_apoyo_id = tipo.id
    elif not db.get(TipoApoyo, tipo_apoyo_id):
        raise HTTPException(422, f"El tipo de apoyo {tipo_apoyo_id} no existe")
    existente = db.scalar(select(ApoyoEstudiante).where(ApoyoEstudiante.estudiante_id == m.estudiante_id,
                          ApoyoEstudiante.tipo_apoyo_id == tipo_apoyo_id, ApoyoEstudiante.periodo_id == m.periodo_id))
    if existente and existente.eliminado_en is None:
        apoyo = existente
    else:
        apoyo = ApoyoEstudiante(estudiante_id=m.estudiante_id, tipo_apoyo_id=tipo_apoyo_id, periodo_id=m.periodo_id, estado="asignado")
        db.add(apoyo)
        db.flush()
        audit(db, u, "apoyos", apoyo.id, "CREAR", {"origen": "cola de Bienestar", "alerta_id": alerta_id})
    a.atendida = True
    audit(db, u, "alertas", a.id, "ACTUALIZAR", {"atendida": True, "apoyo_id": apoyo.id})
    db.commit()
    return {"alerta": ser(a), "apoyo": ser(apoyo)}


@router.get("/parametros")
def ver_parametros(db: Session = Depends(get_db), u=Depends(require(*TODOS))):
    """Parámetros de operación que vienen de la simulación."""
    guardados = {p.clave: p for p in db.scalars(select(Parametro))}
    return [{"clave": k, "valor": guardados[k].valor if k in guardados else v, "descripcion": d} for k, (v, d) in PARAMETROS_DEFECTO.items()]


@router.put("/parametros/{clave}")
def cambiar_parametro(clave: str, valor: float = Query(..., ge=0, le=1000), db: Session = Depends(get_db), u=Depends(require(A))):
    """Cambia un parámetro (por ejemplo, la capacidad cuando Bienestar amplíe sus cupos). Solo administrador."""
    if clave not in PARAMETROS_DEFECTO:
        raise HTTPException(404, f"No existe el parámetro «{clave}»")
    p = db.get(Parametro, clave) or Parametro(clave=clave, descripcion=PARAMETROS_DEFECTO[clave][1])
    anterior = p.valor
    p.valor = valor
    db.add(p)
    audit(db, u, "parametros", 0, "ACTUALIZAR", {"clave": clave, "antes": anterior, "despues": valor})
    db.commit()
    return {"clave": clave, "valor": valor, "descripcion": p.descripcion}
