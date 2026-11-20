# Permanencia UdeC: seguimiento y simulación de la deserción estudiantil

Proyecto integrador de nivelación *Modelación, Simulación y Desarrollo CRUD* (CAD612021938), Universidad de Cundinamarca.
Autora: Venus Alejandra Lombana Rueda. Profesor: Daniel Moncada.

El repositorio tiene dos componentes que forman un solo sistema:

| Carpeta | Qué es |
|---|---|
| `crud/` | **Componente A.** Aplicación web (FastAPI + cliente HTML/JS) que registra estudiantes, matrículas, alertas tempranas y apoyos de Bienestar; exporta los históricos para la simulación y muestra el tablero real frente a simulado. |
| `simulacion/` | **Componente B.** Modelo de dinámica de sistemas con componentes aleatorios en Vensim (`desercion_udec.mdl`), datos exportados del CRUD y scripts de ajuste de distribuciones, experimentos, Monte Carlo y modelo financiero. |
| `db/` | Script de creación para PostgreSQL (`schema_postgres.sql`). La base SQLite de desarrollo se crea con `crud/seed.py`. |
| `docs/` | Diagrama entidad-relación, diccionario de datos y matriz de roles y permisos. |
| `docker-compose.yml`, `Caddyfile` | Despliegue con PostgreSQL y HTTPS. |
| `.github/workflows/ci.yml` | Integración continua: pruebas con cobertura, verificación del modelo y construcción de la imagen. |

> Los datos de la base de desarrollo son **sintéticos** (1.382 estudiantes, 8.918 matrículas). No son datos reales de la Universidad.

## Ejecutar con un solo comando

### Opción 1: Docker (PostgreSQL + HTTPS)
Requisito: Docker Desktop.

```bash
cp .env.example .env        # en Windows: copy .env.example .env   (y cambie las claves)
docker compose up --build
```

Abra **https://localhost**. El certificado lo emite Caddy con una autoridad local, por lo que el navegador mostrará una advertencia la primera vez: acéptela (o instale la raíz de Caddy). La primera vez la base se llena sola con los datos sintéticos.

### Opción 2: sin Docker (SQLite)
Requisito: Python 3.11 o superior (o `uv`).

```powershell
powershell -ExecutionPolicy Bypass -File iniciar.ps1     # Windows
./iniciar.sh                                             # Linux / macOS
```

Abra **http://localhost:8000**. La documentación interactiva de la API (OpenAPI/Swagger) está en `/docs`.

### Usuarios de demostración
| Rol | Correo | Qué puede hacer |
|---|---|---|
| Administrador | `admin@demo.edu.co` | Todo, incluidos usuarios, auditoría, parámetros y carga de proyecciones |
| Operador (Bienestar / coordinación) | `operador@demo.edu.co` | Registrar estudiantes, matrículas, alertas y apoyos; atender la cola de Bienestar |
| Consulta | `consulta@demo.edu.co` | Ver listados, tablero y reportes; descargar CSV y PDF |

Clave de desarrollo: `Cambiar-123`. Cámbiela en cualquier uso real.

## Pruebas

```bash
cd crud
pip install -r requirements-dev.txt
python -m pytest -q --cov=app --cov-report=term-missing
```
56 pruebas (unitarias de la lógica de negocio e integración de la API). Cobertura de la capa de negocio: 99 %.

## Cadena completa CRUD → simulación → CRUD

```bash
# 1. Datos del CRUD (o descárguelos desde Reportes > Exportación, que da los mismos archivos)
python crud/seed.py db/desercion_dev.db
python simulacion/scripts/exportar_datos_crud.py db/desercion_dev.db simulacion/datos

# 2. Análisis de entradas, experimentos, Monte Carlo y modelo financiero
pip install -r simulacion/scripts/requirements.txt
python simulacion/scripts/analisis_entradas.py simulacion/datos simulacion/resultados/fig
python simulacion/scripts/run_experimentos.py simulacion/modelo/desercion_udec.mdl simulacion/datos simulacion/resultados
python simulacion/scripts/montecarlo_financiero.py simulacion/modelo/desercion_udec.mdl simulacion/datos simulacion/resultados
python simulacion/scripts/verificar_modelo.py simulacion/modelo/desercion_udec.mdl

# 3. Proyecciones que carga el tablero del CRUD
python simulacion/scripts/exportar_proyecciones.py simulacion/modelo/desercion_udec.mdl crud/data/proyecciones.csv
```
El paso 3 también se puede hacer desde la aplicación: *Parámetros y proyecciones > Cargar proyecciones* (administrador).

El modelo se abre y se corre en **Vensim PLE 10** (`File > Open Model`, `Simulate`). Las instrucciones detalladas están en `simulacion/README.md`.

## Arquitectura

```
Navegador (cliente web responsivo, Chart.js)
        │  HTTPS (Caddy)
        ▼
FastAPI ── presentación: app/static, OpenAPI en /docs
   │       lógica de negocio: app/negocio.py, app/reportes.py, app/exportacion.py
   │       seguridad: app/security.py (PBKDF2 con sal, JWT, roles, bloqueo por intentos)
   ▼
SQLAlchemy 2.0 ── acceso a datos: app/models.py, app/db.py
   ▼
PostgreSQL (producción) / SQLite (desarrollo)
```

## Seguridad
- Contraseñas con PBKDF2-SHA256, 200.000 iteraciones y sal aleatoria por usuario.
- Inyección SQL: todas las consultas usan el ORM o parámetros enlazados. El orden y los filtros solo aceptan columnas conocidas.
- XSS: el cliente inserta todo texto con `textContent`. La política CSP (`default-src 'self'`) bloquea scripts externos y en línea.
- CSRF: el token viaja en la cabecera `Authorization`, no en cookies, así que el navegador nunca lo envía por su cuenta. CORS está cerrado por defecto.
- Secretos por variables de entorno (`SECRET_KEY`, `DATABASE_URL`, `POSTGRES_PASSWORD`); `.env` está en `.gitignore`.
- HTTPS en el despliegue (Caddy), con redirección desde HTTP y cabecera HSTS.
- Bloqueo de 5 minutos tras 5 intentos de ingreso fallidos.
- Privacidad (Ley 1581 de 2012): el estudiante se identifica solo con un código anónimo y la simulación trabaja con totales.

## Uso de inteligencia artificial
Se usó Claude (Anthropic) como apoyo. El detalle de qué se hizo con la herramienta y qué se verificó está en el documento de declaración de uso de IA de la entrega.

## Despliegue en Render (nube, gratis)

El repositorio trae un `render.yaml` (Blueprint) que crea la base PostgreSQL y el servicio web con Docker.

1. Subir este repositorio a GitHub (sin el archivo `.env`).
2. En https://dashboard.render.com: **New → Blueprint**, conectar GitHub, elegir el repositorio y pulsar **Apply**.
3. Esperar a que `permanencia-db` y `permanencia-udec` queden en verde (el primer build tarda unos minutos).
4. Abrir `https://permanencia-udec.onrender.com/api/health` (o la URL que asigne Render) → `{"estado":"ok"}`.
5. Entrar con los usuarios demo (contraseña `Cambiar-123`).

Notas del plan gratuito: el servicio se duerme tras 15 min sin tráfico (el primer acceso tarda ~1 min), el disco no es persistente (los archivos subidos se pierden al reiniciar) y la base gratuita vence a los 30 días.
