"""Prepara una base temporal con los datos sintéticos y una copia de las proyecciones antes de importar la app."""
import os, shutil, sys, tempfile
RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)
_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_dir, 'prueba.db')}"
os.environ["PROYECCIONES_CSV"] = os.path.join(_dir, "proyecciones.csv")
shutil.copy(os.path.join(RAIZ, "data", "proyecciones.csv"), os.environ["PROYECCIONES_CSV"])
import seed  # noqa: E402
seed.main(os.environ["DATABASE_URL"])
