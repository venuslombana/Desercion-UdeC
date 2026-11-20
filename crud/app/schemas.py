from typing import Optional
from pydantic import BaseModel, Field

class UsuarioIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=80)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    rol_id: int
    activo: bool = True

class ProgramaIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=120); sede: str = Field(min_length=3, max_length=60); semestres_plan: int = Field(9, ge=1, le=14)

class PeriodoIn(BaseModel):
    codigo: str = Field(pattern=r"^\d{4}-[12]$"); anio: int = Field(ge=1990, le=2100); semestre: int = Field(ge=1, le=2)

class CohorteIn(BaseModel):
    programa_id: int; periodo_ingreso_id: int

class EstudianteIn(BaseModel):
    codigo_anonimo: str = Field(min_length=6, max_length=16)
    cohorte_id: int
    estrato: int = Field(ge=1, le=6)
    puntaje_saber11: int = Field(ge=0, le=500)
    trabaja: bool = False

class MatriculaIn(BaseModel):
    estudiante_id: int; periodo_id: int
    nivel_semestre: int = Field(ge=1, le=14)
    promedio: float = Field(ge=0, le=5)
    creditos_inscritos: int = Field(ge=0, le=30)
    materias_basicas_perdidas: int = Field(0, ge=0, le=10)
    resultado: str = Field(pattern="^(CONTINUA|DESERTA|GRADUA)$")

class FactorIn(BaseModel):
    tipo: str = Field(pattern="^(economico|academico|adaptacion)$"); nombre: str = Field(min_length=3, max_length=80)

class TipoApoyoIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=80); palanca: str = Field(pattern="^(economico|academico|adaptacion)$"); cupos_por_periodo: int = Field(ge=0, le=1000)

class ApoyoIn(BaseModel):
    estudiante_id: int; tipo_apoyo_id: int; periodo_id: int
    estado: str = Field("asignado", pattern="^(asignado|en_curso|finalizado)$")

class AlertaIn(BaseModel):
    matricula_id: int
    nivel: str = Field(pattern="^(bajo|medio|alto)$")
    motivo: str = Field(min_length=3, max_length=500)
    atendida: bool = False
