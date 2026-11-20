"""Exporta las proyecciones del modelo por periodo académico para cargarlas en el CRUD (tablero real frente a simulado).
Uso: python exportar_proyecciones.py <modelo.mdl> <salida.csv>
El semestre de simulación t corresponde al periodo número t - 1 contado desde 2015-1 (el CRUD y el modelo arrancan vacíos en 2015-1).
Las políticas de E1 y E3 empiezan en 2026-1, el primer periodo después de los datos históricos."""
import csv, sys
import pysd

MDL, SALIDA = sys.argv[1:3]
PERIODOS = [f"{a}-{s}" for a in range(2015, 2031) for s in (1, 2)]          # 2015-1 .. 2030-2
INICIO = PERIODOS.index("2026-1") + 1
ESC = {"E0 Base": {},
       "E1 Alertas tempranas": {"Ef economico": .3, "Ef academico": .6, "Ef adaptacion": .6, "Aplica media": 0, "Aplica tardia": 0, "Inicio politica": INICIO},
       "E3 Permanencia integral": {"Ef economico": .6, "Ef academico": .6, "Ef adaptacion": .6, "Capacidad bienestar": 32, "Inicio politica": INICIO}}
COLS = ["Matriculados", "Desercion periodo", "Graduados periodo", "Alertas nuevas", "Cobertura bienestar"]
m = pysd.read_vensim(MDL)
with open(SALIDA, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["escenario", "periodo", "matriculados", "desercion_periodo", "graduados", "alertas", "cobertura_bienestar"])
    for nombre, p in ESC.items():
        r = m.run(params={"Modo estocastico": 0, **p}, return_columns=COLS, reload=True)
        for k, per in enumerate(PERIODOS):
            x = r.loc[k + 1]
            w.writerow([nombre, per, round(x["Matriculados"], 2), round(x["Desercion periodo"], 5), round(x["Graduados periodo"], 2),
                        round(x["Alertas nuevas"], 2), round(min(1.0, x["Cobertura bienestar"]), 4)])
print("Proyecciones escritas en", SALIDA)
