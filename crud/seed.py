"""Datos de prueba SINTÉTICOS para desarrollo (no son datos reales de UdeC).
Sirven para probar el CRUD. Para la simulación y la validación deben sustituirse por datos reales anonimizados
(SPADIES / Planeación).
Uso:  python seed.py [ruta.db | URL de SQLAlchemy]     (sin argumento usa DATABASE_URL o db/desercion_dev.db)
La semilla aleatoria es fija (7): la base generada es siempre la misma y de ella salen exactamente los CSV
de simulacion/datos, lo que hace reproducible toda la cadena CRUD → simulación."""
import sys, random, hashlib, os, math
from datetime import datetime
from sqlalchemy import create_engine, select, func, update
from sqlalchemy.orm import Session
sys.path.insert(0, os.path.dirname(__file__))
from app.models import *

BASE = [.204, .117, .087, .076, .074, .060, .054, .033, .023, .024]  # tasas por periodo del modelo (perfil sectorial)

def hash_pw(pw, salt=None):
    salt = salt or os.urandom(16)
    return "pbkdf2$" + salt.hex() + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000).hex()

def periodos(a0=2015, a1=2025):
    return [(f"{a}-{s}", a, s) for a in range(a0, a1 + 1) for s in (1, 2)]

DEFECTO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "desercion_dev.db"))

def motor(destino):
    """Acepta una ruta de archivo SQLite o una URL de SQLAlchemy (sqlite:///..., postgresql+psycopg://...)."""
    if "://" in destino:
        from app.db import normalizar_url
        eng = create_engine(normalizar_url(destino))
        Base.metadata.drop_all(eng)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        if os.path.exists(destino): os.remove(destino)
        eng = create_engine(f"sqlite:///{destino}")
    Base.metadata.create_all(eng)
    return eng

