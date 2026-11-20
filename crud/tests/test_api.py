"""Pruebas de integración de la API: autenticación, roles, CRUD, validación, auditoría, reportes, exportación,
tablero, cola de Bienestar y seguridad. Usan la base sintética que crea conftest.py."""
import csv, io, os, zipfile
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
DATOS_SIM = os.path.join(os.path.dirname(__file__), "..", "..", "simulacion", "datos")


def tok(email, pw="Cambiar-123"):
    r = c.post("/api/auth/login", data={"username": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


ADM, OPE, CON = (tok(f"{x}@demo.edu.co") for x in ("admin", "operador", "consulta"))
NUEVO = {"codigo_anonimo": "TESTEST0001", "cohorte_id": 1, "estrato": 3, "puntaje_saber11": 250, "trabaja": False}


# ---------- autenticación y roles
def test_login_incorrecto():
    assert c.post("/api/auth/login", data={"username": "admin@demo.edu.co", "password": "mala"}).status_code == 401

def test_bloqueo_tras_intentos_fallidos():
    for _ in range(5):
        c.post("/api/auth/login", data={"username": "consulta@demo.edu.co", "password": "mala"})
    r = c.post("/api/auth/login", data={"username": "consulta@demo.edu.co", "password": "Cambiar-123"})
    assert r.status_code == 429
    from app import security
    security.limpiar_fallos("consulta@demo.edu.co")

def test_sin_token_y_token_invalido():
    assert c.get("/api/estudiantes").status_code == 401
    assert c.get("/api/estudiantes", headers={"Authorization": "Bearer xxx"}).status_code == 401

def test_me():
    assert c.get("/api/auth/me", headers=CON).json()["rol"] == "consulta"

def test_consulta_no_puede_crear():
    assert c.post("/api/estudiantes", json=NUEVO, headers=CON).status_code == 403

def test_usuario_inactivo_no_entra():
    r = c.post("/api/usuarios", json={"nombre": "Temporal", "email": "temp@demo.edu.co", "password": "Temporal-123", "rol_id": 3}, headers=ADM)
    uid = r.json()["id"]
    h = tok("temp@demo.edu.co", "Temporal-123")
    c.put(f"/api/usuarios/{uid}", json={"activo": False}, headers=ADM)
    assert c.get("/api/auth/me", headers=h).status_code == 401
    assert c.post("/api/auth/login", data={"username": "temp@demo.edu.co", "password": "Temporal-123"}).status_code == 401


# ---------- listados
def test_paginacion_y_total():
    j = c.get("/api/estudiantes?page=2&size=10", headers=CON).json()
    assert len(j["items"]) == 10 and j["page"] == 2 and j["total"] > 1000

def test_busqueda_filtro_orden():
    j = c.get("/api/estudiantes?estrato=1&sort=puntaje_saber11&order=desc&size=5", headers=CON).json()
    assert all(x["estrato"] == 1 for x in j["items"])
    p = [x["puntaje_saber11"] for x in j["items"]]
    assert p == sorted(p, reverse=True)
    assert c.get("/api/factores?q=básicas", headers=CON).json()["total"] == 1

def test_orden_y_filtro_invalidos():
    assert c.get("/api/estudiantes?sort=password_hash", headers=CON).status_code == 422
    assert c.get("/api/estudiantes?estrato=abc", headers=CON).status_code == 422

def test_inyeccion_sql_no_tiene_efecto():
    r = c.get("/api/estudiantes?q=' OR 1=1 --", headers=CON)
    assert r.status_code == 200 and r.json()["total"] == 0
    assert c.get("/api/estudiantes?size=1", headers=CON).json()["total"] > 1000


# ---------- CRUD, validación, eliminación lógica y auditoría
def test_validacion_servidor():
    r = c.post("/api/estudiantes", json={**NUEVO, "estrato": 9}, headers=OPE)
    assert r.status_code == 422

def test_crud_estudiante_con_auditoria():
    r = c.post("/api/estudiantes", json=NUEVO, headers=OPE); assert r.status_code == 201; i = r.json()["id"]
    assert c.post("/api/estudiantes", json=NUEVO, headers=OPE).status_code == 409
    assert c.put(f"/api/estudiantes/{i}", json={"estrato": 4}, headers=OPE).json()["estrato"] == 4
    assert c.put(f"/api/estudiantes/{i}", json={"estrato": 8}, headers=OPE).status_code == 422
    assert c.put(f"/api/estudiantes/{i}", json={"inventado": 1}, headers=OPE).status_code == 422
    assert c.delete(f"/api/estudiantes/{i}", headers=OPE).status_code == 403
    assert c.delete(f"/api/estudiantes/{i}", headers=ADM).status_code == 204
    assert c.get(f"/api/estudiantes/{i}", headers=CON).status_code == 404
    acc = {x["accion"] for x in c.get(f"/api/auditoria?entidad=estudiantes&registro_id={i}&size=50", headers=ADM).json()["items"]}
    assert {"CREAR", "ACTUALIZAR", "ELIMINAR"} <= acc

def test_auditoria_solo_admin():
    assert c.get("/api/auditoria", headers=OPE).status_code == 403

def test_usuario_password_no_se_expone():
    r = c.post("/api/usuarios", json={"nombre": "Nuevo Usuario", "email": "n@demo.edu.co", "password": "Segura-1234", "rol_id": 3}, headers=ADM)
    assert r.status_code == 201 and "password_hash" not in r.json() and "password" not in r.json()
    assert c.post("/api/auth/login", data={"username": "n@demo.edu.co", "password": "Segura-1234"}).status_code == 200
    det = c.get(f"/api/auditoria?entidad=usuarios&registro_id={r.json()['id']}", headers=ADM).json()["items"][0]["detalle"]
    assert "Segura-1234" not in det

def test_usuario_requiere_password():
    r = c.post("/api/usuarios", json={"nombre": "Sin Clave", "email": "s@demo.edu.co", "rol_id": 3}, headers=ADM)
    assert r.status_code == 422

def test_matricula_validacion():
    r = c.post("/api/matriculas", json={"estudiante_id": 1, "periodo_id": 1, "nivel_semestre": 1, "promedio": 7, "creditos_inscritos": 15, "resultado": "CONTINUA"}, headers=OPE)
    assert r.status_code == 422

def test_relacion_inexistente_da_409():
    r = c.post("/api/apoyos", json={"estudiante_id": 999999, "tipo_apoyo_id": 1, "periodo_id": 22}, headers=OPE)
    assert r.status_code == 409

def test_roles_catalogo():
    assert [r["nombre"] for r in c.get("/api/roles", headers=ADM).json()] == ["administrador", "operador", "consulta"]
    assert c.get("/api/roles", headers=OPE).status_code == 403


# ---------- relación muchos-a-muchos con llave compuesta
def test_crud_estudiante_factor():
    body = {"estudiante_id": 5, "factor_id": 2, "periodo_id": 20, "intensidad": 2}
    assert c.post("/api/estudiante-factores", json=body, headers=OPE).status_code == 201
    assert c.post("/api/estudiante-factores", json=body, headers=OPE).status_code == 409
    assert c.post("/api/estudiante-factores", json={**body, "factor_id": 999}, headers=OPE).status_code == 409
    assert c.put("/api/estudiante-factores/5/2/20", json={"intensidad": 3}, headers=OPE).json()["intensidad"] == 3
    j = c.get("/api/estudiante-factores?estudiante_id=5&sort=intensidad&order=desc", headers=CON).json()
    assert j["total"] >= 1 and j["items"][0]["intensidad"] == 3
    assert c.delete("/api/estudiante-factores/5/2/20", headers=OPE).status_code == 403
    assert c.delete("/api/estudiante-factores/5/2/20", headers=ADM).status_code == 204
    assert c.put("/api/estudiante-factores/5/2/20", json={"intensidad": 1}, headers=OPE).status_code == 404


# ---------- reportes y exportación
def test_reportes_con_indicadores():
    lista = c.get("/api/reportes", headers=CON).json()
    assert len(lista) >= 3
    for r in lista:
        rep = c.get(f"/api/reportes/{r['id']}", headers=CON).json()
        assert len(rep["indicadores"]) >= 3 and rep["filas"]
    assert c.get("/api/reportes/inventado", headers=CON).status_code == 404

def test_reporte_csv_y_pdf():
    r = c.get("/api/reportes/desercion-periodo?formato=csv", headers=CON)
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    filas = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
    assert filas[0][0] == "Periodo" and len(filas) > 15
    p = c.get("/api/reportes/bienestar?formato=pdf", headers=CON)
    assert p.content[:4] == b"%PDF"

def test_deserción_de_cohorte_del_crud_coincide_con_el_modelo():
    ind = c.get("/api/reportes/desercion-nivel", headers=CON).json()["indicadores"][0]
    assert abs(ind["valor"] - 42.9) < 0.5          # el modelo determinista da 42,91 %

def test_exportacion_identica_a_los_datos_de_la_simulacion():
    z = zipfile.ZipFile(io.BytesIO(c.get("/api/exportacion/historicos", headers=CON).content))
    assert len(z.namelist()) == 5
    for n in z.namelist():
        with open(os.path.join(DATOS_SIM, n), "rb") as f:
            assert z.read(n) == f.read(), n
    assert c.get("/api/exportacion/historicos/matriculas_por_nivel", headers=CON).text.startswith("nivel_semestre")
    assert c.get("/api/exportacion/historicos/otra", headers=CON).status_code == 404


# ---------- integración con la simulación
def test_tablero_real_vs_simulado():
    j = c.get("/api/tablero", params={"escenario": "E0 Base"}, headers=CON).json()
    assert j["periodo_en_curso"] == "2025-2" and "E3 Permanencia integral" in j["escenarios"]
    assert all(t["dentro_margen"] for t in j["tarjetas"])
    assert any(p["real"] and p["simulado"] for p in j["serie"])
    assert c.get("/api/tablero", params={"escenario": "No existe"}, headers=CON).status_code == 404

def test_mapa_de_cohortes():
    j = c.get("/api/cohortes-mapa", headers=CON).json()
    assert j["semestres"] == 10 and j["filas"]
    primera = j["filas"][0]
    assert primera["permanencia"][0] == 100.0                      # en el semestre de ingreso todos están matriculados
    vals = [v for v in primera["permanencia"] if v is not None]
    assert all(a >= b for a, b in zip(vals, vals[1:]))              # la permanencia no sube con el tiempo
    assert j["filas"][-1]["permanencia"][-1] is None                 # la cohorte más reciente no tiene futuro todavía
    assert c.get("/api/cohortes-mapa", params={"semestres": 99}, headers=CON).status_code == 422

def test_carga_de_proyecciones_validada():
    r = c.post("/api/proyecciones", files={"archivo": ("p.csv", b"a,b\n1,2\n", "text/csv")}, headers=ADM)
    assert r.status_code == 422
    assert c.post("/api/proyecciones", files={"archivo": ("p.csv", b"x", "text/csv")}, headers=OPE).status_code == 403
    with open(os.environ["PROYECCIONES_CSV"], "rb") as f:
        r = c.post("/api/proyecciones", files={"archivo": ("p.csv", f.read(), "text/csv")}, headers=ADM)
    assert r.status_code == 201 and r.json()["periodos"] == 32

def test_cola_priorizada_y_atencion():
    cola = c.get("/api/bienestar/cola", headers=OPE).json()
    pr = [x["prioridad"] for x in cola["casos"]]
    assert pr == sorted(pr, reverse=True) and cola["capacidad"]["semaforo"] == "verde"
    caso = cola["casos"][0]
    r = c.post(f"/api/bienestar/cola/{caso['alerta_id']}/atender", headers=OPE)
    assert r.status_code == 200 and r.json()["alerta"]["atendida"] and r.json()["apoyo"]["tipo_apoyo_id"] == caso["tipo_apoyo_sugerido_id"]
    assert c.post(f"/api/bienestar/cola/{caso['alerta_id']}/atender", headers=OPE).status_code == 409
    assert c.post(f"/api/bienestar/cola/{caso['alerta_id']}/atender", headers=CON).status_code == 403
    otro = cola["casos"][1]["alerta_id"]
    assert c.post(f"/api/bienestar/cola/{otro}/atender?tipo_apoyo_id=999", headers=OPE).status_code == 422
    assert c.post(f"/api/bienestar/cola/{otro}/atender?tipo_apoyo_id=2", headers=OPE).json()["apoyo"]["tipo_apoyo_id"] == 2
    assert c.post("/api/bienestar/cola/999999/atender", headers=OPE).status_code == 404
    assert len(c.get("/api/bienestar/cola", headers=OPE).json()["casos"]) == len(cola["casos"]) - 2
    assert c.get("/api/bienestar/cola?periodo_id=9999", headers=OPE).status_code == 404

def test_alerta_avisa_capacidad_y_sugiere_apoyo():
    assert c.put("/api/parametros/capacidad_bienestar?valor=10", headers=OPE).status_code == 403
    assert c.put("/api/parametros/capacidad_bienestar?valor=10", headers=ADM).json()["valor"] == 10
    mat = c.get("/api/matriculas?periodo_id=22&nivel_semestre=4&size=1", headers=OPE).json()["items"][0]
    r = c.post("/api/alertas", json={"matricula_id": mat["id"], "nivel": "medio", "motivo": "Riesgo académico en semestre 4"}, headers=OPE)
    assert r.status_code == 201
    j = r.json()
    assert j["capacidad"]["semaforo"] == "rojo" and "X-Aviso" in r.headers
    assert j["palanca_sugerida"] in ("academico", "economico", "adaptacion") and j["apoyo_sugerido"]
    params = {p["clave"]: p["valor"] for p in c.get("/api/parametros", headers=CON).json()}
    assert params["capacidad_bienestar"] == 10
    assert c.put("/api/parametros/no_existe?valor=1", headers=ADM).status_code == 404
    c.put("/api/parametros/capacidad_bienestar?valor=32", headers=ADM)


# ---------- seguridad y cliente web
def test_cabeceras_de_seguridad_y_cliente_web():
    r = c.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY" and r.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" not in c.get("/docs").headers
    assert c.get("/api/health").json()["estado"] == "ok"
