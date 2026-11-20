"""Pruebas unitarias de la lógica de negocio (app/negocio.py, app/proyecciones.py y app/security.py)."""
import math
import pytest
from app import negocio, proyecciones, security


@pytest.mark.parametrize("nivel,esperada", [(1, "temprana"), (2, "temprana"), (3, "media"), (5, "media"), (6, "tardia"), (14, "tardia")])
def test_etapa(nivel, esperada):
    assert negocio.etapa(nivel) == esperada


def test_etapa_fuera_de_rango():
    with pytest.raises(ValueError):
        negocio.etapa(0)


def test_palanca_sin_factores_usa_el_mayor_peso_de_la_etapa():
    assert negocio.palanca_sugerida(1) == "adaptacion"      # temprana: adaptación 0,4
    assert negocio.palanca_sugerida(4) == "academico"       # media: académica 0,5
    assert negocio.palanca_sugerida(8) == "academico"       # tardía: empate 0,4 se resuelve por académica


def test_palanca_respeta_los_factores_del_estudiante():
    assert negocio.palanca_sugerida(1, ["economico"]) == "economico"
    assert negocio.palanca_sugerida(1, ["economico", "academico"]) == "academico"   # empate 0,3: gana académica
    assert negocio.palanca_sugerida(7, ["economico", "adaptacion"]) == "economico"
    assert negocio.palanca_sugerida(3, ["desconocido"]) == "academico"              # tipos no válidos se ignoran


def test_prioridad_ordena_por_nivel_luego_semestre_luego_materias():
    alto_s1 = negocio.prioridad("alto", 1, 0)
    alto_s6 = negocio.prioridad("alto", 6, 0)
    medio_s1 = negocio.prioridad("medio", 1, 3)
    assert alto_s1 > alto_s6 > medio_s1 > negocio.prioridad("bajo", 1, 0)
    assert negocio.prioridad("medio", 2, 2) > negocio.prioridad("medio", 2, 0)
    assert negocio.prioridad("alto", 1, 50) == negocio.prioridad("alto", 1, 5)        # tope de materias


def test_prioridad_nivel_invalido():
    with pytest.raises(ValueError):
        negocio.prioridad("critico", 1)


@pytest.mark.parametrize("casos,capacidad,semaforo", [(10, 32, "verde"), (26, 32, "ambar"), (32, 32, "ambar"), (40, 32, "rojo"), (5, 0, "rojo"), (0, 0, "rojo")])
def test_semaforo_de_capacidad(casos, capacidad, semaforo):
    assert negocio.estado_capacidad(casos, capacidad).semaforo == semaforo


def test_cobertura_esperada():
    e = negocio.estado_capacidad(40, 32)
    assert e.cobertura_esperada == 0.8 and e.ocupacion == 1.25 and "superan" in e.mensaje
    assert negocio.estado_capacidad(0, 32).cobertura_esperada == 1.0


def test_tasa_y_retencion():
    assert negocio.tasa(5, 0) == 0 and negocio.tasa(1, 4) == 0.25
    tasas = [b * 0.715 for b in (.204, .117, .087, .076, .074, .060, .054, .033, .023, .024)]
    assert math.isclose(1 - negocio.retencion_cohorte(tasas), 0.4291, abs_tol=1e-3)   # mismo valor que el modelo determinista
    with pytest.raises(ValueError):
        negocio.retencion_cohorte([1.2])


def test_comparar_real_y_simulado():
    assert negocio.comparar(0.06, 0.05)["dentro_margen"] is False                     # 20 % de desviación
    assert negocio.comparar(0.055, 0.05)["dentro_margen"] is True
    assert negocio.comparar(None, 0.05) == {"desviacion": None, "dentro_margen": None}
    assert negocio.comparar(0, 0)["desviacion"] == 0


CSV_OK = "escenario,periodo,matriculados,desercion_periodo,graduados,alertas,cobertura_bienestar\nE0 Base,2015-1,65.8,0.14,0,12,1\n"


def test_parsear_proyecciones_valido():
    d = proyecciones.parsear(CSV_OK)
    assert d["E0 Base"]["2015-1"]["matriculados"] == 65.8


@pytest.mark.parametrize("contenido,mensaje", [
    ("a,b\n1,2\n", "columnas"),
    (CSV_OK.replace("65.8", "abc"), "numérico"),
    (CSV_OK.replace("0.14", "1.4"), "entre 0 y 1"),
    (CSV_OK.replace("2015-1", "2015-3"), "formato"),
    (CSV_OK.split("\n")[0] + "\n", "no tiene filas"),
])
def test_parsear_proyecciones_invalido(contenido, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        proyecciones.parsear(contenido)


def test_hash_con_sal_y_verificacion():
    h1, h2 = security.hash_pw("Clave-Segura-1"), security.hash_pw("Clave-Segura-1")
    assert h1 != h2                                         # la sal cambia el hash
    assert security.verify_pw("Clave-Segura-1", h1) and not security.verify_pw("otra", h1)
    assert not security.verify_pw("x", "formato-invalido")


def test_bloqueo_por_intentos():
    correo = "fuerza@bruta.co"
    for _ in range(security.MAX_INTENTOS):
        assert not security.bloqueado(correo)
        security.registrar_fallo(correo)
    assert security.bloqueado(correo)
    security.limpiar_fallos(correo)
    assert not security.bloqueado(correo)
