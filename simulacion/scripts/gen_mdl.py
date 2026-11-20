"""Genera el modelo Vensim (.mdl) de deserción estudiantil con tres vistas de diagrama.
Uso: python gen_mdl2.py <salida.mdl>"""
import math, re, sys

E = {}
ST, FL, RT = "Estudiantes", "Estudiantes/Semestre", "1/Semestre"
def eq(n, e, u, c=""): E[n] = (e, u, c)

# ---------------- Ecuaciones ----------------
eq("Sem 1", "INTEG(Ingreso - Avance 1 - Desercion 1, 0)", ST, "Estudiantes matriculados en primer semestre.")
for i in range(2, 10):
    eq(f"Sem {i}", f"INTEG(Avance {i-1} - Avance {i} - Desercion {i}, 0)", ST, f"Estudiantes matriculados en el semestre {i}.")
eq("Sem 10", "INTEG(Avance 9 - Graduacion oportuna - Paso a rezago - Desercion 10, 0)", ST, "Estudiantes en el semestre 10 (9 del plan más uno de margen).")
eq("Rezago", "INTEG(Paso a rezago - Graduacion rezago - Desercion rezago, 0)", ST, "Estudiantes que terminaron el semestre 10 sin graduarse.")
eq("Graduados", "INTEG(Graduacion oportuna + Graduacion rezago, 0)", ST, "Graduados acumulados.")
eq("Desertores", "INTEG(Desercion total, 0)", ST, "Contador de desertores acumulados.")
eq("Ingresados acum", "INTEG(Ingreso, 0)", ST, "Contador de ingresos; se usa para verificar la conservación.")
eq("Casos pendientes", "INTEG(Alertas nuevas - Casos atendidos - Casos vencidos, 0)", ST, "Cola de casos con alerta temprana que esperan atención de Bienestar.")

eq("Ingreso", "IF THEN ELSE(Modo estocastico = 1, RANDOM NORMAL(Ingreso minimo, Ingreso maximo, Ingreso media, Ingreso de, Semilla), Ingreso media) * Factor demanda",
   FL, "Llegadas por semestre: Normal(65,8; 6,5) truncada en [50, 80], ajustada con las 21 cohortes exportadas del CRUD.")
for i in range(1, 10):
    eq(f"Avance {i}", f"Sem {i} / TIME STEP - Desercion {i}", FL, f"Estudiantes que pasan del semestre {i} al {i+1}. Requiere TIME STEP = 1 semestre.")
for i in range(1, 11):
    eq(f"Desercion {i}", f"Sem {i} * Tasa {i}", FL, f"Estudiantes que abandonan en el semestre {i}.")
eq("Avance 10", "Sem 10 / TIME STEP - Desercion 10", FL, "Estudiantes que terminan el semestre 10.")
eq("Graduacion oportuna", "Avance 10 * Eficiencia titulacion", FL, "")
eq("Paso a rezago", "Avance 10 * (1 - Eficiencia titulacion)", FL, "")
eq("Graduacion rezago", "Rezago * Tasa grad rezago", FL, "")
eq("Desercion rezago", "Rezago * Tasa des rezago", FL, "")
eq("Desercion total", " + ".join(f"Desercion {i}" for i in range(1, 11)) + " + Desercion rezago", FL, "Todas las salidas por deserción del semestre.")
eq("Alertas nuevas", "(Sem 1 + Sem 2) * Prob alerta", FL, "Alertas tempranas generadas en los semestres 1 y 2.")
eq("Casos atendidos", "MIN(Casos pendientes / TIME STEP, Capacidad bienestar)", FL, "Casos que Bienestar alcanza a atender (recurso limitado).")
eq("Casos vencidos", "(Casos pendientes / TIME STEP - Casos atendidos) * Fraccion abandono cola", FL, "Casos no atendidos que salen de la cola.")

