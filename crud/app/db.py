"""Acceso a datos: motor y sesión de SQLAlchemy. La URL se lee de DATABASE_URL (secreto por variable de entorno)."""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

_default = "sqlite:///" + os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "db", "desercion_dev.db"))


def normalizar_url(url: str) -> str:
    """Render y Heroku entregan la URL como postgres:// o postgresql://; SQLAlchemy con psycopg 3 necesita postgresql+psycopg://."""
    for prefijo in ("postgres://", "postgresql://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url[len(prefijo):]
    return url


URL = normalizar_url(os.getenv("DATABASE_URL", _default))
engine = create_engine(URL, connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

if URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _fk_on(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")      # SQLite no valida llaves foráneas si no se activa


def get_db():
    with SessionLocal() as s:
        yield s
