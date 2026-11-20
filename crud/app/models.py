"""Modelo de datos (SQLAlchemy 2.0) del CRUD de seguimiento de la deserción.
Programa: Ingeniería de Sistemas y Computación, UdeC Sede Fusagasugá.
Privacidad (Ley 1581/2012): el estudiante se identifica solo con un código anónimo; no se guardan nombres, documentos ni ubicación."""
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, Float, Boolean, DateTime, Date, Text, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class Trazable:
    """Columnas comunes: marcas de tiempo y eliminación lógica."""
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actualizado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)
    eliminado_en: Mapped[Optional[datetime]] = mapped_column(DateTime)  # eliminación lógica

class Rol(Base):
    __tablename__ = "rol"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True)  # administrador | operador | consulta

class Usuario(Trazable, Base):
    __tablename__ = "usuario"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # hash con sal; nunca texto plano
    rol_id: Mapped[int] = mapped_column(ForeignKey("rol.id"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    rol: Mapped[Rol] = relationship()

class Programa(Base):
    __tablename__ = "programa"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    sede: Mapped[str] = mapped_column(String(60))
    semestres_plan: Mapped[int] = mapped_column(Integer, default=9)
    __table_args__ = (UniqueConstraint("nombre", "sede"),)

class PeriodoAcademico(Base):
    __tablename__ = "periodo_academico"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(6), unique=True)  # 2024-1
    anio: Mapped[int] = mapped_column(Integer)
    semestre: Mapped[int] = mapped_column(Integer)
    __table_args__ = (CheckConstraint("semestre IN (1,2)"),)

class Cohorte(Trazable, Base):
    __tablename__ = "cohorte"
    id: Mapped[int] = mapped_column(primary_key=True)
    programa_id: Mapped[int] = mapped_column(ForeignKey("programa.id"))
    periodo_ingreso_id: Mapped[int] = mapped_column(ForeignKey("periodo_academico.id"))
    __table_args__ = (UniqueConstraint("programa_id", "periodo_ingreso_id"),)

class Estudiante(Trazable, Base):
    __tablename__ = "estudiante"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_anonimo: Mapped[str] = mapped_column(String(16), unique=True)
    cohorte_id: Mapped[int] = mapped_column(ForeignKey("cohorte.id"), index=True)
    estrato: Mapped[int] = mapped_column(Integer)
    puntaje_saber11: Mapped[int] = mapped_column(Integer)
    trabaja: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint("estrato BETWEEN 1 AND 6"), CheckConstraint("puntaje_saber11 BETWEEN 0 AND 500"))

class Matricula(Trazable, Base):
    """Entidad transaccional principal: un registro por estudiante y periodo (fuente de datos para la simulación)."""
    __tablename__ = "matricula"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiante.id"), index=True)
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodo_academico.id"), index=True)
    nivel_semestre: Mapped[int] = mapped_column(Integer)
    promedio: Mapped[float] = mapped_column(Float)
    creditos_inscritos: Mapped[int] = mapped_column(Integer)
    materias_basicas_perdidas: Mapped[int] = mapped_column(Integer, default=0)
    resultado: Mapped[str] = mapped_column(String(10))  # CONTINUA | DESERTA | GRADUA (qué pasó al cerrar el periodo)
    periodo: Mapped[PeriodoAcademico] = relationship()
    __table_args__ = (UniqueConstraint("estudiante_id", "periodo_id"), CheckConstraint("nivel_semestre BETWEEN 1 AND 14"),
                      CheckConstraint("promedio BETWEEN 0 AND 5"), CheckConstraint("resultado IN ('CONTINUA','DESERTA','GRADUA')"))

class FactorRiesgo(Base):
    __tablename__ = "factor_riesgo"
    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(15))  # economico | academico | adaptacion
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    __table_args__ = (CheckConstraint("tipo IN ('economico','academico','adaptacion')"),)

class EstudianteFactor(Base):
    """Relación muchos-a-muchos estudiante–factor de riesgo (por periodo)."""
    __tablename__ = "estudiante_factor"
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiante.id"), primary_key=True)
    factor_id: Mapped[int] = mapped_column(ForeignKey("factor_riesgo.id"), primary_key=True)
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodo_academico.id"), primary_key=True)
    intensidad: Mapped[int] = mapped_column(Integer)  # 1 baja, 2 media, 3 alta
    __table_args__ = (CheckConstraint("intensidad BETWEEN 1 AND 3"),)

class TipoApoyo(Base):
    __tablename__ = "tipo_apoyo"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    palanca: Mapped[str] = mapped_column(String(15))  # economico | academico | adaptacion
    cupos_por_periodo: Mapped[int] = mapped_column(Integer)  # capacidad de Bienestar
    __table_args__ = (CheckConstraint("palanca IN ('economico','academico','adaptacion')"),)

class ApoyoEstudiante(Trazable, Base):
    """Relación muchos-a-muchos estudiante–tipo de apoyo (con atributos)."""
    __tablename__ = "apoyo_estudiante"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiante.id"), index=True)
    tipo_apoyo_id: Mapped[int] = mapped_column(ForeignKey("tipo_apoyo.id"))
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodo_academico.id"))
    estado: Mapped[str] = mapped_column(String(12), default="asignado")
    __table_args__ = (UniqueConstraint("estudiante_id", "tipo_apoyo_id", "periodo_id"),
                      CheckConstraint("estado IN ('asignado','en_curso','finalizado')"))

class Alerta(Trazable, Base):
    __tablename__ = "alerta"
    id: Mapped[int] = mapped_column(primary_key=True)
    matricula_id: Mapped[int] = mapped_column(ForeignKey("matricula.id"), index=True)
    nivel: Mapped[str] = mapped_column(String(5))
    motivo: Mapped[str] = mapped_column(Text)
    atendida: Mapped[bool] = mapped_column(Boolean, default=False)
    matricula: Mapped["Matricula"] = relationship()
    __table_args__ = (CheckConstraint("nivel IN ('bajo','medio','alto')"),)

class Parametro(Base):
    """Parámetros de operación que salen de la simulación (por ejemplo, la capacidad de Bienestar del escenario recomendado)."""
    __tablename__ = "parametro"
    clave: Mapped[str] = mapped_column(String(40), primary_key=True)
    valor: Mapped[float] = mapped_column(Float)
    descripcion: Mapped[str] = mapped_column(String(200))
    actualizado_en: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Auditoria(Base):
    """Quién creó, modificó o eliminó un registro y cuándo."""
    __tablename__ = "auditoria"
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id"))
    entidad: Mapped[str] = mapped_column(String(40))
    registro_id: Mapped[int] = mapped_column(Integer)
    accion: Mapped[str] = mapped_column(String(10))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detalle: Mapped[Optional[str]] = mapped_column(Text)
    __table_args__ = (CheckConstraint("accion IN ('CREAR','ACTUALIZAR','ELIMINAR')"), Index("ix_auditoria_entidad", "entidad", "registro_id"))
