"""Fábrica de routers CRUD: paginación, búsqueda, filtros y orden en el servidor; validación; eliminación lógica; auditoría."""
import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import ValidationError
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .db import get_db
from .models import Auditoria
from .security import require

def ser(o):
    return {c.name: getattr(o, c.name) for c in o.__table__.columns if c.name != "password_hash"}

def audit(db, user, entidad, rid, accion, detalle=None):
    db.add(Auditoria(usuario_id=user.id, entidad=entidad, registro_id=rid, accion=accion, detalle=json.dumps(detalle, default=str, ensure_ascii=False) if detalle else None))

def crud_router(model, name, In, read, write=(), delete=(), search=(), filters=(), transform=None, after_create=None, desc=""):
    """Crea las cinco operaciones REST de un recurso.
    read/write/delete: roles autorizados. search: columnas para búsqueda de texto. filters: columnas filtrables.
    transform: ajusta los datos antes de guardar. after_create: regla de negocio que se ejecuta después de crear
    (devuelve un dict que se agrega a la respuesta y, si trae «aviso», también la cabecera X-Aviso)."""
    r = APIRouter(prefix=f"/api/{name}", tags=[name]); cols = model.__table__.columns; soft = "eliminado_en" in cols
    def cast(f, v):
        t = cols[f].type.python_type
        try: return (v.lower() in ("1", "true", "si", "sí")) if t is bool else t(v)
        except ValueError: raise HTTPException(422, f"Valor inválido para el filtro «{f}»")
    def get_or_404(db, id):
        o = db.get(model, id)
        if not o or (soft and o.eliminado_en): raise HTTPException(404, f"{name} {id} no existe")
        return o
    def validar(d):
        try: return In(**d).model_dump()
        except ValidationError as e: raise HTTPException(422, [{"campo": ".".join(map(str, x["loc"])), "mensaje": x["msg"]} for x in e.errors()])
    def guardar(db, fn):
        try: fn(); db.flush()
        except IntegrityError as e:
            db.rollback(); raise HTTPException(409, "No se pudo guardar: dato duplicado, relación inexistente o regla de integridad incumplida")

    @r.get("")
    def listar(request: Request, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), q: str | None = None,
               sort: str = "id", order: str = Query("asc", pattern="^(asc|desc)$"), db: Session = Depends(get_db), u=Depends(require(*read))):
        stmt = select(model)
        if soft: stmt = stmt.where(model.eliminado_en.is_(None))
        for f in filters:
            if (v := request.query_params.get(f)) is not None: stmt = stmt.where(cols[f] == cast(f, v))
        if q and search: stmt = stmt.where(or_(*[cols[f].ilike(f"%{q}%") for f in search]))
        if sort not in cols: raise HTTPException(422, f"No se puede ordenar por «{sort}»")
        stmt = stmt.order_by(cols[sort].desc() if order == "desc" else cols[sort])
        total = db.scalar(select(func.count()).select_from(stmt.subquery()))
        return {"items": [ser(x) for x in db.scalars(stmt.limit(size).offset((page - 1) * size))], "total": total, "page": page, "size": size}

    @r.get("/{id}")
    def uno(id: int, db: Session = Depends(get_db), u=Depends(require(*read))): return ser(get_or_404(db, id))

    if write:
        @r.post("", status_code=201)
        def crear(body: In, response: Response, db: Session = Depends(get_db), u=Depends(require(*write))):
            d = body.model_dump()
            if transform: d = transform(d, None)
            o = model(**d); db.add(o); guardar(db, lambda: None)
            audit(db, u, name, o.id, "CREAR", {k: v for k, v in body.model_dump().items() if k != "password"}); db.commit()
            out = ser(o)
            if after_create and (extra := after_create(db, o)):
                out.update(extra)
                if extra.get("aviso"): response.headers["X-Aviso"] = extra["aviso"].encode("ascii", "ignore").decode()
            return out

        @r.put("/{id}")
        def actualizar(id: int, cambios: Dict[str, Any], db: Session = Depends(get_db), u=Depends(require(*write))):
            o = get_or_404(db, id); actual = {k: getattr(o, k) for k in In.model_fields if hasattr(o, k)}
            malos = [k for k in cambios if k not in In.model_fields]
            if malos: raise HTTPException(422, f"Campos no editables: {malos}")
            d = validar({**actual, **cambios})
            if transform: d = transform(d, o)
            guardar(db, lambda: [setattr(o, k, v) for k, v in d.items()])
            audit(db, u, name, id, "ACTUALIZAR", {k: v for k, v in cambios.items() if k != "password"}); db.commit(); return ser(o)

    if delete:
        @r.delete("/{id}", status_code=204)
        def eliminar(id: int, db: Session = Depends(get_db), u=Depends(require(*delete))):
            from datetime import datetime
            o = get_or_404(db, id)
            guardar(db, (lambda: setattr(o, "eliminado_en", datetime.now())) if soft else (lambda: db.delete(o)))
            audit(db, u, name, id, "ELIMINAR", {"logica": soft}); db.commit()
    return r
