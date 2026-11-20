# Roles y permisos (diseño)

| Recurso | administrador | operador (Bienestar / coordinación) | consulta |
|---|---|---|---|
| Usuarios y roles | Crear, consultar, actualizar, eliminar | — | — |
| Programas, periodos, cohortes | CRUD | Consultar | Consultar |
| Estudiantes (anónimos) | CRUD | Crear, consultar, actualizar | Consultar |
| Matrículas | CRUD | Crear, consultar, actualizar | Consultar |
| Factores de riesgo y tipos de apoyo | CRUD | Consultar | Consultar |
| Apoyos a estudiantes | CRUD | CRUD | Consultar |
| Alertas | CRUD | Consultar, actualizar (marcar atendida) | Consultar |
| Reportes y exportación CSV | Sí | Sí | Sí (solo agregados) |
| Auditoría | Consultar | — | — |

Eliminación lógica (`eliminado_en`) en usuario, cohorte, estudiante, matrícula, apoyo y alerta. Toda creación, modificación o eliminación se registra en `auditoria`.
