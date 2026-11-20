"""Seguridad: contraseñas con PBKDF2-SHA256 y sal aleatoria, tokens JWT, control de acceso por rol y bloqueo
por intentos fallidos. El secreto del JWT se lee de la variable de entorno SECRET_KEY."""
import os, hashlib, hmac, time, jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import Usuario

SECRET = os.getenv("SECRET_KEY", "solo-desarrollo-cambiar-en-produccion")  # secreto por variable de entorno
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
MAX_INTENTOS, BLOQUEO_SEG = 5, 300
_fallidos: dict[str, list[float]] = {}


def bloqueado(email: str) -> bool:
    """True si el correo acumuló MAX_INTENTOS fallidos en los últimos BLOQUEO_SEG segundos (frena la fuerza bruta)."""
    ahora = time.time()
    intentos = [t for t in _fallidos.get(email.lower(), []) if ahora - t < BLOQUEO_SEG]
    _fallidos[email.lower()] = intentos
    return len(intentos) >= MAX_INTENTOS


def registrar_fallo(email: str):
    _fallidos.setdefault(email.lower(), []).append(time.time())


def limpiar_fallos(email: str):
    _fallidos.pop(email.lower(), None)

def hash_pw(pw, salt=None):
    salt = salt or os.urandom(16)
    return "pbkdf2$" + salt.hex() + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000).hex()

def verify_pw(pw, stored):
    try: _, salt, h = stored.split("$")
    except ValueError: return False
    return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex(), h)

def make_token(uid, rol, minutes=60):
    return jwt.encode({"sub": str(uid), "rol": rol, "exp": int(time.time()) + minutes * 60}, SECRET, "HS256")

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)):
    try: data = jwt.decode(token, SECRET, ["HS256"])
    except jwt.PyJWTError: raise HTTPException(401, "Token inválido o vencido")
    u = db.get(Usuario, int(data["sub"]))
    if not u or not u.activo or u.eliminado_en: raise HTTPException(401, "Usuario inactivo")
    return u

def require(*roles):
    def dep(u: Usuario = Depends(current_user)):
        if u.rol.nombre not in roles: raise HTTPException(403, f"El rol «{u.rol.nombre}» no tiene permiso para esta acción")
        return u
    return dep