etapa = lambda i: "temprana" if i <= 2 else "media" if i <= 5 else "tardia"
for i in range(1, 11):
    eq(f"Tasa {i}", f"Tasa base {i} * Multiplicador comun * (1 - Reduccion {etapa(i)})", RT, f"Tasa de deserción por periodo del semestre {i}.")
eq("Multiplicador comun", "Calibracion * Ruido desercion", "Dmnl", "Calibración institucional por choque aleatorio del periodo.")
eq("Ruido desercion", "IF THEN ELSE(Modo estocastico = 1, RANDOM NORMAL(0.4, 1.6, 1, CV desercion, Semilla + 1), 1)", "Dmnl",
   "Variación de las tasas entre periodos. CV = 0,236, estimado con la deserción de primer semestre de 21 cohortes del CRUD.")
W = "(Peso eco {e} * Ef economico + Peso aca {e} * Ef academico + Peso ada {e} * Ef adaptacion)"
eq("Reduccion temprana", "Politica activa * Aplica temprana * Max reduccion * Cobertura bienestar * " + W.format(e="temprana"), "Dmnl",
   "Reducción de la tasa en semestres 1-2. Se multiplica por la cobertura porque la ruta de apoyo empieza con la alerta temprana.")
eq("Reduccion media", "Politica activa * Aplica media * Max reduccion * " + W.format(e="media"), "Dmnl", "Reducción en semestres 3-5.")
eq("Reduccion tardia", "Politica activa * Aplica tardia * Max reduccion * " + W.format(e="tardia"), "Dmnl", "Reducción en semestres 6-10.")
eq("Politica activa", "IF THEN ELSE(Time >= Inicio politica, 1, 0)", "Dmnl", "Vale 1 desde el semestre en que arrancan las políticas.")
eq("Cobertura bienestar", "MIN(1, XIDZ(Casos atendidos, Casos pendientes / TIME STEP, 1))", "Dmnl", "Fracción de la cola que recibe atención en el semestre.")

eq("Matriculados", " + ".join(f"Sem {i}" for i in range(1, 11)) + " + Rezago", ST, "")
eq("Desercion periodo", "ZIDZ(Desercion total * TIME STEP, Matriculados)", "Dmnl", "Tasa de deserción por periodo (indicador SPADIES).")
eq("Retencion 10", " * ".join(f"(1 - Tasa {i} * TIME STEP)" for i in range(1, 11)), "Dmnl", "Fracción de una cohorte que termina el semestre 10 con las tasas vigentes.")
eq("Desercion cohorte 10", "100 * (1 - Retencion 10)", "Dmnl", "Deserción acumulada de cohorte a 10 semestres, en porcentaje.")
eq("Graduacion oportuna pct", "100 * Retencion 10 * Eficiencia titulacion", "Dmnl", "Graduación oportuna de cohorte, en porcentaje.")
eq("Graduados periodo", "Graduacion oportuna + Graduacion rezago", FL, "")
eq("Error conservacion", "Ingresados acum - (Matriculados + Graduados + Desertores)", ST, "Debe valer 0 en todo instante.")

