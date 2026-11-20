"""Lectura y validación del CSV de proyecciones que produce el modelo de simulación.

El archivo lo genera simulacion/scripts/exportar_proyecciones.py corriendo el modelo de Vensim (vía PySD)
para cada escenario. El tablero lo usa para comparar los indicadores reales con los proyectados.
"""
import csv
import io
import os

COLUMNAS = ["escenario", "periodo", "matriculados", "desercion_periodo", "graduados", "alertas", "cobertura_bienestar"]
RUTA_DEFECTO = os.path.join(os.path.dirname(__file__), "..", "data", "proyecciones.csv")


def ruta() -> str:
    return os.getenv("PROYECCIONES_CSV", RUTA_DEFECTO)


def parsear(contenido: str) -> dict[str, dict[str, dict]]:
    """Convierte el CSV en {escenario: {periodo: fila}}. Lanza ValueError con un mensaje claro si no es válido."""
    lector = csv.DictReader(io.StringIO(contenido))
    if lector.fieldnames is None or [c.strip() for c in lector.fieldnames] != COLUMNAS:
        raise ValueError(f"El CSV debe tener exactamente las columnas: {', '.join(COLUMNAS)}")
    datos: dict[str, dict[str, dict]] = {}
    for n, fila in enumerate(lector, start=2):
        try:
            reg = {"matriculados": float(fila["matriculados"]), "desercion_periodo": float(fila["desercion_periodo"]),
                   "graduados": float(fila["graduados"]), "alertas": float(fila["alertas"]),
                   "cobertura_bienestar": float(fila["cobertura_bienestar"])}
        except (TypeError, ValueError):
            raise ValueError(f"Fila {n}: hay un valor que no es numérico")
        if not 0 <= reg["desercion_periodo"] <= 1 or not 0 <= reg["cobertura_bienestar"] <= 1:
            raise ValueError(f"Fila {n}: la deserción y la cobertura deben estar entre 0 y 1")
        per = fila["periodo"].strip()
        if len(per) != 6 or per[4] != "-" or per[5] not in "12" or not per[:4].isdigit():
            raise ValueError(f"Fila {n}: el periodo «{per}» no tiene el formato AAAA-S")
        datos.setdefault(fila["escenario"].strip(), {})[per] = reg
    if not datos:
        raise ValueError("El CSV no tiene filas")
    return datos


def cargar() -> dict[str, dict[str, dict]]:
    """Proyecciones vigentes. Si el archivo no existe devuelve un diccionario vacío."""
    p = ruta()
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return parsear(f.read())


def guardar(contenido: str) -> dict[str, dict[str, dict]]:
    """Valida y reemplaza el archivo de proyecciones."""
    datos = parsear(contenido)
    os.makedirs(os.path.dirname(os.path.abspath(ruta())), exist_ok=True)
    with open(ruta(), "w", encoding="utf-8", newline="") as f:
        f.write(contenido)
    return datos
