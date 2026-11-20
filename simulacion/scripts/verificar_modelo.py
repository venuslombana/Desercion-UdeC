"""Verificación automática del modelo: corridas deterministas de los cinco escenarios contra la tabla de
verificación del informe (valores en t = 40) y error de conservación. La usa el pipeline de CI.
Uso: python verificar_modelo.py <modelo.mdl>"""
import sys
import pysd

ESPERADO = {  # Desercion cohorte 10, Matriculados, Graduados, Desertores (t = 40, Modo estocastico = 0)
    "E0": ({}, (42.91, 548.42, 971.68, 1111.89)),
    "E1": ({"Ef economico": .3, "Ef academico": .6, "Ef adaptacion": .6, "Aplica media": 0, "Aplica tardia": 0}, (39.50, 575.98, 1030.27, 1025.74)),
    "E2": ({"Ef economico": .3, "Ef academico": .6, "Ef adaptacion": .6, "Aplica media": 0, "Aplica tardia": 0, "Capacidad bienestar": 32}, (39.03, 579.80, 1037.60, 1014.60)),
    "E3": ({"Ef economico": .6, "Ef academico": .6, "Ef adaptacion": .6, "Capacidad bienestar": 32}, (32.11, 613.85, 1155.41, 862.74)),
    "E4": ({"Ef economico": .6, "Ef academico": .6, "Ef adaptacion": .6, "Factor demanda": 1.25}, (34.13, 747.66, 1404.65, 1137.69)),
}
COLS = ["Desercion cohorte 10", "Matriculados", "Graduados", "Desertores", "Error conservacion"]
m = pysd.read_vensim(sys.argv[1])
fallas = 0
for esc, (params, esperado) in ESPERADO.items():
    r = m.run(params={"Modo estocastico": 0, **params}, return_columns=COLS, reload=True)
    fin = r.iloc[-1]
    obtenido = tuple(round(float(fin[c]), 2) for c in COLS[:4])
    ok = all(abs(a - b) <= 0.01 for a, b in zip(obtenido, esperado)) and r["Error conservacion"].abs().max() < 1e-6
    fallas += not ok
    print(f"{esc}: {'OK ' if ok else 'FALLA'} obtenido={obtenido} esperado={esperado}")
sys.exit(1 if fallas else 0)
