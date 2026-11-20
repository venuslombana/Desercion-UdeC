"""Lógica de negocio del CRUD, separada de la API para poder probarla con pruebas unitarias.

Las reglas de este módulo salen del modelo de simulación (componente B):
- Las etapas y los pesos de cada palanca son los mismos del modelo de Vensim (desercion_udec.mdl).
- La capacidad recomendada de Bienestar (32 casos por semestre) es la del escenario E3, la alternativa elegida.
- El semáforo de capacidad usa la cobertura: en la simulación, por debajo de 100 % de cobertura se pierde
  parte del efecto de las alertas tempranas.
"""
from dataclasses import dataclass

ETAPAS = {"temprana": range(1, 3), "media": range(3, 6), "tardia": range(6, 15)}
# Pesos (económica, académica, adaptación) por etapa: mismos valores del modelo de simulación.
PESOS = {"temprana": {"economico": .3, "academico": .3, "adaptacion": .4},
         "media": {"economico": .3, "academico": .5, "adaptacion": .2},
         "tardia": {"economico": .4, "academico": .4, "adaptacion": .2}}
CAPACIDAD_RECOMENDADA = 32.0      # casos por semestre, escenario E3
UMBRAL_AMBAR = 0.8                # ocupación desde la que se avisa antes de saturar
TOLERANCIA_MODELO = 0.15          # desviación relativa aceptada entre lo real y lo simulado
NIVEL_PESO = {"alto": 3, "medio": 2, "bajo": 1}


def etapa(nivel_semestre: int) -> str:
    """Etapa del recorrido académico a la que pertenece un semestre."""
    for nombre, rango in ETAPAS.items():
        if nivel_semestre in rango:
            return nombre
    raise ValueError(f"Semestre fuera de rango: {nivel_semestre}")


def palanca_sugerida(nivel_semestre: int, tipos_factor: list[str] | None = None) -> str:
    """Palanca de apoyo que se sugiere para un caso.

    Si el estudiante tiene factores de riesgo registrados, se elige la palanca con mayor peso entre los
    tipos de factor presentes. Si no tiene, se elige la palanca de mayor peso en su etapa.
    En caso de empate gana el orden académico > adaptación > económico, porque la palanca académica
    no depende de presupuesto adicional.
    """
    pesos = PESOS[etapa(nivel_semestre)]
    candidatos = [t for t in (tipos_factor or []) if t in pesos] or list(pesos)
    orden = {"academico": 0, "adaptacion": 1, "economico": 2}
    return sorted(set(candidatos), key=lambda t: (-pesos[t], orden[t]))[0]


def prioridad(nivel_alerta: str, nivel_semestre: int, materias_perdidas: int = 0) -> float:
    """Puntaje de prioridad de un caso en la cola de Bienestar (más alto = se atiende primero).

    Regla pública y explicable: pesa el nivel de la alerta, lo temprano del semestre (donde la tasa de
    deserción es mayor) y las materias básicas perdidas. No usa estrato ni condición laboral, para que la
    regla no discrimine por variables socioeconómicas (ver reflexión ética del informe).
    """
    if nivel_alerta not in NIVEL_PESO:
        raise ValueError(f"Nivel de alerta inválido: {nivel_alerta}")
    urgencia_semestre = max(0, 11 - min(nivel_semestre, 10)) / 10          # 1,0 en primer semestre
    return round(NIVEL_PESO[nivel_alerta] * 10 + urgencia_semestre * 5 + min(materias_perdidas, 5), 2)


@dataclass
class EstadoCapacidad:
    casos: int
    capacidad: float
    ocupacion: float
    cobertura_esperada: float
    semaforo: str
    mensaje: str


def estado_capacidad(casos_pendientes: int, capacidad: float) -> EstadoCapacidad:
    """Semáforo de capacidad de Bienestar para el periodo en curso."""
    if capacidad <= 0:
        return EstadoCapacidad(casos_pendientes, capacidad, float("inf") if casos_pendientes else 0.0, 0.0, "rojo",
                               "Bienestar no tiene capacidad configurada")
    ocup = casos_pendientes / capacidad
    cobertura = min(1.0, capacidad / casos_pendientes) if casos_pendientes else 1.0
    if ocup > 1:
        sem, msg = "rojo", (f"Los casos del periodo ({casos_pendientes}) superan la capacidad de Bienestar ({capacidad:g}). "
                            f"Cobertura esperada: {cobertura:.0%}. La simulación indica que con cobertura menor al 100 % "
                            "se pierde parte del efecto de las alertas tempranas.")
    elif ocup >= UMBRAL_AMBAR:
        sem, msg = "ambar", f"Bienestar está al {ocup:.0%} de su capacidad ({casos_pendientes} de {capacidad:g} casos)."
    else:
        sem, msg = "verde", f"Bienestar está al {ocup:.0%} de su capacidad ({casos_pendientes} de {capacidad:g} casos)."
    return EstadoCapacidad(casos_pendientes, capacidad, round(ocup, 4), round(cobertura, 4), sem, msg)


def tasa(numerador: float, denominador: float) -> float:
    """División segura para indicadores (0 cuando no hay denominador)."""
    return numerador / denominador if denominador else 0.0


def retencion_cohorte(tasas_por_nivel: list[float]) -> float:
    """Fracción de una cohorte que termina el último nivel dadas las tasas de deserción por nivel."""
    r = 1.0
    for t in tasas_por_nivel:
        if not 0 <= t <= 1:
            raise ValueError("Cada tasa debe estar entre 0 y 1")
        r *= 1 - t
    return r


def comparar(real: float | None, simulado: float | None, tolerancia: float = TOLERANCIA_MODELO) -> dict:
    """Compara un indicador real con el proyectado por el modelo.

    Devuelve la desviación relativa y si el modelo sigue dentro del margen. Cuando la desviación supera
    la tolerancia el tablero recomienda recalibrar el modelo con los datos nuevos.
    """
    if real is None or simulado is None:
        return {"desviacion": None, "dentro_margen": None}
    base = abs(simulado) if simulado else abs(real)
    desv = (real - simulado) / base if base else 0.0
    return {"desviacion": round(desv, 4), "dentro_margen": abs(desv) <= tolerancia}