BASE = [.204, .117, .087, .076, .074, .060, .054, .033, .023, .024]
for i, b in enumerate(BASE, 1): eq(f"Tasa base {i}", f"{b}", RT, f"Tasa por periodo del perfil SPADIES, semestre {i}.")
for n, v, u, c in [
    ("Ingreso media", 65.8, FL + " [50,80,0.1]", "Media ajustada con el CRUD."),
    ("Ingreso de", 6.5, FL + " [0,15,0.1]", "Desviación estándar ajustada con el CRUD."),
    ("Ingreso minimo", 50, FL, "Truncamiento inferior."), ("Ingreso maximo", 80, FL, "Truncamiento superior."),
    ("Factor demanda", 1, "Dmnl [0.5,1.5,0.05]", "1 = demanda actual; 1,25 = escenario de aumento de demanda."),
    ("Modo estocastico", 1, "Dmnl [0,1,1]", "1 = llegadas y tasas aleatorias; 0 = corrida determinista."),
    ("Semilla", 1, "Dmnl [1,100,1]", "Semilla de números aleatorios. Se cambia en cada réplica (1 a 10)."),
    ("CV desercion", 0.236, "Dmnl [0,0.5,0.01]", "Coeficiente de variación de las tasas entre periodos."),
    ("Calibracion", 0.715, "Dmnl [0.3,1.5,0.005]", "Mínimos cuadrados ponderados de las tasas observadas en el CRUD frente al perfil SPADIES."),
    ("Eficiencia titulacion", 0.66, "Dmnl [0.3,1,0.01]", "Fracción que se gradúa al terminar el semestre 10 (CRUD: 0,664)."),
    ("Tasa grad rezago", 0.12, RT, "CRUD: 0,119."), ("Tasa des rezago", 0.04, RT, "CRUD: 0,039."),
    ("Prob alerta", 0.185, RT, "Alertas por estudiante de semestres 1-2 en cada periodo (CRUD: 0,185)."),
    ("Capacidad bienestar", 21.5, FL + " [0,80,0.5]", "Casos que Bienestar atiende por semestre (CRUD: 21,6 apoyos por periodo)."),
    ("Fraccion abandono cola", 0.5, "Dmnl [0,1,0.05]", "Supuesto: la mitad de los casos no atendidos sale de la cola cada semestre."),
    ("Max reduccion", 0.5, "Dmnl [0,1,0.05]", "Supuesto: reducción máxima de una tasa con política 100 % efectiva."),
    ("Ef economico", 0, "Dmnl [0,1,0.05]", "Efectividad de la palanca económica (becas, exoneraciones)."),
    ("Ef academico", 0, "Dmnl [0,1,0.05]", "Efectividad de la palanca académica (monitorías)."),
    ("Ef adaptacion", 0, "Dmnl [0,1,0.05]", "Efectividad de la palanca de adaptación (psicoorientación)."),
    ("Inicio politica", 0, "Semestre [0,40,1]", "Semestre en que empiezan las políticas (0 = desde el inicio)."),
    ("Aplica temprana", 1, "Dmnl [0,1,1]", "1 = la política cubre semestres 1-2."),
    ("Aplica media", 1, "Dmnl [0,1,1]", "1 = la política cubre semestres 3-5."),
    ("Aplica tardia", 1, "Dmnl [0,1,1]", "1 = la política cubre semestres 6-10.")]:
    eq(n, str(v), u, c)
for et, ws in (("temprana", (.3, .3, .4)), ("media", (.3, .5, .2)), ("tardia", (.4, .4, .2))):
    for k, w in zip(("eco", "aca", "ada"), ws): eq(f"Peso {k} {et}", str(w), "Dmnl", "Supuesto de trabajo.")

# ---------------- Vistas ----------------
X = [500, 760, 1020, 1280, 1540]
V1 = dict(name="1 Flujo de estudiantes", pos={}, flows=[], shadows=[])
for k in range(5):
    V1["pos"][f"Sem {k+1}"] = (X[k], 260, 3); V1["pos"][f"Sem {k+6}"] = (X[4-k], 480, 3)
