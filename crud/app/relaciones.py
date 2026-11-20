"""CRUD de la relación muchos-a-muchos estudiante–factor de riesgo (llave compuesta) y consulta de roles."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .crud import audit, ser
from .db import get_db
from .models import EstudianteFactor, Estudiante, FactorRiesgo, PeriodoAcademico, Rol
from .security import require

A, O, C = "administrador", "operador", "consulta"
router = APIRouter(prefix="/api", tags=["estudiante-factores"])


class EstudianteFactorIn(BaseModel):
    estudiante_id: int = Field(ge=1)
    factor_id: int = Field(ge=1)
    periodo_id: int = Field(ge=1)
    intensidad: int = Field(ge=1, le=3)


class IntensidadIn(BaseModel):
    intensidad: int = Field(ge=1, le=3)


def _clave(e, f, p):
    return e * 10**8 + f * 10**4 + p          # identificador numérico de la fila para la auditoría


def _obtener(db, e, f, p):
    o = db.get(EstudianteFactor, (e, f, p))
    if not o:
        raise HTTPException(404, "La relación estudiante–factor no existe")
    return o


@router.get("/estudiante-factores")
def listar(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), estudiante_id: int | None = None,
           factor_id: int | None = None, periodo_id: int | None = None, intensidad: int | None = None,
           sort: str = Query("estudiante_id", pattern="^(estudiante_id|factor_id|periodo_id|intensidad)$"),
           order: str = Query("asc", pattern="^(asc|desc)$"), db: Session = Depends(get_db), u=Depends(require(A, O, C))):
    stmt = select(EstudianteFactor)
    for col, v in (("estudiante_id", estudiante_id), ("factor_id", factor_id), ("periodo_id", periodo_id), ("intensidad", intensidad)):
        if v is not None:
            stmt = stmt.where(getattr(EstudianteFactor, col) == v)
    c = getattr(EstudianteFactor, sort)
    stmt = stmt.order_by(c.desc() if order == "desc" else c)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    return {"items": [ser(x) for x in db.scalars(stmt.limit(size).offset((page - 1) * size))], "total": total, "page": page, "size": size}


@router.post("/estudiante-factores", status_code=201)
def crear(body: EstudianteFactorIn, db: Session = Depends(get_db), u=Depends(require(A, O))):
    for modelo, i, n in ((Estudiante, body.estudiante_id, "estudiante"), (FactorRiesgo, body.factor_id, "factor"), (PeriodoAcademico, body.periodo_id, "periodo")):
        if not db.get(modelo, i):
            raise HTTPException(409, f"El {n} {i} no existe")
    o = EstudianteFactor(**body.model_dump())
    db.add(o)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ese factor ya está registrado para el estudiante en ese periodo")
    audit(db, u, "estudiante-factores", _clave(body.estudiante_id, body.factor_id, body.periodo_id), "CREAR", body.model_dump())
    db.commit()
    return ser(o)


@router.put("/estudiante-factores/{estudiante_id}/{factor_id}/{periodo_id}")
def actualizar(estudiante_id: int, factor_id: int, periodo_id: int, body: IntensidadIn, db: Session = Depends(get_db), u=Depends(require(A, O))):
    o = _obtener(db, estudiante_id, factor_id, periodo_id)
    o.intensidad = body.intensidad
    audit(db, u, "estudiante-factores", _clave(estudiante_id, factor_id, periodo_id), "ACTUALIZAR", body.model_dump())
    db.commit()
    return ser(o)


@router.delete("/estudiante-factores/{estudiante_id}/{factor_id}/{periodo_id}", status_code=204)
def eliminar(estudiante_id: int, factor_id: int, periodo_id: int, db: Session = Depends(get_db), u=Depends(require(A))):
    """Eliminación física: es una fila de relación sin historia propia; la auditoría conserva el registro."""
    o = _obtener(db, estudiante_id, factor_id, periodo_id)
    detalle = ser(o)
    db.delete(o)
    audit(db, u, "estudiante-factores", _clave(estudiante_id, factor_id, periodo_id), "ELIMINAR", detalle)
    db.commit()


@router.get("/roles", tags=["usuarios"])
def roles(db: Session = Depends(get_db), u=Depends(require(A))):
    """Roles del sistema. Son un catálogo fijo porque los permisos de cada rol están definidos en el código;
    agregar un rol exige una migración y nuevas pruebas, no un formulario."""
    return [{"id": r.id, "nombre": r.nombre} for r in db.scalars(select(Rol).order_by(Rol.id))]