def main(path=None, seed=7):
    random.seed(seed)
    path = path or os.getenv("DATABASE_URL") or DEFECTO
    eng = motor(path)
    with Session(eng) as s:
        roles = {n: Rol(nombre=n) for n in ("administrador", "operador", "consulta")}; s.add_all(roles.values())
        for n, e, r in (("Administrador Demo", "admin@demo.edu.co", "administrador"), ("Operador Bienestar", "operador@demo.edu.co", "operador"), ("Consulta Facultad", "consulta@demo.edu.co", "consulta")):
            s.add(Usuario(nombre=n, email=e, password_hash=hash_pw("Cambiar-123"), rol=roles[r]))
        prog = Programa(nombre="Ingeniería de Sistemas y Computación", sede="Fusagasugá", semestres_plan=9); s.add(prog)
        pers = [PeriodoAcademico(codigo=c, anio=a, semestre=sm) for c, a, sm in periodos()]; s.add_all(pers); s.flush()
        factores = [FactorRiesgo(tipo=t, nombre=n) for t, n in (("economico", "Dificultad de sostenimiento"), ("economico", "Necesidad de trabajar"),
            ("academico", "Pérdida de ciencias básicas"), ("academico", "Bajo rendimiento acumulado"), ("adaptacion", "Dificultad de adaptación"), ("adaptacion", "Orientación vocacional dudosa"))]
        tipos = [TipoApoyo(nombre=n, palanca=p, cupos_por_periodo=c) for n, p, c in (("Beca / exoneración", "economico", 40), ("Monitoría de ciencias básicas", "academico", 60), ("Acompañamiento psicosocial", "adaptacion", 45))]
        s.add_all(factores + tipos); s.flush()
        last = len(pers) - 1; n_est = 0
        for ci in range(0, last):  # cohortes 2015-1 .. 2025-1 (la última no tiene seguimiento)
            coh = Cohorte(programa_id=prog.id, periodo_ingreso_id=pers[ci].id); s.add(coh); s.flush()
            for _ in range(random.randint(55, 75)):
                n_est += 1
                est = Estudiante(codigo_anonimo=hashlib.sha256(f"est{n_est}".encode()).hexdigest()[:16], cohorte_id=coh.id,
                    estrato=random.choices([1, 2, 3, 4, 5], [.22, .38, .28, .09, .03])[0], puntaje_saber11=int(random.gauss(255, 40)), trabaja=random.random() < .28)
                est.puntaje_saber11 = max(100, min(450, est.puntaje_saber11)); s.add(est); s.flush()
                riesgo = 0.9 * (255 - est.puntaje_saber11) / 40 * 0.5 + (0.5 if est.trabaja else 0) + (0.3 if est.estrato <= 2 else 0)
                mult = math.exp(0.5 * riesgo) / 1.25
                nivel, pi = 1, ci; rezago = 0
                while pi <= last:
                    prom = max(1.0, min(5.0, random.gauss(3.7 - 0.45 * riesgo, 0.5)))
                    perd = max(0, int(random.gauss(0.4 + 0.7 * max(riesgo, 0), 0.8))) if nivel <= 5 else 0
                    tasa = BASE[min(nivel, 10) - 1] * 0.8 * mult if rezago == 0 else 0.03
                    res = "CONTINUA"
                    if pi == last: res = "CONTINUA"
                    elif nivel >= 10 and rezago == 0 and random.random() < 0.65: res = "GRADUA"
                    elif nivel >= 10 and rezago > 0 and random.random() < 0.12: res = "GRADUA"
                    elif random.random() < tasa: res = "DESERTA"
                    m = Matricula(estudiante_id=est.id, periodo_id=pers[pi].id, nivel_semestre=min(nivel, 14), promedio=round(prom, 2),
                                  creditos_inscritos=random.randint(12, 18), materias_basicas_perdidas=perd, resultado=res); s.add(m); s.flush()
                    if nivel <= 2 and (prom < 3.0 or perd >= 2): s.add(Alerta(matricula_id=m.id, nivel="alto" if perd >= 2 else "medio", motivo="Bajo rendimiento / ciencias básicas perdidas"))
                    if nivel <= 3 and random.random() < 0.08 + 0.1 * max(riesgo, 0):
                        s.add(ApoyoEstudiante(estudiante_id=est.id, tipo_apoyo_id=random.choice(tipos).id, periodo_id=pers[pi].id, estado="finalizado"))
                    if nivel == 1 and random.random() < 0.5 * min(1, max(0.1, 0.4 + riesgo)):
                        s.add(EstudianteFactor(estudiante_id=est.id, factor_id=random.choice(factores).id, periodo_id=pers[pi].id, intensidad=random.randint(1, 3)))
                    if res != "CONTINUA": break
                    if nivel >= 10: rezago += 1
                    nivel += 1; pi += 1
        # Los casos de periodos cerrados ya pasaron por Bienestar; solo quedan en cola los del periodo en curso.
        cerradas = select(Matricula.id).where(Matricula.periodo_id < pers[last].id)
        s.execute(update(Alerta).where(Alerta.matricula_id.in_(cerradas)).values(atendida=True))
        s.add_all([Parametro(clave="capacidad_bienestar", valor=32.0, descripcion="Casos que Bienestar atiende por semestre (escenario E3 recomendado)"),
                   Parametro(clave="meta_desercion_cohorte", valor=35.0, descripcion="Meta de deserción de cohorte a 10 semestres (%)"),
                   Parametro(clave="tolerancia_modelo", valor=0.15, descripcion="Desviación relativa aceptada entre lo real y lo simulado")])
        s.add(Auditoria(usuario_id=1, entidad="seed", registro_id=0, accion="CREAR", detalle="Carga de datos sintéticos de desarrollo")); s.commit()
        for t in (Estudiante, Matricula, Alerta, ApoyoEstudiante, EstudianteFactor):
            print(t.__tablename__, s.scalar(select(func.count()).select_from(t)))
    return path

if __name__ == "__main__":
    print("Base creada en", main(*sys.argv[1:2]))
