#!/usr/bin/env bash
# Ejecuta el sistema sin Docker en Linux o macOS con un solo comando:  ./iniciar.sh
set -e
cd "$(dirname "$0")/crud"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements-dev.txt
[ -f ../db/desercion_dev.db ] || .venv/bin/python seed.py ../db/desercion_dev.db
echo "Abra http://localhost:8000"
exec .venv/bin/python -m uvicorn app.main:app --port 8000
