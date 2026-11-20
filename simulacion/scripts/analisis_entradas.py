"""Análisis de datos de entrada: ajuste de distribuciones con los CSV exportados del CRUD.
Uso: python analisis_entradas.py <carpeta_csv> <carpeta_figuras>"""
import csv, json, os, sys
import numpy as np
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

src, figs = sys.argv[1], sys.argv[2]; os.makedirs(figs, exist_ok=True)
leer = lambda n: list(csv.DictReader(open(os.path.join(src, n), encoding="utf-8")))
BASE = np.array([.204, .117, .087, .076, .074, .060, .054, .033, .023, .024])
R = {}

def chi2_normal(x, mu, sd, k=5):
    bordes = stats.norm.ppf(np.linspace(0, 1, k + 1), mu, sd)  # clases equiprobables
    obs = np.histogram(x, bins=np.r_[-np.inf, bordes[1:-1], np.inf])[0]; esp = np.full(k, len(x) / k)
    est = ((obs - esp) ** 2 / esp).sum(); gl = k - 1 - 2
    return est, gl, 1 - stats.chi2.cdf(est, gl)

# 1. Llegadas por semestre
x = np.array([int(r["estudiantes"]) for r in leer("ingresos_por_cohorte.csv")], float)
mu, sd = x.mean(), x.std(ddof=1); a, b = x.min(), x.max()
ks_n = stats.kstest(x, stats.norm(mu, sd).cdf); ks_u = stats.kstest(x, stats.uniform(a - .5, b - a + 1).cdf)
lam = mu; ks_p = stats.kstest(x, stats.poisson(lam,).cdf)
ch = chi2_normal(x, mu, sd)
R["llegadas"] = dict(n=len(x), media=mu, de=sd, min=a, max=b, cv=sd / mu, ks_normal=(ks_n.statistic, ks_n.pvalue),
                     ks_uniforme=(ks_u.statistic, ks_u.pvalue), ks_poisson=(ks_p.statistic, ks_p.pvalue), chi2_normal=ch,
                     disp_poisson=sd ** 2 / mu)
fig, ax = plt.subplots(figsize=(6, 3.4))
ax.hist(x, bins=np.arange(52.5, 80, 5), density=True, color="#9fb7d4", edgecolor="white", label="CRUD (21 cohortes)")
g = np.linspace(48, 82, 200)
ax.plot(g, stats.norm.pdf(g, mu, sd), color="#1f4e79", lw=2, label=f"Normal({mu:.1f}; {sd:.1f})")
ax.plot(g, stats.uniform.pdf(g, a - .5, b - a + 1), color="#c0504d", lw=2, ls="--", label=f"Uniforme({a:.0f}; {b:.0f})")
ax.plot(g, stats.norm.pdf(g, lam, np.sqrt(lam)), color="#7f7f7f", lw=1.5, ls=":", label=f"Poisson({lam:.1f}) aprox.")
ax.set_xlabel("Estudiantes que ingresan por semestre"); ax.set_ylabel("Densidad"); ax.legend(fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(os.path.join(figs, "ajuste_llegadas.png"), dpi=200); plt.close(fig)

# 2. Tasa de deserción en primer semestre por cohorte
d = leer("desercion_sem1_por_cohorte.csv")
p = np.array([int(r["desertan"]) / int(r["matriculados_sem1"]) for r in d]); n1 = np.array([int(r["matriculados_sem1"]) for r in d])
mp, sp = p.mean(), p.std(ddof=1); ks_p1 = stats.kstest(p, stats.norm(mp, sp).cdf); sw = stats.shapiro(p)
pbar = sum(int(r["desertan"]) for r in d) / n1.sum(); sd_binom = np.sqrt(pbar * (1 - pbar) / n1.mean())
R["tasa_sem1"] = dict(n=len(p), media=mp, de=sp, cv=sp / mp, ks_normal=(ks_p1.statistic, ks_p1.pvalue), shapiro=(sw.statistic, sw.pvalue),
                      p_agregada=pbar, de_binomial_esperada=sd_binom)
fig, ax = plt.subplots(figsize=(6, 3.4))
ax.hist(p * 100, bins=6, density=True, color="#9fb7d4", edgecolor="white", label="CRUD (21 cohortes)")
g = np.linspace(0, 30, 200); ax.plot(g, stats.norm.pdf(g, mp * 100, sp * 100), color="#1f4e79", lw=2, label=f"Normal({100*mp:.1f} %; {100*sp:.1f} %)")
ax.set_xlabel("Deserción en primer semestre (%)"); ax.set_ylabel("Densidad"); ax.legend(fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(os.path.join(figs, "ajuste_tasa_sem1.png"), dpi=200); plt.close(fig)

# 3. Tasas por nivel y calibración (mínimos cuadrados ponderados por matrículas)
nv = leer("matriculas_por_nivel.csv")
obs = np.array([int(r["desertan"]) / int(r["matriculas"]) for r in nv[:10]]); w = np.array([int(r["matriculas"]) for r in nv[:10]], float)
cal = (w * obs * BASE).sum() / (w * BASE ** 2).sum()
rez = nv[10:]; mr = sum(int(r["matriculas"]) for r in rez)
R["niveles"] = dict(tasas_obs=obs.tolist(), matriculas=w.tolist(), calibracion=cal,
                    eficiencia_titulacion=int(nv[9]["se_graduan"]) / (int(nv[9]["matriculas"]) - int(nv[9]["desertan"])),
                    grad_rezago=sum(int(r["se_graduan"]) for r in rez) / mr, des_rezago=sum(int(r["desertan"]) for r in rez) / mr)
chi_niv = stats.chisquare([int(r["desertan"]) for r in nv[:10]], f_exp=w * BASE * cal * (sum(int(r["desertan"]) for r in nv[:10]) / (w * BASE * cal).sum()))
R["niveles"]["chi2_forma"] = (chi_niv.statistic, chi_niv.pvalue)
fig, ax = plt.subplots(figsize=(6, 3.4)); k = np.arange(1, 11)
ax.bar(k - .2, obs * 100, .4, color="#9fb7d4", label="Observada (CRUD)"); ax.bar(k + .2, BASE * cal * 100, .4, color="#1f4e79", label=f"Modelo (SPADIES × {cal:.2f})")
ax.set_xticks(k); ax.set_xlabel("Semestre"); ax.set_ylabel("Deserción por periodo (%)"); ax.legend(fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False); fig.tight_layout(); fig.savefig(os.path.join(figs, "tasas_por_nivel.png"), dpi=200); plt.close(fig)

# 4. Alertas y capacidad de Bienestar (se omite 2015-1: solo había una cohorte)
ap = leer("alertas_y_apoyos_por_periodo.csv")[1:]
al = np.array([int(r["alertas"]) for r in ap]); m12 = np.array([int(r["matriculas_sem1_2"]) for r in ap]); cap = np.array([int(r["apoyos_asignados"]) for r in ap], float)
ks_cap = stats.kstest(cap, stats.norm(cap.mean(), cap.std(ddof=1)).cdf)
R["bienestar"] = dict(prob_alerta=al.sum() / m12.sum(), alertas_media=al.mean(), capacidad_media=cap.mean(), capacidad_de=cap.std(ddof=1),
                      disp_capacidad=cap.var(ddof=1) / cap.mean(), ks_capacidad_normal=(ks_cap.statistic, ks_cap.pvalue))
json.dump(R, open(os.path.join(figs, "..", "entradas.json"), "w"), indent=1, default=float)
print(json.dumps(R, indent=1, default=float))
