"""Corre el diseño de experimentos sobre el modelo Vensim con PySD: escenarios, réplicas, validación y sensibilidad.
Uso: python run_experimentos.py <modelo.mdl> <carpeta_csv_crud> <carpeta_salida>"""
import csv, json, os, sys
import numpy as np
import pysd
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

MDL, DATOS, OUT = sys.argv[1:4]; FIG = os.path.join(OUT, "fig"); os.makedirs(FIG, exist_ok=True)
m = pysd.read_vensim(MDL)
REPLICAS, CALENT = 10, 16          # 10 réplicas; se descartan los primeros 16 semestres (calentamiento)
COLS = ["Matriculados", "Desercion periodo", "Desercion cohorte 10", "Graduados periodo", "Cobertura bienestar",
        "Casos pendientes", "Desercion total", "Error conservacion", "Graduacion oportuna pct", "Ingreso"]
CAP_AMPL = 32.0   # capacidad de Bienestar ampliada en 50 %
ALERTAS = {"Ef economico": .3, "Ef academico": .6, "Ef adaptacion": .6, "Aplica media": 0, "Aplica tardia": 0}
INTEGRAL = {"Ef economico": .6, "Ef academico": .6, "Ef adaptacion": .6}
ESC = {
    "E0 Base": {},
    "E1 Alertas tempranas": ALERTAS,
    "E2 Alertas + capacidad 50 %": {**ALERTAS, "Capacidad bienestar": CAP_AMPL},
    "E3 Permanencia integral": {**INTEGRAL, "Capacidad bienestar": CAP_AMPL},
    "E4 Integral sin ampliar y demanda +25 %": {**INTEGRAL, "Factor demanda": 1.25},
}
METR = {"Deserción de cohorte a 10 sem. (%)": "Desercion cohorte 10", "Deserción por periodo (%)": "Desercion periodo",
        "Matriculados": "Matriculados", "Graduados por semestre": "Graduados periodo", "Cobertura de Bienestar (%)": "Cobertura bienestar",
        "Casos en cola": "Casos pendientes"}
ESCALA = {"Desercion periodo": 100, "Cobertura bienestar": 100}

def correr(params, semilla=None):
    p = {"Modo estocastico": 1 if semilla else 0, **params}
    if semilla: np.random.seed(semilla); p["Semilla"] = semilla
    return m.run(params=p, return_columns=COLS, reload=True)

def ic95(x):
    x = np.asarray(x); h = stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)); return x.mean(), h

res, series, err_max = {}, {}, 0.0
for nombre, p in ESC.items():
    reps = []
    for s in range(1, REPLICAS + 1):
        r = correr(p, s); err_max = max(err_max, r["Error conservacion"].abs().max())
        w = r.loc[CALENT:]; reps.append({k: float(w[c].mean() * ESCALA.get(c, 1)) for k, c in METR.items()})
        series.setdefault(nombre, []).append(r)
    res[nombre] = {k: [x[k] for x in reps] for k in METR}

tabla = {e: {k: ic95(v) for k, v in d.items()} for e, d in res.items()}
# diferencias pareadas contra la base (números aleatorios comunes: misma semilla en cada réplica)
dif = {}
for e in list(ESC)[1:]:
    for k in ("Deserción de cohorte a 10 sem. (%)", "Graduados por semestre", "Matriculados"):
        d = np.array(res[e][k]) - np.array(res["E0 Base"][k]); mu, h = ic95(d)
        dif.setdefault(e, {})[k] = (mu, h, stats.ttest_rel(res[e][k], res["E0 Base"][k]).pvalue)
K = "Deserción de cohorte a 10 sem. (%)"; E = list(ESC)
extra = {f"{a.split()[0]}_menos_{b.split()[0]}": ic95(np.array(res[a][K]) - np.array(res[b][K])) for a, b in ((E[2], E[1]), (E[3], E[2]), (E[4], E[3]))}

