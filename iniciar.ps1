# Ejecuta el sistema sin Docker en Windows con un solo comando:
#   powershell -ExecutionPolicy Bypass -File iniciar.ps1
# Crea un entorno virtual (con uv si está instalado; si no, con python -m venv), instala dependencias,
# crea la base de desarrollo si no existe y abre http://localhost:8000
$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\crud"
if (-not (Test-Path ".venv")) {
    if (Get-Command uv -ErrorAction SilentlyContinue) { uv venv .venv --python 3.12 } else { python -m venv .venv }
}
$py = ".\.venv\Scripts\python.exe"
if (Get-Command uv -ErrorAction SilentlyContinue) { uv pip install --python $py -r requirements-dev.txt } else { & $py -m pip install -r requirements-dev.txt }
if (-not (Test-Path "..\db\desercion_dev.db")) { & $py seed.py ..\db\desercion_dev.db }
Start-Process "http://localhost:8000"
& $py -m uvicorn app.main:app --port 8000
