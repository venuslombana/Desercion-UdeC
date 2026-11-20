"""Aplicación FastAPI: API REST, autenticación, cabeceras de seguridad y cliente web.

Arquitectura por capas:
- Presentación: cliente web en app/static (HTML + JavaScript) y documentación OpenAPI en /docs.
- Lógica de negocio: app/negocio.py (reglas puras), app/reportes.py y app/exportacion.py.
- Acceso a datos: app/models.py y app/db.py (SQLAlchemy 2.0; SQLite en desarrollo, PostgreSQL en producción).
"""
import os
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session
from . import schemas as S
from .crud import crud_router
from .db import get_db
from .models import Usuario, Programa, PeriodoAcademico, Cohorte, Estudiante, Matricula, FactorRiesgo, TipoApoyo, ApoyoEstudiante, Alerta, Auditoria
from .relaciones import router as relaciones_router
from .reportes import router as reportes_router, despues_de_crear_alerta
from .security import verify_pw, hash_pw, make_token, current_user, bloqueado, registrar_fallo, limpiar_fallos

VERSION = "1.0.0"
STATIC = os.path.join(os.path.dirname(__file__), "static")

app = FastAPI(title="Seguimiento de la deserción · Ingeniería de Sistemas y Computación, UdeC Fusagasugá", version=VERSION,
              description="API REST del CRUD de seguimiento de la permanencia estudiantil. Autenticación JWT (botón Authorize) "
                          "con tres roles: administrador, operador y consulta. Los datos de la base de desarrollo son sintéticos.")

origenes = [o for o in os.getenv("CORS_ORIGINS", "").split(",") if o]
if origenes:                                           # el cliente web se sirve desde el mismo origen; CORS solo si se configura
    app.add_middleware(CORSMiddleware, allow_origins=origenes, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def cabeceras_seguridad(request: Request, call_next):
    """Cabeceras contra XSS, clickjacking y rastreo de tipo MIME. La CSP no se aplica a /docs porque Swagger usa recursos externos."""
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    if not request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        resp.headers["Content-Security-Policy"] = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                                                   "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000"
    return resp


@app.get("/api/health", tags=["sistema"])
def health():
    return {"estado": "ok", "version": VERSION}


@app.post("/api/auth/login", tags=["auth"])
def login(f: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Inicia sesión. Devuelve un token válido por 60 minutos. Tras 5 intentos fallidos el correo se bloquea 5 minutos."""
    if bloqueado(f.username):
        raise HTTPException(429, "Demasiados intentos fallidos. Espere 5 minutos e intente de nuevo.")
    u = db.scalar(select(Usuario).where(Usuario.email == f.username, Usuario.eliminado_en.is_(None)))
    if not u or not u.activo or not verify_pw(f.password, u.password_hash):
        registrar_fallo(f.username)
        raise HTTPException(401, "Correo o contraseña incorrectos")
    limpiar_fallos(f.username)
    return {"access_token": make_token(u.id, u.rol.nombre), "token_type": "bearer", "rol": u.rol.nombre, "nombre": u.nombre}


@app.get("/api/auth/me", tags=["auth"])
def me(u: Usuario = Depends(current_user)):
    return {"id": u.id, "nombre": u.nombre, "email": u.email, "rol": u.rol.nombre}


A, O, C = "administrador", "operador", "consulta"
TODOS = (A, O, C)


def usuario_tf(d, actual):
    pw = d.pop("password", None)
    if pw:
        d["password_hash"] = hash_pw(pw)
    elif actual is None:
        raise HTTPException(422, [{"campo": "password", "mensaje": "La contraseña es obligatoria al crear un usuario"}])
    else:
        d["password_hash"] = actual.password_hash
    return d


for r in (
    crud_router(Usuario, "usuarios", S.UsuarioIn, (A,), (A,), (A,), search=("nombre", "email"), filters=("rol_id", "activo"), transform=usuario_tf),
    crud_router(Programa, "programas", S.ProgramaIn, TODOS, (A,), (A,), search=("nombre", "sede")),
    crud_router(PeriodoAcademico, "periodos", S.PeriodoIn, TODOS, (A,), (A,), search=("codigo",), filters=("anio", "semestre")),
    crud_router(Cohorte, "cohortes", S.CohorteIn, TODOS, (A,), (A,), filters=("programa_id", "periodo_ingreso_id")),
    crud_router(Estudiante, "estudiantes", S.EstudianteIn, TODOS, (A, O), (A,), search=("codigo_anonimo",), filters=("cohorte_id", "estrato", "trabaja")),
    crud_router(Matricula, "matriculas", S.MatriculaIn, TODOS, (A, O), (A,), filters=("estudiante_id", "periodo_id", "nivel_semestre", "resultado")),
    crud_router(FactorRiesgo, "factores", S.FactorIn, TODOS, (A,), (A,), search=("nombre",), filters=("tipo",)),
    crud_router(TipoApoyo, "tipos-apoyo", S.TipoApoyoIn, TODOS, (A,), (A,), search=("nombre",), filters=("palanca",)),
    crud_router(ApoyoEstudiante, "apoyos", S.ApoyoIn, TODOS, (A, O), (A, O), filters=("estudiante_id", "tipo_apoyo_id", "periodo_id", "estado")),
    crud_router(Alerta, "alertas", S.AlertaIn, TODOS, (A, O), (A,), search=("motivo",), filters=("nivel", "atendida", "matricula_id"),
                after_create=despues_de_crear_alerta),
    crud_router(Auditoria, "auditoria", S.AlertaIn, (A,), (), (), search=("entidad", "detalle"), filters=("entidad", "accion", "usuario_id", "registro_id")),
):
    app.include_router(r)
app.include_router(relaciones_router)
app.include_router(reportes_router)

app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def cliente_web():
    return FileResponse(os.path.join(STATIC, "index.html"))
