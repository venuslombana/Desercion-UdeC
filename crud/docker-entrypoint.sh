#!/bin/sh
# Espera la base de datos, la llena con los datos sintéticos si está vacía y arranca la API.
set -e
python - <<'PY'
import os, time
from sqlalchemy import create_engine, inspect, text
from app.db import normalizar_url
url = normalizar_url(os.environ["DATABASE_URL"])
for intento in range(30):
    try:
        eng = create_engine(url); eng.connect().close(); break
    except Exception as e:
        print("Esperando la base de datos...", e.__class__.__name__); time.sleep(2)
else:
    raise SystemExit("La base de datos no respondió")
vacia = "usuario" not in inspect(eng).get_table_names()
if not vacia:
    with eng.connect() as c: vacia = c.execute(text("SELECT COUNT(*) FROM usuario")).scalar() == 0
if vacia and os.getenv("SEED_ON_START", "1") == "1":
    import seed; seed.main(url)
PY
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers --forwarded-allow-ips="*"
