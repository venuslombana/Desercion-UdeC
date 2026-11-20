# Modelo de simulación: deserción y políticas de permanencia

Modelo de dinámica de sistemas con llegadas y tasas aleatorias, construido en Vensim PLE 10.5.2 (`modelo/desercion_udec.mdl`).
El profesor autorizó Vensim en lugar de ProModel. Los scripts de Python leen el mismo `.mdl` con PySD y reproducen todas las cifras del informe.

## Contenido
| Archivo | Para qué sirve |
|---|---|
| `modelo/desercion_udec.mdl` | Modelo de Vensim, con tres vistas: flujo de estudiantes; Bienestar y políticas; indicadores |
| `modelo/desercion_udec.py` | Traducción automática del modelo a Python que hace PySD. **No se ejecuta sola**: es un módulo interno |
| `datos/*.csv` | Las cinco series exportadas del CRUD (`GET /api/exportacion/historicos` o `scripts/exportar_datos_crud.py`) |
| `scripts/analisis_entradas.py` | Ajuste de distribuciones y pruebas de bondad de ajuste (K-S, chi-cuadrado, Shapiro-Wilk) |
| `scripts/run_experimentos.py` | 5 escenarios × 10 réplicas, intervalos de confianza, diferencias pareadas, validación, casos extremos y sensibilidad |
| `scripts/montecarlo_financiero.py` | Monte Carlo de 10.000 iteraciones y modelo financiero (VPN, B/C, TIR, sensibilidad) |
| `scripts/exportar_proyecciones.py` | Proyecciones por periodo de E0, E1 y E3 para el tablero del CRUD |
| `scripts/verificar_modelo.py` | Comprueba las corridas deterministas contra la tabla de verificación (lo usa la integración continua) |
| `scripts/gen_mdl.py` | Genera el `.mdl` desde las ecuaciones (permite revisar el modelo como texto) |
| `resultados/` | Salidas en JSON y figuras |

## 1. Abrir y revisar el modelo en Vensim PLE
1. Instale Vensim PLE 10 (licencia gratuita para uso académico, https://vensim.com).
2. `File > Open Model` → `modelo/desercion_udec.mdl`. Las vistas se cambian con las pestañas de abajo.
3. `Model > Check Model` debe responder que el modelo está bien; `Model > Units Check`: niveles en Estudiantes, flujos en Estudiantes/Semestre, tasas en 1/Semestre.
4. `Model > Settings`: INITIAL TIME 0, FINAL TIME 40, TIME STEP 1, unidad Semestre. **No cambie el TIME STEP**: el avance entre semestres supone que vale 1.

## 2. Corridas deterministas (verificación)
Con `Modo estocastico = 0` no hay números aleatorios y Vensim debe dar exactamente estos valores en t = 40:

| Escenario | Desercion cohorte 10 | Matriculados | Graduados | Desertores | Error conservacion |
|---|---|---|---|---|---|
| E0 | 42,91 | 548,42 | 971,68 | 1.111,89 | 0,00 |
| E1 | 39,50 | 575,98 | 1.030,27 | 1.025,74 | 0,00 |
| E2 | 39,03 | 579,80 | 1.037,60 | 1.014,60 | 0,00 |
| E3 | 32,11 | 613,85 | 1.155,41 | 862,74 | 0,00 |
| E4 | 34,13 | 747,66 | 1.404,65 | 1.137,69 | 0,00 |

Constantes de cada escenario (las demás quedan con su valor por defecto):

| Constante | E0 | E1 | E2 | E3 | E4 |
|---|---|---|---|---|---|
| Ef economico | 0 | 0,3 | 0,3 | 0,6 | 0,6 |
| Ef academico | 0 | 0,6 | 0,6 | 0,6 | 0,6 |
| Ef adaptacion | 0 | 0,6 | 0,6 | 0,6 | 0,6 |
| Aplica media | 1 | 0 | 0 | 1 | 1 |
| Aplica tardia | 1 | 0 | 0 | 1 | 1 |
| Capacidad bienestar | 21,5 | 21,5 | 32 | 32 | 21,5 |
| Factor demanda | 1 | 1 | 1 | 1 | 1,25 |

Para cada fila: escriba el nombre de la corrida en *Run Name*, cambie las constantes (doble clic o SyntheSim), pulse *Simulate* y lea el valor en t = 40 con la herramienta *Table*.
Para demostrar el modelo en vivo, active **SyntheSim**: aparecen deslizadores en las constantes y las gráficas cambian al moverlos.

## 3. Réplicas estocásticas en Vensim
1. `Modo estocastico = 1`.
2. Para cada escenario corra 10 réplicas con `Semilla` de 1 a 10 y un nombre de corrida distinto en cada una (E3_s1 … E3_s10).
3. Promedie cada variable entre los semestres 16 y 40 (los primeros 16 son calentamiento).
4. Con los 10 promedios: media ± t(0,975; 9) × s / √10, con t = 2,262.

Vensim y PySD usan generadores aleatorios distintos: con la misma semilla las trayectorias no coinciden punto a punto, pero las medias de 10 réplicas caen dentro de los intervalos del informe.

## 4. Reproducir todo con Python
Desde la raíz del repositorio:

```bash
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r simulacion/scripts/requirements.txt
python simulacion/scripts/verificar_modelo.py simulacion/modelo/desercion_udec.mdl
python simulacion/scripts/analisis_entradas.py simulacion/datos simulacion/resultados/fig
python simulacion/scripts/run_experimentos.py simulacion/modelo/desercion_udec.mdl simulacion/datos simulacion/resultados
python simulacion/scripts/montecarlo_financiero.py simulacion/modelo/desercion_udec.mdl simulacion/datos simulacion/resultados
python simulacion/scripts/exportar_proyecciones.py simulacion/modelo/desercion_udec.mdl crud/data/proyecciones.csv
```
`run_experimentos.py` tarda unos minutos porque recarga el modelo en cada corrida, para que los parámetros de un escenario no pasen al siguiente.

**Correr una sola réplica** (lo que se pide en la sustentación):
```bash
python -c "import pysd; m=pysd.read_vensim('simulacion/modelo/desercion_udec.mdl'); r=m.run(params={'Modo estocastico':1,'Semilla':3}); print(r[['Matriculados','Desercion cohorte 10']].loc[16:].mean())"
```
