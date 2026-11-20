"""Exportación de datos históricos para alimentar la simulación (integración CRUD → modelo).

Las mismas consultas las usa el endpoint GET /api/exportacion/... y el script scripts/exportar_datos_crud.py,
así que los CSV que descarga el usuario son idénticos a los que usó el análisis de datos de entrada.
Se excluye el periodo en curso (el último registrado) porque todavía no tiene resultado definitivo.
Las consultas usan SQL estándar con parámetros enlazados: corren igual en SQLite y en PostgreSQL.
"""
import csv
import io
import zipfile
from sqlalchemy import text
from sqlalchemy.orm import Session

CUENTA = "SUM(CASE WHEN {c} THEN 1 ELSE 0 END)"

CONSULTAS = {
    "ingresos_por_cohorte": (["periodo_ingreso", "estudiantes"], """
        SELECT p.codigo, COUNT(*) FROM estudiante e JOIN cohorte co ON co.id = e.cohorte_id
        JOIN periodo_academico p ON p.id = co.periodo_ingreso_id WHERE e.eliminado_en IS NULL
        GROUP BY p.codigo ORDER BY p.codigo"""),
    "matriculas_por_nivel": (["nivel_semestre", "matriculas", "desertan", "se_graduan"], f"""
        SELECT nivel_semestre, COUNT(*), {CUENTA.format(c="resultado = 'DESERTA'")}, {CUENTA.format(c="resultado = 'GRADUA'")}
        FROM matricula WHERE periodo_id < :ultimo AND eliminado_en IS NULL GROUP BY nivel_semestre ORDER BY nivel_semestre"""),
    "desercion_sem1_por_cohorte": (["periodo", "matriculados_sem1", "desertan"], f"""
        SELECT p.codigo, COUNT(*), {CUENTA.format(c="m.resultado = 'DESERTA'")} FROM matricula m
        JOIN periodo_academico p ON p.id = m.periodo_id
        WHERE m.nivel_semestre = 1 AND m.periodo_id < :ultimo AND m.eliminado_en IS NULL GROUP BY p.codigo ORDER BY p.codigo"""),
    "alertas_y_apoyos_por_periodo": (["periodo", "matriculas_sem1_2", "alertas", "apoyos_asignados"], """
        SELECT p.codigo,
          (SELECT COUNT(*) FROM matricula m WHERE m.periodo_id = p.id AND m.nivel_semestre <= 2),
          (SELECT COUNT(*) FROM alerta a JOIN matricula m ON m.id = a.matricula_id WHERE m.periodo_id = p.id),
          (SELECT COUNT(*) FROM apoyo_estudiante ap WHERE ap.periodo_id = p.id)
        FROM periodo_academico p WHERE p.id < :ultimo ORDER BY p.codigo"""),
    "matriculas_por_periodo": (["periodo", "matriculas", "desertan", "se_graduan"], f"""
        SELECT p.codigo, COUNT(*), {CUENTA.format(c="m.resultado = 'DESERTA'")}, {CUENTA.format(c="m.resultado = 'GRADUA'")}
        FROM matricula m JOIN periodo_academico p ON p.id = m.periodo_id
        WHERE m.periodo_id < :ultimo AND m.eliminado_en IS NULL GROUP BY p.codigo ORDER BY p.codigo"""),
}


def ultimo_periodo_id(db: Session) -> int:
    """Id del periodo en curso (el último registrado)."""
    return db.execute(text("SELECT MAX(id) FROM periodo_academico")).scalar() or 0


def datos(db: Session, nombre: str) -> tuple[list[str], list[tuple]]:
    """Columnas y filas de una de las series históricas."""
    if nombre not in CONSULTAS:
        raise KeyError(nombre)
    cab, sql = CONSULTAS[nombre]
    filas = [tuple(int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v for v in f)
             for f in db.execute(text(sql), {"ultimo": ultimo_periodo_id(db)})]
    return cab, filas


def a_csv(cab: list[str], filas: list[tuple]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(cab)
    w.writerows(filas)
    return buf.getvalue()


def zip_todo(db: Session) -> bytes:
    """Los cinco CSV en un solo archivo ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre in CONSULTAS:
            z.writestr(f"{nombre}.csv", a_csv(*datos(db, nombre)))
    return buf.getvalue()
