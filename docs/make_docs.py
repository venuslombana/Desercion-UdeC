import os, sys, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "crud"))
from app.models import Base
out = os.path.dirname(__file__)
# --- ERD (Graphviz)
L = ['digraph{rankdir=LR;graph[fontname="Helvetica",dpi=150,pad=0.2,nodesep=0.35,ranksep=0.9];node[shape=plaintext,fontname="Helvetica",fontsize=10];edge[color="#555555",arrowhead=crow,arrowtail=none,dir=both,arrowtail=tee];']
for t in Base.metadata.sorted_tables:
    rows = "".join(f'<TR><TD ALIGN="LEFT" PORT="{c.name}">{"<B>PK</B> " if c.primary_key else ("<I>FK</I> " if c.foreign_keys else "     ")}{c.name}</TD><TD ALIGN="LEFT"><FONT COLOR="#667788">{str(c.type).split("(")[0].lower()}</FONT></TD></TR>' for c in t.columns)
    L.append(f'{t.name}[label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#0b5d3b"><TR><TD COLSPAN="2" BGCOLOR="#0b5d3b"><FONT COLOR="white"><B>{t.name}</B></FONT></TD></TR>{rows}</TABLE>>];')
for t in Base.metadata.sorted_tables:
    for fk in t.foreign_keys:
        L.append(f'{t.name}:{fk.parent.name} -> {fk.column.table.name}:{fk.column.name}[arrowhead=tee,arrowtail=crow];')
L.append("}")
open(os.path.join(out, "erd.dot"), "w").write("\n".join(L))
subprocess.run(["dot", "-Tpng", os.path.join(out, "erd.dot"), "-o", os.path.join(out, "erd.png")])
# --- Diccionario de datos
M = ["# Diccionario de datos\n"]
for t in Base.metadata.sorted_tables:
    M.append(f"\n## {t.name}\n\n| Columna | Tipo | PK/FK | Nulo | Restricciones |\n|---|---|---|---|---|")
    for c in t.columns:
        k = "PK" if c.primary_key else (f"FK → {list(c.foreign_keys)[0].column.table.name}" if c.foreign_keys else "")
        M.append(f"| {c.name} | {str(c.type).lower()} | {k} | {'sí' if c.nullable else 'no'} | {'único' if c.unique else ''} |")
    cons = [str(x.sqltext) for x in t.constraints if x.__class__.__name__ == "CheckConstraint"] + ["UNIQUE(" + ", ".join(c.name for c in x.columns) + ")" for x in t.constraints if x.__class__.__name__ == "UniqueConstraint"]
    if cons: M.append("\n*Restricciones de tabla:* " + "; ".join(cons))
open(os.path.join(out, "diccionario_datos.md"), "w", encoding="utf-8").write("\n".join(M) + "\n")