# ---------- Validación contra el CRUD ----------
obs = [r for r in csv.DictReader(open(os.path.join(DATOS, "matriculas_por_periodo.csv"), encoding="utf-8")) if r["periodo"] >= "2020-1"]
o_des = np.array([int(r["desertan"]) / int(r["matriculas"]) * 100 for r in obs]); o_mat = np.array([int(r["matriculas"]) for r in obs], float)
o_gra = np.array([int(r["se_graduan"]) for r in obs], float)
# el CRUD arranca vacío en 2015-1 igual que el modelo en t = 0; 2020-1 a 2025-1 corresponde a t = 11..21
ven = [r.loc[11:21] for r in series["E0 Base"]]
s_des = np.array([(w["Desercion periodo"] * 100).mean() for w in ven]); s_mat = np.array([w["Matriculados"].mean() for w in ven]); s_gra = np.array([w["Graduados periodo"].mean() for w in ven])
val = {}
for k, so, oo in (("Deserción por periodo (%)", s_des, o_des), ("Matriculados", s_mat, o_mat), ("Graduados por semestre", s_gra, o_gra)):
    t = stats.ttest_ind(so, oo, equal_var=False)
    val[k] = dict(sim=ic95(so), obs=ic95(oo), t=t.statistic, p=t.pvalue, n_obs=len(oo))

# ---------- Casos extremos (corridas deterministas) ----------
ext = {}
r = correr({"Ingreso media": 0}); ext["Sin ingresos: matriculados máx."] = float(r["Matriculados"].abs().max())
r = correr({"Calibracion": 1.5}); ext["Calibración 1,5: deserción cohorte (%)"] = float(r["Desercion cohorte 10"].iloc[-1])
r = correr({"Calibracion": 0.3}); ext["Calibración 0,3: deserción cohorte (%)"] = float(r["Desercion cohorte 10"].iloc[-1])
r = correr({**ESC["E1 Alertas tempranas"], "Capacidad bienestar": 0}); ext["E1 con capacidad 0: deserción cohorte (%)"] = float(r["Desercion cohorte 10"].iloc[-1])
r = correr({"Ef economico": 1, "Ef academico": 1, "Ef adaptacion": 1, "Capacidad bienestar": 1000}); ext["Efectividad 1 y capacidad ilimitada (%)"] = float(r["Desercion cohorte 10"].iloc[-1])
ext["Eficiencia 1: rezago máximo"] = float(m.run(params={"Modo estocastico": 0, "Eficiencia titulacion": 1}, return_columns=["Rezago"], reload=True)["Rezago"].max())
base_det = correr({}); ext["Base determinista: deserción cohorte (%)"] = float(base_det["Desercion cohorte 10"].iloc[-1])
ext["Error de conservación máximo (todas las corridas)"] = float(err_max)

# ---------- Sensibilidad (determinista) ----------
caps = np.arange(0, 61, 2.5); sens_cap = []
for cap in caps:
    r = correr({**ESC["E1 Alertas tempranas"], "Capacidad bienestar": float(cap)}).loc[CALENT:]
    sens_cap.append((float(cap), float(r["Desercion cohorte 10"].mean()), float(r["Cobertura bienestar"].mean() * 100)))
efs = np.round(np.arange(0, 1.01, .1), 2); sens_ef = []
for ef in efs:
    r = correr({"Ef economico": ef, "Ef academico": ef, "Ef adaptacion": ef, "Capacidad bienestar": CAP_AMPL}).loc[CALENT:]
    sens_ef.append((float(ef), float(r["Desercion cohorte 10"].mean())))
ref = correr(ESC["E3 Permanencia integral"]).loc[CALENT:]["Desercion cohorte 10"].mean()
torn = []
for prm, base_v in (("Calibracion", .715), ("Max reduccion", .5), ("Capacidad bienestar", CAP_AMPL), ("Prob alerta", .185),
                    ("Fraccion abandono cola", .5), ("Eficiencia titulacion", .66)):
    vals = []
    for f in (.8, 1.2):
        r = correr({**ESC["E3 Permanencia integral"], prm: base_v * f}).loc[CALENT:]; vals.append(float(r["Desercion cohorte 10"].mean()))
    torn.append((prm, vals[0], vals[1]))
efp = []
for f in (.8, 1.2):
    r = correr({**ESC["E3 Permanencia integral"], "Ef economico": .6 * f, "Ef academico": .6 * f, "Ef adaptacion": .6 * f}).loc[CALENT:]
    efp.append(float(r["Desercion cohorte 10"].mean()))
torn.append(("Efectividad (tres palancas)", *efp)); torn.sort(key=lambda t: abs(t[2] - t[1]))

# ---------- Figuras ----------
AZ, GR, RO, VE, NA = "#1f4e79", "#8c8c8c", "#c0504d", "#4f8f3a", "#d98c1f"
COL = dict(zip(ESC, [GR, NA, AZ, VE, RO]))
def estilo(ax): ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color="#e6e6e6"); ax.set_axisbelow(True)

