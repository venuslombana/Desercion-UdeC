-- Esquema generado desde app/models.py (PostgreSQL)

CREATE TABLE factor_riesgo (
	id SERIAL NOT NULL, 
	tipo VARCHAR(15) NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (tipo IN ('economico','academico','adaptacion')), 
	UNIQUE (nombre)
);


CREATE TABLE parametro (
	clave VARCHAR(40) NOT NULL, 
	valor FLOAT NOT NULL, 
	descripcion VARCHAR(200) NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (clave)
);


CREATE TABLE periodo_academico (
	id SERIAL NOT NULL, 
	codigo VARCHAR(6) NOT NULL, 
	anio INTEGER NOT NULL, 
	semestre INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (semestre IN (1,2)), 
	UNIQUE (codigo)
);


CREATE TABLE programa (
	id SERIAL NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	sede VARCHAR(60) NOT NULL, 
	semestres_plan INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre, sede)
);


CREATE TABLE rol (
	id SERIAL NOT NULL, 
	nombre VARCHAR(30) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);


CREATE TABLE tipo_apoyo (
	id SERIAL NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	palanca VARCHAR(15) NOT NULL, 
	cupos_por_periodo INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (palanca IN ('economico','academico','adaptacion')), 
	UNIQUE (nombre)
);


CREATE TABLE cohorte (
	id SERIAL NOT NULL, 
	programa_id INTEGER NOT NULL, 
	periodo_ingreso_id INTEGER NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	eliminado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (programa_id, periodo_ingreso_id), 
	FOREIGN KEY(programa_id) REFERENCES programa (id), 
	FOREIGN KEY(periodo_ingreso_id) REFERENCES periodo_academico (id)
);


CREATE TABLE usuario (
	id SERIAL NOT NULL, 
	nombre VARCHAR(80) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	rol_id INTEGER NOT NULL, 
	activo BOOLEAN NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	eliminado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	FOREIGN KEY(rol_id) REFERENCES rol (id)
);


CREATE TABLE auditoria (
	id SERIAL NOT NULL, 
	usuario_id INTEGER, 
	entidad VARCHAR(40) NOT NULL, 
	registro_id INTEGER NOT NULL, 
	accion VARCHAR(10) NOT NULL, 
	fecha TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	detalle TEXT, 
	PRIMARY KEY (id), 
	CHECK (accion IN ('CREAR','ACTUALIZAR','ELIMINAR')), 
	FOREIGN KEY(usuario_id) REFERENCES usuario (id)
);

CREATE INDEX ix_auditoria_entidad ON auditoria (entidad, registro_id);

CREATE TABLE estudiante (
	id SERIAL NOT NULL, 
	codigo_anonimo VARCHAR(16) NOT NULL, 
	cohorte_id INTEGER NOT NULL, 
	estrato INTEGER NOT NULL, 
	puntaje_saber11 INTEGER NOT NULL, 
	trabaja BOOLEAN NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	eliminado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CHECK (estrato BETWEEN 1 AND 6), 
	CHECK (puntaje_saber11 BETWEEN 0 AND 500), 
	UNIQUE (codigo_anonimo), 
	FOREIGN KEY(cohorte_id) REFERENCES cohorte (id)
);

CREATE INDEX ix_estudiante_cohorte_id ON estudiante (cohorte_id);

CREATE TABLE apoyo_estudiante (
	id SERIAL NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	tipo_apoyo_id INTEGER NOT NULL, 
	periodo_id INTEGER NOT NULL, 
	estado VARCHAR(12) NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	eliminado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (estudiante_id, tipo_apoyo_id, periodo_id), 
	CHECK (estado IN ('asignado','en_curso','finalizado')), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiante (id), 
	FOREIGN KEY(tipo_apoyo_id) REFERENCES tipo_apoyo (id), 
	FOREIGN KEY(periodo_id) REFERENCES periodo_academico (id)
);

CREATE INDEX ix_apoyo_estudiante_estudiante_id ON apoyo_estudiante (estudiante_id);

CREATE TABLE estudiante_factor (
	estudiante_id INTEGER NOT NULL, 
	factor_id INTEGER NOT NULL, 
	periodo_id INTEGER NOT NULL, 
	intensidad INTEGER NOT NULL, 
	PRIMARY KEY (estudiante_id, factor_id, periodo_id), 
	CHECK (intensidad BETWEEN 1 AND 3), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiante (id), 
	FOREIGN KEY(factor_id) REFERENCES factor_riesgo (id), 
	FOREIGN KEY(periodo_id) REFERENCES periodo_academico (id)
);


CREATE TABLE matricula (
	id SERIAL NOT NULL, 
	estudiante_id INTEGER NOT NULL, 
	periodo_id INTEGER NOT NULL, 
	nivel_semestre INTEGER NOT NULL, 
	promedio FLOAT NOT NULL, 
	creditos_inscritos INTEGER NOT NULL, 
	materias_basicas_perdidas INTEGER NOT NULL, 
	resultado VARCHAR(10) NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	eliminado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (estudiante_id, periodo_id), 
	CHECK (nivel_semestre BETWEEN 1 AND 14), 
	CHECK (promedio BETWEEN 0 AND 5), 
	CHECK (resultado IN ('CONTINUA','DESERTA','GRADUA')), 
	FOREIGN KEY(estudiante_id) REFERENCES estudiante (id), 
	FOREIGN KEY(periodo_id) REFERENCES periodo_academico (id)
);

CREATE INDEX ix_matricula_estudiante_id ON matricula (estudiante_id);
CREATE INDEX ix_matricula_periodo_id ON matricula (periodo_id);

CREATE TABLE alerta (
	id SERIAL NOT NULL, 
	matricula_id INTEGER NOT NULL, 
	nivel VARCHAR(5) NOT NULL, 
	motivo TEXT NOT NULL, 
	atendida BOOLEAN NOT NULL, 
	creado_en TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITHOUT TIME ZONE, 
	eliminado_en TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	CHECK (nivel IN ('bajo','medio','alto')), 
	FOREIGN KEY(matricula_id) REFERENCES matricula (id)
);

CREATE INDEX ix_alerta_matricula_id ON alerta (matricula_id);

