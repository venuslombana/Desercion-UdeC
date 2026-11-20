# Diccionario de datos


## factor_riesgo

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| tipo | varchar(15) |  | no |  |
| nombre | varchar(80) |  | no | único |

*Restricciones de tabla:* tipo IN ('economico','academico','adaptacion'); UNIQUE(nombre)

## parametro

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| clave | varchar(40) | PK | no |  |
| valor | float |  | no |  |
| descripcion | varchar(200) |  | no |  |
| actualizado_en | datetime |  | sí |  |

## periodo_academico

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| codigo | varchar(6) |  | no | único |
| anio | integer |  | no |  |
| semestre | integer |  | no |  |

*Restricciones de tabla:* semestre IN (1,2); UNIQUE(codigo)

## programa

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| nombre | varchar(120) |  | no |  |
| sede | varchar(60) |  | no |  |
| semestres_plan | integer |  | no |  |

*Restricciones de tabla:* UNIQUE(nombre, sede)

## rol

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| nombre | varchar(30) |  | no | único |

*Restricciones de tabla:* UNIQUE(nombre)

## tipo_apoyo

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| nombre | varchar(80) |  | no | único |
| palanca | varchar(15) |  | no |  |
| cupos_por_periodo | integer |  | no |  |

*Restricciones de tabla:* palanca IN ('economico','academico','adaptacion'); UNIQUE(nombre)

## cohorte

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| programa_id | integer | FK → programa | no |  |
| periodo_ingreso_id | integer | FK → periodo_academico | no |  |
| creado_en | datetime |  | no |  |
| actualizado_en | datetime |  | sí |  |
| eliminado_en | datetime |  | sí |  |

*Restricciones de tabla:* UNIQUE(programa_id, periodo_ingreso_id)

## usuario

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| nombre | varchar(80) |  | no |  |
| email | varchar(120) |  | no | único |
| password_hash | varchar(255) |  | no |  |
| rol_id | integer | FK → rol | no |  |
| activo | boolean |  | no |  |
| creado_en | datetime |  | no |  |
| actualizado_en | datetime |  | sí |  |
| eliminado_en | datetime |  | sí |  |

*Restricciones de tabla:* UNIQUE(email)

## auditoria

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| usuario_id | integer | FK → usuario | sí |  |
| entidad | varchar(40) |  | no |  |
| registro_id | integer |  | no |  |
| accion | varchar(10) |  | no |  |
| fecha | datetime |  | no |  |
| detalle | text |  | sí |  |

*Restricciones de tabla:* accion IN ('CREAR','ACTUALIZAR','ELIMINAR')

## estudiante

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| codigo_anonimo | varchar(16) |  | no | único |
| cohorte_id | integer | FK → cohorte | no |  |
| estrato | integer |  | no |  |
| puntaje_saber11 | integer |  | no |  |
| trabaja | boolean |  | no |  |
| creado_en | datetime |  | no |  |
| actualizado_en | datetime |  | sí |  |
| eliminado_en | datetime |  | sí |  |

*Restricciones de tabla:* estrato BETWEEN 1 AND 6; puntaje_saber11 BETWEEN 0 AND 500; UNIQUE(codigo_anonimo)

## apoyo_estudiante

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| estudiante_id | integer | FK → estudiante | no |  |
| tipo_apoyo_id | integer | FK → tipo_apoyo | no |  |
| periodo_id | integer | FK → periodo_academico | no |  |
| estado | varchar(12) |  | no |  |
| creado_en | datetime |  | no |  |
| actualizado_en | datetime |  | sí |  |
| eliminado_en | datetime |  | sí |  |

*Restricciones de tabla:* estado IN ('asignado','en_curso','finalizado'); UNIQUE(estudiante_id, tipo_apoyo_id, periodo_id)

## estudiante_factor

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| estudiante_id | integer | PK | no |  |
| factor_id | integer | PK | no |  |
| periodo_id | integer | PK | no |  |
| intensidad | integer |  | no |  |

*Restricciones de tabla:* intensidad BETWEEN 1 AND 3

## matricula

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| estudiante_id | integer | FK → estudiante | no |  |
| periodo_id | integer | FK → periodo_academico | no |  |
| nivel_semestre | integer |  | no |  |
| promedio | float |  | no |  |
| creditos_inscritos | integer |  | no |  |
| materias_basicas_perdidas | integer |  | no |  |
| resultado | varchar(10) |  | no |  |
| creado_en | datetime |  | no |  |
| actualizado_en | datetime |  | sí |  |
| eliminado_en | datetime |  | sí |  |

*Restricciones de tabla:* promedio BETWEEN 0 AND 5; nivel_semestre BETWEEN 1 AND 14; resultado IN ('CONTINUA','DESERTA','GRADUA'); UNIQUE(estudiante_id, periodo_id)

## alerta

| Columna | Tipo | PK/FK | Nulo | Restricciones |
|---|---|---|---|---|
| id | integer | PK | no |  |
| matricula_id | integer | FK → matricula | no |  |
| nivel | varchar(5) |  | no |  |
| motivo | text |  | no |  |
| atendida | boolean |  | no |  |
| creado_en | datetime |  | no |  |
| actualizado_en | datetime |  | sí |  |
| eliminado_en | datetime |  | sí |  |

*Restricciones de tabla:* nivel IN ('bajo','medio','alto')