fig, ax = plt.subplots(figsize=(6.4, 3.4))
for r in series["E0 Base"]: ax.plot(r.index, r["Matriculados"], color=AZ, alpha=.25, lw=1)
ax.plot(base_det.index, base_det["Matriculados"], color=AZ, lw=2.2, label="Matriculados (determinista)")
ax.axvline(CALENT, color=GR, ls="--", lw=1); ax.text(CALENT + .4, 60, "fin del calentamiento", fontsize=8, color=GR)
todo = list(csv.DictReader(open(os.path.join(DATOS, "matriculas_por_periodo.csv"), encoding="utf-8")))
ax.scatter(np.arange(len(todo)) + 1, [int(r["matriculas"]) for r in todo], s=14, color=RO, zorder=3, label="Matrículas CRUD 2015-1 a 2025-1")
ax.set_xlabel("Semestre de simulación"); ax.set_ylabel("Estudiantes"); ax.legend(fontsize=8, frameon=False, loc="lower right"); estilo(ax)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "evolucion_base.png"), dpi=200); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.4)); k = "Deserción de cohorte a 10 sem. (%)"
nom = list(ESC); mu = [tabla[e][k][0] for e in nom]; h = [tabla[e][k][1] for e in nom]
ax.bar(range(len(nom)), mu, yerr=h, capsize=4, color=[COL[e] for e in nom], width=.6)
for i, v in enumerate(mu): ax.text(i, v + h[i] + .6, f"{v:.1f}", ha="center", fontsize=8)
ax.axhline(35, color=RO, ls=":", lw=1); ax.text(-0.42, 35.6, "meta 35 %", fontsize=8, color=RO, ha="left", va="bottom")
ax.set_xticks(range(len(nom))); ax.set_xticklabels([e.split(" ", 1)[0] for e in nom]); ax.set_ylabel("Deserción de cohorte (%)"); estilo(ax)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "escenarios_ic95.png"), dpi=200); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.2))
for e in nom:
    sr = np.mean([r["Cobertura bienestar"].values for r in series[e]], axis=0) * 100
    ax.plot(series[e][0].index, sr, color=COL[e], lw=1.8, label=e.split(" ", 1)[0])
ax.set_xlabel("Semestre de simulación"); ax.set_ylabel("Cobertura de Bienestar (%)"); ax.set_ylim(0, 105); ax.legend(fontsize=8, frameon=False, ncol=5, loc="lower left"); estilo(ax)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "cobertura_escenarios.png"), dpi=200); plt.close(fig)

fig, ax1 = plt.subplots(figsize=(6.4, 3.2)); c_ = np.array(sens_cap)
ax1.plot(c_[:, 0], c_[:, 1], color=AZ, lw=2); ax1.set_xlabel("Capacidad de Bienestar (casos por semestre)"); ax1.set_ylabel("Deserción de cohorte (%)", color=AZ)
ax2 = ax1.twinx(); ax2.plot(c_[:, 0], c_[:, 2], color=NA, lw=1.6, ls="--"); ax2.set_ylabel("Cobertura (%)", color=NA)
ax1.axvline(21.5, color=GR, lw=1, ls=":"); ax1.text(22, c_[:, 1].max() - .3, "capacidad actual", fontsize=8, color=GR)
ax1.spines[["top"]].set_visible(False); ax2.spines[["top"]].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "sensibilidad_capacidad.png"), dpi=200); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.2))
for i, (prm, lo, hi) in enumerate(torn):
    ax.barh(i, lo - ref, left=ref, color=AZ, height=.55); ax.barh(i, hi - ref, left=ref, color=NA, height=.55)
ax.axvline(ref, color="k", lw=.8); ax.set_yticks(range(len(torn))); ax.set_yticklabels([t[0] for t in torn], fontsize=8)
ax.set_xlabel("Deserción de cohorte en E3 (%)  ·  azul: −20 %   naranja: +20 %"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "tornado_e3.png"), dpi=200); plt.close(fig)

json.dump(dict(tabla=tabla, dif=dif, extra=extra, val=val, ext=ext, sens_cap=sens_cap, sens_ef=sens_ef, torn=torn, ref_e3=ref,
               reps=res, escenarios=ESC), open(os.path.join(OUT, "resultados.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
for e in tabla:
    print(e, {k: f"{v[0]:.2f} ± {v[1]:.2f}" for k, v in tabla[e].items()})
print("dif", json.dumps(dif, indent=0, ensure_ascii=False, default=float)); print("extra", extra)
print("val", json.dumps(val, indent=0, ensure_ascii=False, default=float)); print("ext", json.dumps(ext, indent=0, ensure_ascii=False))
print("sens_ef", sens_ef); print("torn", torn, ref)
