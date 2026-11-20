"""Monte Carlo (10 000 iteraciones) de la deserción de cohorte y modelo financiero de la permanencia integral (E3).
Uso: python montecarlo_financiero.py <modelo.mdl> <carpeta_csv_crud> <carpeta_salida>"""
import csv, json, os, sys
import numpy as np
import pysd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

MDL, DATOS, OUT = sys.argv[1:4]; FIG = os.path.join(OUT, "fig"); os.makedirs(FIG, exist_ok=True)
BASE = np.array([.204, .117, .087, .076, .074, .060, .054, .033, .023, .024])
ETAPA = np.array([0, 0, 1, 1, 1, 2, 2, 2, 2, 2])
PESOS = np.array([[.3, .3, .4], [.3, .5, .2], [.4, .4, .2]])
AZ, GR, NA, RO = "#1f4e79", "#8c8c8c", "#d98c1f", "#c0504d"

# Error estándar de la calibración (mínimos cuadrados ponderados con varianza binomial por nivel)
nv = list(csv.DictReader(open(os.path.join(DATOS, "matriculas_por_nivel.csv"), encoding="utf-8")))[:10]
n = np.array([int(r["matriculas"]) for r in nv], float); o = np.array([int(r["desertan"]) for r in nv]) / n
cal = (n * o * BASE).sum() / (n * BASE ** 2).sum(); se_cal = np.sqrt(((n * BASE) ** 2 * o * (1 - o) / n).sum()) / (n * BASE ** 2).sum()

# ---------- Monte Carlo ----------
N = 10_000; rng = np.random.default_rng(2026)
def cohorte(politica):
    c = rng.normal(cal, se_cal, N)
    choque = np.clip(rng.normal(1, .236, (N, 10)), .4, 1.6)          # un choque por cada periodo que vive la cohorte
    if politica:
        ef = rng.triangular(.3, .6, .8, (N, 3)); mx = rng.uniform(.4, .6, N)
        red = mx[:, None] * (ef @ PESOS.T)                             # reducción por etapa (N x 3)
        red = red[:, ETAPA]
    else: red = 0
    tasas = BASE * c[:, None] * choque * (1 - red)
    return 100 * (1 - np.prod(1 - tasas, axis=1))
mc0, mc3 = cohorte(False), cohorte(True)
pct = lambda x: {f"P{q}": float(np.percentile(x, q)) for q in (5, 25, 50, 75, 95)}
MC = dict(iteraciones=N, calibracion=(cal, se_cal), base=dict(media=float(mc0.mean()), de=float(mc0.std()), **pct(mc0), p_meta=float((mc0 < 35).mean())),
          e3=dict(media=float(mc3.mean()), de=float(mc3.std()), **pct(mc3), p_meta=float((mc3 < 35).mean())),
          p_e3_mejor=float((mc3 < mc0).mean()))
fig, ax = plt.subplots(figsize=(6.4, 3.4)); b = np.linspace(10, 75, 66)
ax.hist(mc0, bins=b, color=GR, alpha=.65, label="E0 Base"); ax.hist(mc3, bins=b, color=AZ, alpha=.75, label="E3 Permanencia integral")
ax.axvline(35, color=RO, ls=":", lw=1.2); ax.text(35.5, ax.get_ylim()[1] * .92, "meta 35 %", color=RO, fontsize=8)
for x, c_ in ((mc0, GR), (mc3, AZ)):
    for q in (5, 95): ax.axvline(np.percentile(x, q), color=c_, lw=.8, ls="--")
ax.set_xlabel("Deserción de cohorte a 10 semestres (%)"); ax.set_ylabel("Frecuencia (10 000 iteraciones)")
ax.legend(fontsize=8, frameon=False); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "montecarlo.png"), dpi=200); plt.close(fig)

# ---------- Modelo financiero ----------
m = pysd.read_vensim(MDL)
INICIO, H = 20, 10                     # la política arranca en estado estable (t = 20) y se evalúa 10 semestres (5 años)
TASA_EA = .12; i_s = (1 + TASA_EA) ** .5 - 1
SUP = dict(ingreso_estudiante=2.0, inversion=dict(desarrollo=18.0, capacitacion=3.0),
           operacion=dict(servidor_y_soporte=1.8, profesional_bienestar=15.6, monitorias=19.2, apoyos_economicos=9.0))  # millones de COP
def extra_matriculados(ef):
    p = {"Modo estocastico": 0, "Inicio politica": INICIO, "Ef economico": ef, "Ef academico": ef, "Ef adaptacion": ef, "Capacidad bienestar": 32.0}
    a = m.run(params=p, return_columns=["Matriculados"], reload=True)["Matriculados"]
    b = m.run(params={"Modo estocastico": 0}, return_columns=["Matriculados"], reload=True)["Matriculados"]
    return (a - b).loc[INICIO + 1:INICIO + H].values             # estudiantes adicionales que se matriculan cada semestre
