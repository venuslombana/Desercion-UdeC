"""Exporta desde la base del CRUD las series históricas que alimentan el modelo de simulación.
Uso: python exportar_datos_crud.py <ruta.db | URL de SQLAlchemy> <carpeta_salida>
Usa las mismas consultas del endpoint GET /api/exportacion/historicos del CRUD (crud/app/exportacion.py),
así que el archivo descargado desde la aplicación y el generado aquí son idénticos.
Genera: ingresos_por_cohorte.csv, matriculas_por_periodo.csv, matriculas_por_nivel.csv,
desercion_sem1_por_cohorte.csv, alertas_y_apoyos_por_periodo.csv"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "crud"))
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app import exportacion

origen, salida = sys.argv[1], sys.argv[2]
os.makedirs(salida, exist_ok=True)
eng = create_engine(origen if "://" in origen else f"sqlite:///{origen}")
with Session(eng) as db:
    for nombre in exportacion.CONSULTAS:
        cab, filas = exportacion.datos(db, nombre)
        with open(os.path.join(salida, f"{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
            f.write(exportacion.a_csv(cab, filas))
print("Exportado en", salida)