V1["pos"].update({"Graduados": (240, 480, 3), "Rezago": (500, 720, 3)})
f = V1["flows"]
f.append(("Ingreso", None, "Sem 1", 370, 260, (250, 260), None))
for k in range(1, 5): f.append((f"Avance {k}", f"Sem {k}", f"Sem {k+1}", (X[k-1] + X[k]) // 2, 260, None, None))
f.append(("Avance 5", "Sem 5", "Sem 6", X[4], 370, None, None))
for k in range(6, 10): f.append((f"Avance {k}", f"Sem {k}", f"Sem {k+1}", (X[10-k] + X[9-k]) // 2, 480, None, None))
for k in range(1, 6): f.append((f"Desercion {k}", f"Sem {k}", None, X[k-1], 190, None, (X[k-1], 125)))
for k in range(6, 10): f.append((f"Desercion {k}", f"Sem {k}", None, X[10-k], 550, None, (X[10-k], 615)))
f += [("Desercion 10", "Sem 10", None, 500, 410, None, (500, 360)),
      ("Graduacion oportuna", "Sem 10", "Graduados", 370, 480, None, None),
      ("Paso a rezago", "Sem 10", "Rezago", 500, 600, None, None),
      ("Graduacion rezago", "Rezago", "Graduados", 370, 600, None, None),
      ("Desercion rezago", "Rezago", None, 500, 800, None, (500, 870))]
a = {"Avance 10": (430, 545)}
for k in range(1, 6): a[f"Tasa {k}"] = (X[k-1] + 70, 160); a[f"Tasa base {k}"] = (X[k-1] + 70, 105)
for k in range(6, 10): a[f"Tasa {k}"] = (X[10-k] + 70, 590); a[f"Tasa base {k}"] = (X[10-k] + 70, 650)
a.update({"Tasa 10": (590, 375), "Tasa base 10": (565, 330),
          "Ingreso media": (250, 180), "Ingreso de": (330, 150), "Ingreso minimo": (180, 215), "Ingreso maximo": (210, 320),
          "Factor demanda": (330, 340), "Semilla": (100, 90), "Modo estocastico": (110, 140), "CV desercion": (110, 40),
          "Ruido desercion": (260, 40), "Calibracion": (400, 95), "Multiplicador comun": (700, 40),
          "Eficiencia titulacion": (260, 400), "Tasa grad rezago": (250, 700), "Tasa des rezago": (720, 760)})
for n, p in a.items(): V1["pos"][n] = (p[0], p[1], 8)
# sombras colocadas a mano para no cruzar el diagrama
for x in X: V1["shadows"] += [("Multiplicador comun", x + 165, 130)]
for x in X[1:]: V1["shadows"] += [("Multiplicador comun", x + 165, 570)]
V1["shadows"] += [("Multiplicador comun", 730, 355), ("Reduccion tardia", 730, 400), ("Modo estocastico", 150, 360), ("Semilla", 110, 300)]
for k, x in enumerate(X, 1): V1["shadows"] += [(f"Reduccion {etapa(k)}", x + 170, 210)]
for k, x in zip(range(9, 5, -1), X[1:]): V1["shadows"] += [("Reduccion tardia", x + 170, 650)]

V2 = dict(name="2 Bienestar y politicas", pos={
    "Casos pendientes": (500, 300, 3)}, flows=[
    ("Alertas nuevas", None, "Casos pendientes", 330, 300, (210, 300), None),
    ("Casos atendidos", "Casos pendientes", None, 680, 300, None, (800, 300)),
    ("Casos vencidos", "Casos pendientes", None, 500, 400, None, (500, 480))], shadows=[
    ("Sem 1", 230, 200), ("Sem 2", 330, 200)])
for n, p in {"Prob alerta": (210, 380), "Capacidad bienestar": (720, 200), "Fraccion abandono cola": (650, 430),
             "Cobertura bienestar": (860, 400), "Reduccion temprana": (1150, 400), "Reduccion media": (1150, 560), "Reduccion tardia": (1150, 720),
             "Politica activa": (950, 560), "Inicio politica": (950, 640), "Max reduccion": (950, 720),
             "Aplica temprana": (1150, 320), "Aplica media": (1330, 640), "Aplica tardia": (1150, 800),
             "Ef economico": (1450, 450), "Ef academico": (1450, 560), "Ef adaptacion": (1450, 670)}.items():
    V2["pos"][n] = (p[0], p[1], 8)
# pesos: un bloque por etapa a la derecha de cada reducción
for et, y in (("temprana", 400), ("media", 560), ("tardia", 720)):
    for i, k in enumerate(("eco", "aca", "ada")):
        V2["pos"][f"Peso {k} {et}"] = (1300, y - 40 + 40 * i, 8)
V2["pos"]["Aplica media"] = (1150, 480, 8); V2["pos"]["Aplica tardia"] = (1150, 640, 8); V2["pos"]["Aplica temprana"] = (1150, 330, 8)
V2["shadows"] += [("Politica activa", 1030, 450), ("Max reduccion", 1030, 610), ("Politica activa", 1030, 690), ("Max reduccion", 1030, 770)]

V3 = dict(name="3 Indicadores", pos={"Desertores": (900, 260, 3), "Ingresados acum": (330, 660, 3)},
          flows=[("Desercion total", None, "Desertores", 740, 260, (640, 260), None)], shadows=[])
for i in range(1, 11):
    V3["shadows"].append((f"Sem {i}", 90, 40 + 40 * i)); V3["shadows"].append((f"Desercion {i}", 500, 40 + 40 * i))
    V3["shadows"].append((f"Tasa {i}", 1100, 40 + 40 * i))
V3["shadows"] += [("Rezago", 90, 480), ("Desercion rezago", 500, 480), ("Ingreso", 130, 660), ("Graduados", 680, 760),
                  ("Graduacion oportuna", 110, 820), ("Graduacion rezago", 110, 880), ("Eficiencia titulacion", 1320, 400)]
for n, p in {"Matriculados": (300, 260), "Desercion periodo": (700, 420), "Retencion 10": (1300, 260),
             "Desercion cohorte 10": (1500, 200), "Graduacion oportuna pct": (1500, 320), "Graduados periodo": (330, 850),
             "Error conservacion": (680, 660)}.items():
    V3["pos"][n] = (p[0], p[1], 8)
VIEWS = [V1, V2, V3]
ZOOM = "75"

def deps(n):
    e = E[n][0]; out = []
    for m in sorted(E, key=len, reverse=True):
        pat = r"(?<![A-Za-z0-9])" + re.escape(m) + r"(?![A-Za-z0-9])"
        if m != n and re.search(pat, e): e = re.sub(pat, "#", e); out.append(m)
    return out

def build(path):
    L = ["{UTF-8}"]
    for n in sorted(E, key=str.lower):
        e, u, c = E[n]
        if e.startswith("INTEG("):
            flujo, ini = e[6:-1].rsplit(",", 1); L.append(f"{n}= INTEG (\n\t{flujo.strip()},\n\t\t{ini.strip()})")
        else: L.append(f"{n}=\n\t{e}")
        L.append(f"\t~\t{u}\n\t~\t{c}\n\t|\n")
    L += ["********************************************************\n\t.Control\n********************************************************~\n\t\tSimulation Control Parameters\n\t|\n",
          "FINAL TIME  = 40\n\t~\tSemestre\n\t~\tFinal de la simulación (20 años).\n\t|\n",
          "INITIAL TIME  = 0\n\t~\tSemestre\n\t~\tInicio de la simulación.\n\t|\n",
          "SAVEPER  = \n        TIME STEP\n\t~\tSemestre [0,?]\n\t~\tFrecuencia de guardado.\n\t|\n",
          "TIME STEP  = 1\n\t~\tSemestre [0,?]\n\t~\tPaso de integración: un semestre. No cambiar: el avance entre semestres lo supone.\n\t|\n",
          "\\\\\\---/// Sketch information - do not modify anything except names\nV300  Do not put anything below this section - it will be ignored"]
    home = {}  # vista donde está la variable "original"
    for vi, V in enumerate(VIEWS):
        for n in V["pos"]: home.setdefault(n, vi)
        for fl in V["flows"]: home.setdefault(fl[0], vi)
    falt = [n for n in E if n not in home]
    for vi, V in enumerate(VIEWS):
        L.append(f"*{V['name']}")
        L.append("$192-192-192,0,Times New Roman|12||0-0-0|0-0-0|0-0-255|-1--1--1|-1--1--1|96,96," + ZOOM + ",0")
        objs, nid, inst = [], [0], {}   # inst: nombre -> [(id, x, y)]
        def new():
            nid[0] += 1; return nid[0]
        def add_var(n, x, y, shape, shadow=False):
            i = new()
            if shadow: objs.append(f"10,{i},{n},{x},{y},{max(30, 5 * len(n))},11,8,2,0,3,-1,0,0,0,128-128-128,0-0-0,|12||128-128-128")
            elif shape == 3: objs.append(f"10,{i},{n},{x},{y},40,20,3,3,0,0,0,0,0,0")
            else: objs.append(f"10,{i},{n},{x},{y},{max(30, 5 * len(n))},11,8,3,0,0,0,0,0,0")
            inst.setdefault(n, []).append((i, x, y)); return i
        for n, (x, y, s) in V["pos"].items(): add_var(n, x, y, s)
        pipe = set()
        for rate, src, dst, x, y, cs, cd in V["flows"]:
            if cs: sid = new(); objs.append(f"12,{sid},48,{cs[0]},{cs[1]},10,8,0,3,0,0,-1,0,0,0")
            else: sid = inst[src][0][0]
            if cd: did = new(); objs.append(f"12,{did},48,{cd[0]},{cd[1]},10,8,0,3,0,0,-1,0,0,0")
            else: did = inst[dst][0][0]
            p1, p2, v = new(), new(), new()
            dx, dy = (V["pos"][dst][:2] if dst else cd); sx, sy = (V["pos"][src][:2] if src else cs)
            objs.append(f"1,{p1},{v},{did},4,0,0,22,0,0,0,-1--1--1,,1|({dx},{dy})|")
            objs.append(f"1,{p2},{v},{sid},100,0,0,22,0,0,0,-1--1--1,,1|({sx},{sy})|")
            objs.append(f"11,{v},48,{x},{y},6,8,34,3,0,0,1,0,0,0")
            r = new(); vert = sx == dx
            objs.append(f"10,{r},{rate},{x + (50 if vert else 0)},{y + (0 if vert else 18)},{max(30, 5 * len(rate))},11,40,3,0,0,-1,0,0,0")
            inst.setdefault(rate, []).append((r, x, y))
            for s_, d_ in ((src, rate), (rate, dst)): pipe.add((s_, d_))
        for n, x, y in V["shadows"]: add_var(n, x, y, 8, shadow=True)
        originals = list(V["pos"]) + [fl[0] for fl in V["flows"]]
        for n in originals:
            if home.get(n) != vi: continue
            _, nx, ny = inst[n][0]
            for m in deps(n):
                if E[n][0].startswith("INTEG(") and m in [fl[0] for fl in V["flows"]] and ((m, n) in pipe or (n, m) in pipe): continue
                if m not in inst:
                    ang = len(inst) % 8 * math.pi / 4
                    add_var(m, int(nx + 110 * math.cos(ang)), int(ny - 45 + 20 * math.sin(ang)), 8, shadow=True)
                sid, sx, sy = min(inst[m], key=lambda t: (t[1] - nx) ** 2 + (t[2] - ny) ** 2)
                objs.append(f"1,{new()},{sid},{inst[n][0][0]},0,0,0,0,0,64,0,-1--1--1,,1|({(sx + nx) // 2},{(sy + ny) // 2})|")
        L += objs
    L.append("///---\\\\\\\n:L<%^E!@\n9:Current\n15:0,0,0,0,0,0\n19:100,0\n27:0,\n34:0,\n4:Time\n5:Desercion cohorte 10\n24:0\n25:40\n26:40\n")
    open(path, "w", encoding="utf-8", newline="\r\n").write("\n".join(L))
    return falt

if __name__ == "__main__":
    if len(sys.argv) > 2: VIEWS.insert(0, VIEWS.pop(int(sys.argv[2])))  # solo para previsualizar otra vista
    print("Variables sin dibujar:", build(sys.argv[1]))