def flujo(ef, ing, extra=None):
    extra = extra_matriculados(ef) if extra is None else extra
    inv = sum(SUP["inversion"].values()); op = sum(SUP["operacion"].values())
    ben = extra * ing; neto = np.r_[-inv, ben - op]
    vpn = float(sum(v / (1 + i_s) ** t for t, v in enumerate(neto)))
    return dict(extra=extra, beneficio=ben, neto=neto, vpn=vpn, acumulado=np.cumsum(neto),
                bc=float(sum(v / (1 + i_s) ** (t + 1) for t, v in enumerate(ben)) / (inv + sum(op / (1 + i_s) ** (t + 1) for t in range(H)))))
def tir(neto):
    lo, hi = -.99, 5.0
    f = lambda r: sum(v / (1 + r) ** t for t, v in enumerate(neto))
    if f(lo) * f(hi) > 0: return None
    for _ in range(200):
        mid = (lo + hi) / 2; (lo, hi) = (mid, hi) if f(lo) * f(mid) > 0 else (lo, mid)
    return mid
F = flujo(.6, SUP["ingreso_estudiante"]); r_s = tir(F["neto"])
rec = next((t + 1 for t, v in enumerate(F["acumulado"][1:]) if v >= 0), None)
op = sum(SUP["operacion"].values()); sost = float(F["beneficio"][-1] / op)
FIN = dict(supuestos=SUP, tasa_ea=TASA_EA, tasa_semestral=i_s, extra=F["extra"].tolist(), beneficio=F["beneficio"].tolist(), neto=F["neto"].tolist(),
           acumulado=F["acumulado"].tolist(), vpn=F["vpn"], bc=F["bc"], tir_semestral=r_s, tir_anual=(1 + r_s) ** 2 - 1 if r_s else None,
           recuperacion_semestre=rec, indice_sostenibilidad=sost)
efs = [.3, .4, .5, .6, .7, .8]; ings = [1.2, 1.6, 2.0, 2.4, 2.8]; cache = {e: extra_matriculados(e) for e in efs}
grid = [[flujo(e, g, cache[e])["vpn"] for g in ings] for e in efs]
FIN.update(sens_ef=efs, sens_ing=ings, sens_vpn=grid)
# punto de equilibrio en ingreso por estudiante con efectividad 0,6
lo, hi = .1, 5.0
for _ in range(60):
    mid = (lo + hi) / 2; lo, hi = (mid, hi) if flujo(.6, mid, cache[.6])["vpn"] < 0 else (lo, mid)
FIN["ingreso_equilibrio"] = mid

fig, ax = plt.subplots(figsize=(6.4, 3.2)); t = np.arange(H + 1)
ax.bar(t, F["neto"], color=[RO if v < 0 else AZ for v in F["neto"]], width=.6, label="Flujo neto")
ax.plot(t, F["acumulado"], color=NA, marker="o", ms=3, lw=1.6, label="Flujo acumulado")
ax.axhline(0, color="k", lw=.6); ax.set_xlabel("Semestre desde el arranque"); ax.set_ylabel("Millones de COP"); ax.legend(fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(os.path.join(FIG, "flujo_caja.png"), dpi=200); plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.4)); g = np.array(grid)
im = ax.imshow(g, cmap="RdBu", vmin=-abs(g).max(), vmax=abs(g).max(), aspect="auto", origin="lower")
ax.set_xticks(range(len(ings))); ax.set_xticklabels([f"{x:.1f}" for x in ings]); ax.set_yticks(range(len(efs))); ax.set_yticklabels([f"{x:.1f}" for x in efs])
for i in range(len(efs)):
    for j in range(len(ings)): ax.text(j, i, f"{g[i, j]:.0f}", ha="center", va="center", fontsize=8, color="white" if abs(g[i, j]) > abs(g).max() * .55 else "black")
ax.set_xlabel("Ingreso neto por estudiante-semestre (millones de COP)"); ax.set_ylabel("Efectividad de las palancas")
fig.colorbar(im, ax=ax, label="VPN (millones de COP)"); fig.tight_layout(); fig.savefig(os.path.join(FIG, "sensibilidad_vpn.png"), dpi=200); plt.close(fig)

json.dump(dict(mc=MC, fin=FIN), open(os.path.join(OUT, "mc_fin.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(MC, indent=1)); print({k: v for k, v in FIN.items() if k not in ("supuestos",)})
