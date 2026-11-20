"""
Python model 'desercion_udec.py'
Translated using PySD
"""

from pathlib import Path
import numpy as np
from scipy import stats

from pysd.py_backend.functions import if_then_else, xidz, zidz
from pysd.py_backend.statefuls import Integ
from pysd import Component

__pysd_version__ = "3.14.3"

__data = {"scope": None, "time": lambda: 0}

_root = Path(__file__).parent


component = Component()

#######################################################################
#                          CONTROL VARIABLES                          #
#######################################################################

_control_vars = {
    "initial_time": lambda: 0,
    "final_time": lambda: 40,
    "time_step": lambda: 1,
    "saveper": lambda: time_step(),
}


def _init_outer_references(data):
    for key in data:
        __data[key] = data[key]


@component.add(name="Time")
def time():
    """
    Current time of the model.
    """
    return __data["time"]()


@component.add(
    name="FINAL TIME", units="Semestre", comp_type="Constant", comp_subtype="Normal"
)
def final_time():
    """
    Final de la simulación (20 años).
    """
    return __data["time"].final_time()


@component.add(
    name="INITIAL TIME", units="Semestre", comp_type="Constant", comp_subtype="Normal"
)
def initial_time():
    """
    Inicio de la simulación.
    """
    return __data["time"].initial_time()


@component.add(
    name="SAVEPER",
    units="Semestre",
    limits=(0.0, np.nan),
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time_step": 1},
)
def saveper():
    """
    Frecuencia de guardado.
    """
    return __data["time"].saveper()


@component.add(
    name="TIME STEP",
    units="Semestre",
    limits=(0.0, np.nan),
    comp_type="Constant",
    comp_subtype="Normal",
)
def time_step():
    """
    Paso de integración: un semestre. No cambiar: el avance entre semestres lo supone.
    """
    return __data["time"].time_step()


#######################################################################
#                           MODEL VARIABLES                           #
#######################################################################


@component.add(
    name="Alertas nuevas",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_1": 1, "sem_2": 1, "prob_alerta": 1},
)
def alertas_nuevas():
    """
    Alertas tempranas generadas en los semestres 1 y 2.
    """
    return (sem_1() + sem_2()) * prob_alerta()


@component.add(
    name="Aplica media",
    units="Dmnl",
    limits=(0.0, 1.0, 1.0),
    comp_type="Constant",
    comp_subtype="Normal",
)
def aplica_media():
    """
    1 = la política cubre semestres 3-5.
    """
    return 1


@component.add(
    name="Aplica tardia",
    units="Dmnl",
    limits=(0.0, 1.0, 1.0),
    comp_type="Constant",
    comp_subtype="Normal",
)
def aplica_tardia():
    """
    1 = la política cubre semestres 6-10.
    """
    return 1


@component.add(
    name="Aplica temprana",
    units="Dmnl",
    limits=(0.0, 1.0, 1.0),
    comp_type="Constant",
    comp_subtype="Normal",
)
def aplica_temprana():
    """
    1 = la política cubre semestres 1-2.
    """
    return 1


@component.add(
    name="Avance 1",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_1": 1, "time_step": 1, "desercion_1": 1},
)
def avance_1():
    """
    Estudiantes que pasan del semestre 1 al 2. Requiere TIME STEP = 1 semestre.
    """
    return sem_1() / time_step() - desercion_1()


@component.add(
    name="Avance 10",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_10": 1, "time_step": 1, "desercion_10": 1},
)
def avance_10():
    """
    Estudiantes que terminan el semestre 10.
    """
    return sem_10() / time_step() - desercion_10()


@component.add(
    name="Avance 2",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_2": 1, "time_step": 1, "desercion_2": 1},
)
def avance_2():
    """
    Estudiantes que pasan del semestre 2 al 3. Requiere TIME STEP = 1 semestre.
    """
    return sem_2() / time_step() - desercion_2()


@component.add(
    name="Avance 3",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_3": 1, "time_step": 1, "desercion_3": 1},
)
def avance_3():
    """
    Estudiantes que pasan del semestre 3 al 4. Requiere TIME STEP = 1 semestre.
    """
    return sem_3() / time_step() - desercion_3()


@component.add(
    name="Avance 4",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_4": 1, "time_step": 1, "desercion_4": 1},
)
def avance_4():
    """
    Estudiantes que pasan del semestre 4 al 5. Requiere TIME STEP = 1 semestre.
    """
    return sem_4() / time_step() - desercion_4()


@component.add(
    name="Avance 5",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_5": 1, "time_step": 1, "desercion_5": 1},
)
def avance_5():
    """
    Estudiantes que pasan del semestre 5 al 6. Requiere TIME STEP = 1 semestre.
    """
    return sem_5() / time_step() - desercion_5()


@component.add(
    name="Avance 6",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_6": 1, "time_step": 1, "desercion_6": 1},
)
def avance_6():
    """
    Estudiantes que pasan del semestre 6 al 7. Requiere TIME STEP = 1 semestre.
    """
    return sem_6() / time_step() - desercion_6()


@component.add(
    name="Avance 7",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_7": 1, "time_step": 1, "desercion_7": 1},
)
def avance_7():
    """
    Estudiantes que pasan del semestre 7 al 8. Requiere TIME STEP = 1 semestre.
    """
    return sem_7() / time_step() - desercion_7()


@component.add(
    name="Avance 8",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_8": 1, "time_step": 1, "desercion_8": 1},
)
def avance_8():
    """
    Estudiantes que pasan del semestre 8 al 9. Requiere TIME STEP = 1 semestre.
    """
    return sem_8() / time_step() - desercion_8()


@component.add(
    name="Avance 9",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_9": 1, "time_step": 1, "desercion_9": 1},
)
def avance_9():
    """
    Estudiantes que pasan del semestre 9 al 10. Requiere TIME STEP = 1 semestre.
    """
    return sem_9() / time_step() - desercion_9()


@component.add(
    name="Calibracion",
    units="Dmnl",
    limits=(0.3, 1.5, 0.005),
    comp_type="Constant",
    comp_subtype="Normal",
)
def calibracion():
    """
    Mínimos cuadrados ponderados de las tasas observadas en el CRUD frente al perfil SPADIES.
    """
    return 0.715


@component.add(
    name="Capacidad bienestar",
    units="Estudiantes/Semestre",
    limits=(0.0, 80.0, 0.5),
    comp_type="Constant",
    comp_subtype="Normal",
)
def capacidad_bienestar():
    """
    Casos que Bienestar atiende por semestre (CRUD: 21,6 apoyos por periodo).
    """
    return 21.5


@component.add(
    name="Casos atendidos",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"casos_pendientes": 1, "time_step": 1, "capacidad_bienestar": 1},
)
def casos_atendidos():
    """
    Casos que Bienestar alcanza a atender (recurso limitado).
    """
    return float(np.minimum(casos_pendientes() / time_step(), capacidad_bienestar()))


@component.add(
    name="Casos pendientes",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_casos_pendientes": 1},
    other_deps={
        "_integ_casos_pendientes": {
            "initial": {},
            "step": {"alertas_nuevas": 1, "casos_atendidos": 1, "casos_vencidos": 1},
        }
    },
)
def casos_pendientes():
    """
    Cola de casos con alerta temprana que esperan atención de Bienestar.
    """
    return _integ_casos_pendientes()


_integ_casos_pendientes = Integ(
    lambda: alertas_nuevas() - casos_atendidos() - casos_vencidos(),
    lambda: 0,
    "_integ_casos_pendientes",
)


@component.add(
    name="Casos vencidos",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "casos_pendientes": 1,
        "time_step": 1,
        "casos_atendidos": 1,
        "fraccion_abandono_cola": 1,
    },
)
def casos_vencidos():
    """
    Casos no atendidos que salen de la cola.
    """
    return (
        casos_pendientes() / time_step() - casos_atendidos()
    ) * fraccion_abandono_cola()


@component.add(
    name="Cobertura bienestar",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"casos_atendidos": 1, "time_step": 1, "casos_pendientes": 1},
)
def cobertura_bienestar():
    """
    Fracción de la cola que recibe atención en el semestre.
    """
    return float(
        np.minimum(1, xidz(casos_atendidos(), casos_pendientes() / time_step(), 1))
    )


@component.add(
    name="CV desercion",
    units="Dmnl",
    limits=(0.0, 0.5, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def cv_desercion():
    """
    Coeficiente de variación de las tasas entre periodos.
    """
    return 0.236


@component.add(
    name="Desercion 1",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_1": 1, "tasa_1": 1},
)
def desercion_1():
    """
    Estudiantes que abandonan en el semestre 1.
    """
    return sem_1() * tasa_1()


@component.add(
    name="Desercion 10",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_10": 1, "tasa_10": 1},
)
def desercion_10():
    """
    Estudiantes que abandonan en el semestre 10.
    """
    return sem_10() * tasa_10()


@component.add(
    name="Desercion 2",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_2": 1, "tasa_2": 1},
)
def desercion_2():
    """
    Estudiantes que abandonan en el semestre 2.
    """
    return sem_2() * tasa_2()


@component.add(
    name="Desercion 3",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_3": 1, "tasa_3": 1},
)
def desercion_3():
    """
    Estudiantes que abandonan en el semestre 3.
    """
    return sem_3() * tasa_3()


@component.add(
    name="Desercion 4",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_4": 1, "tasa_4": 1},
)
def desercion_4():
    """
    Estudiantes que abandonan en el semestre 4.
    """
    return sem_4() * tasa_4()


@component.add(
    name="Desercion 5",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_5": 1, "tasa_5": 1},
)
def desercion_5():
    """
    Estudiantes que abandonan en el semestre 5.
    """
    return sem_5() * tasa_5()


@component.add(
    name="Desercion 6",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_6": 1, "tasa_6": 1},
)
def desercion_6():
    """
    Estudiantes que abandonan en el semestre 6.
    """
    return sem_6() * tasa_6()


@component.add(
    name="Desercion 7",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_7": 1, "tasa_7": 1},
)
def desercion_7():
    """
    Estudiantes que abandonan en el semestre 7.
    """
    return sem_7() * tasa_7()


@component.add(
    name="Desercion 8",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_8": 1, "tasa_8": 1},
)
def desercion_8():
    """
    Estudiantes que abandonan en el semestre 8.
    """
    return sem_8() * tasa_8()


@component.add(
    name="Desercion 9",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"sem_9": 1, "tasa_9": 1},
)
def desercion_9():
    """
    Estudiantes que abandonan en el semestre 9.
    """
    return sem_9() * tasa_9()


@component.add(
    name="Desercion cohorte 10",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"retencion_10": 1},
)
def desercion_cohorte_10():
    """
    Deserción acumulada de cohorte a 10 semestres, en porcentaje.
    """
    return 100 * (1 - retencion_10())


@component.add(
    name="Desercion periodo",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"desercion_total": 1, "time_step": 1, "matriculados": 1},
)
def desercion_periodo():
    """
    Tasa de deserción por periodo (indicador SPADIES).
    """
    return zidz(desercion_total() * time_step(), matriculados())


@component.add(
    name="Desercion rezago",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"rezago": 1, "tasa_des_rezago": 1},
)
def desercion_rezago():
    return rezago() * tasa_des_rezago()


@component.add(
    name="Desercion total",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "desercion_1": 1,
        "desercion_2": 1,
        "desercion_3": 1,
        "desercion_4": 1,
        "desercion_5": 1,
        "desercion_6": 1,
        "desercion_7": 1,
        "desercion_8": 1,
        "desercion_9": 1,
        "desercion_10": 1,
        "desercion_rezago": 1,
    },
)
def desercion_total():
    """
    Todas las salidas por deserción del semestre.
    """
    return (
        desercion_1()
        + desercion_2()
        + desercion_3()
        + desercion_4()
        + desercion_5()
        + desercion_6()
        + desercion_7()
        + desercion_8()
        + desercion_9()
        + desercion_10()
        + desercion_rezago()
    )


@component.add(
    name="Desertores",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_desertores": 1},
    other_deps={"_integ_desertores": {"initial": {}, "step": {"desercion_total": 1}}},
)
def desertores():
    """
    Contador de desertores acumulados.
    """
    return _integ_desertores()


_integ_desertores = Integ(lambda: desercion_total(), lambda: 0, "_integ_desertores")


@component.add(
    name="Ef academico",
    units="Dmnl",
    limits=(0.0, 1.0, 0.05),
    comp_type="Constant",
    comp_subtype="Normal",
)
def ef_academico():
    """
    Efectividad de la palanca académica (monitorías).
    """
    return 0


@component.add(
    name="Ef adaptacion",
    units="Dmnl",
    limits=(0.0, 1.0, 0.05),
    comp_type="Constant",
    comp_subtype="Normal",
)
def ef_adaptacion():
    """
    Efectividad de la palanca de adaptación (psicoorientación).
    """
    return 0


@component.add(
    name="Ef economico",
    units="Dmnl",
    limits=(0.0, 1.0, 0.05),
    comp_type="Constant",
    comp_subtype="Normal",
)
def ef_economico():
    """
    Efectividad de la palanca económica (becas, exoneraciones).
    """
    return 0


@component.add(
    name="Eficiencia titulacion",
    units="Dmnl",
    limits=(0.3, 1.0, 0.01),
    comp_type="Constant",
    comp_subtype="Normal",
)
def eficiencia_titulacion():
    """
    Fracción que se gradúa al terminar el semestre 10 (CRUD: 0,664).
    """
    return 0.66


@component.add(
    name="Error conservacion",
    units="Estudiantes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "ingresados_acum": 1,
        "desertores": 1,
        "matriculados": 1,
        "graduados": 1,
    },
)
def error_conservacion():
    """
    Debe valer 0 en todo instante.
    """
    return ingresados_acum() - (matriculados() + graduados() + desertores())


@component.add(
    name="Factor demanda",
    units="Dmnl",
    limits=(0.5, 1.5, 0.05),
    comp_type="Constant",
    comp_subtype="Normal",
)
def factor_demanda():
    """
    1 = demanda actual; 1,25 = escenario de aumento de demanda.
    """
    return 1


@component.add(
    name="Fraccion abandono cola",
    units="Dmnl",
    limits=(0.0, 1.0, 0.05),
    comp_type="Constant",
    comp_subtype="Normal",
)
def fraccion_abandono_cola():
    """
    Supuesto: la mitad de los casos no atendidos sale de la cola cada semestre.
    """
    return 0.5


@component.add(
    name="Graduacion oportuna",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"avance_10": 1, "eficiencia_titulacion": 1},
)
def graduacion_oportuna():
    return avance_10() * eficiencia_titulacion()


@component.add(
    name="Graduacion oportuna pct",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"retencion_10": 1, "eficiencia_titulacion": 1},
)
def graduacion_oportuna_pct():
    """
    Graduación oportuna de cohorte, en porcentaje.
    """
    return 100 * retencion_10() * eficiencia_titulacion()


@component.add(
    name="Graduacion rezago",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"rezago": 1, "tasa_grad_rezago": 1},
)
def graduacion_rezago():
    return rezago() * tasa_grad_rezago()


@component.add(
    name="Graduados",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_graduados": 1},
    other_deps={
        "_integ_graduados": {
            "initial": {},
            "step": {"graduacion_oportuna": 1, "graduacion_rezago": 1},
        }
    },
)
def graduados():
    """
    Graduados acumulados.
    """
    return _integ_graduados()


_integ_graduados = Integ(
    lambda: graduacion_oportuna() + graduacion_rezago(), lambda: 0, "_integ_graduados"
)


@component.add(
    name="Graduados periodo",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"graduacion_oportuna": 1, "graduacion_rezago": 1},
)
def graduados_periodo():
    return graduacion_oportuna() + graduacion_rezago()


@component.add(
    name="Ingresados acum",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_ingresados_acum": 1},
    other_deps={"_integ_ingresados_acum": {"initial": {}, "step": {"ingreso": 1}}},
)
def ingresados_acum():
    """
    Contador de ingresos; se usa para verificar la conservación.
    """
    return _integ_ingresados_acum()


_integ_ingresados_acum = Integ(lambda: ingreso(), lambda: 0, "_integ_ingresados_acum")


@component.add(
    name="Ingreso",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "modo_estocastico": 1,
        "ingreso_minimo": 1,
        "time": 1,
        "ingreso_de": 1,
        "semilla": 1,
        "ingreso_maximo": 1,
        "ingreso_media": 2,
        "factor_demanda": 1,
    },
)
def ingreso():
    """
    Llegadas por semestre: Normal(65,8; 6,5) truncada en [50, 80], ajustada con las 21 cohortes exportadas del CRUD.
    """
    return (
        if_then_else(
            modo_estocastico() == 1,
            lambda: float(
                stats.truncnorm.rvs(
                    xidz(ingreso_minimo() - ingreso_media(), ingreso_de(), -np.inf),
                    xidz(ingreso_maximo() - ingreso_media(), ingreso_de(), np.inf),
                    loc=ingreso_media(),
                    scale=ingreso_de(),
                    size=(),
                )
            ),
            lambda: ingreso_media(),
        )
        * factor_demanda()
    )


@component.add(
    name="Ingreso de",
    units="Estudiantes/Semestre",
    limits=(0.0, 15.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def ingreso_de():
    """
    Desviación estándar ajustada con el CRUD.
    """
    return 6.5


@component.add(
    name="Ingreso maximo",
    units="Estudiantes/Semestre",
    comp_type="Constant",
    comp_subtype="Normal",
)
def ingreso_maximo():
    """
    Truncamiento superior.
    """
    return 80


@component.add(
    name="Ingreso media",
    units="Estudiantes/Semestre",
    limits=(50.0, 80.0, 0.1),
    comp_type="Constant",
    comp_subtype="Normal",
)
def ingreso_media():
    """
    Media ajustada con el CRUD.
    """
    return 65.8


@component.add(
    name="Ingreso minimo",
    units="Estudiantes/Semestre",
    comp_type="Constant",
    comp_subtype="Normal",
)
def ingreso_minimo():
    """
    Truncamiento inferior.
    """
    return 50


@component.add(
    name="Inicio politica",
    units="Semestre",
    limits=(0.0, 40.0, 1.0),
    comp_type="Constant",
    comp_subtype="Normal",
)
def inicio_politica():
    """
    Semestre en que empiezan las políticas (0 = desde el inicio).
    """
    return 0


@component.add(
    name="Matriculados",
    units="Estudiantes",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "sem_1": 1,
        "sem_2": 1,
        "sem_3": 1,
        "sem_4": 1,
        "sem_5": 1,
        "sem_6": 1,
        "sem_7": 1,
        "sem_8": 1,
        "sem_9": 1,
        "sem_10": 1,
        "rezago": 1,
    },
)
def matriculados():
    return (
        sem_1()
        + sem_2()
        + sem_3()
        + sem_4()
        + sem_5()
        + sem_6()
        + sem_7()
        + sem_8()
        + sem_9()
        + sem_10()
        + rezago()
    )


@component.add(
    name="Max reduccion",
    units="Dmnl",
    limits=(0.0, 1.0, 0.05),
    comp_type="Constant",
    comp_subtype="Normal",
)
def max_reduccion():
    """
    Supuesto: reducción máxima de una tasa con política 100 % efectiva.
    """
    return 0.5


@component.add(
    name="Modo estocastico",
    units="Dmnl",
    limits=(0.0, 1.0, 1.0),
    comp_type="Constant",
    comp_subtype="Normal",
)
def modo_estocastico():
    """
    1 = llegadas y tasas aleatorias; 0 = corrida determinista.
    """
    return 1


@component.add(
    name="Multiplicador comun",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"calibracion": 1, "ruido_desercion": 1},
)
def multiplicador_comun():
    """
    Calibración institucional por choque aleatorio del periodo.
    """
    return calibracion() * ruido_desercion()


@component.add(
    name="Paso a rezago",
    units="Estudiantes/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"avance_10": 1, "eficiencia_titulacion": 1},
)
def paso_a_rezago():
    return avance_10() * (1 - eficiencia_titulacion())


@component.add(
    name="Peso aca media", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_aca_media():
    """
    Supuesto de trabajo.
    """
    return 0.5


@component.add(
    name="Peso aca tardia", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_aca_tardia():
    """
    Supuesto de trabajo.
    """
    return 0.4


@component.add(
    name="Peso aca temprana", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_aca_temprana():
    """
    Supuesto de trabajo.
    """
    return 0.3


@component.add(
    name="Peso ada media", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_ada_media():
    """
    Supuesto de trabajo.
    """
    return 0.2


@component.add(
    name="Peso ada tardia", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_ada_tardia():
    """
    Supuesto de trabajo.
    """
    return 0.2


@component.add(
    name="Peso ada temprana", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_ada_temprana():
    """
    Supuesto de trabajo.
    """
    return 0.4


@component.add(
    name="Peso eco media", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_eco_media():
    """
    Supuesto de trabajo.
    """
    return 0.3


@component.add(
    name="Peso eco tardia", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_eco_tardia():
    """
    Supuesto de trabajo.
    """
    return 0.4


@component.add(
    name="Peso eco temprana", units="Dmnl", comp_type="Constant", comp_subtype="Normal"
)
def peso_eco_temprana():
    """
    Supuesto de trabajo.
    """
    return 0.3


@component.add(
    name="Politica activa",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"time": 1, "inicio_politica": 1},
)
def politica_activa():
    """
    Vale 1 desde el semestre en que arrancan las políticas.
    """
    return if_then_else(time() >= inicio_politica(), lambda: 1, lambda: 0)


@component.add(
    name="Prob alerta", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def prob_alerta():
    """
    Alertas por estudiante de semestres 1-2 en cada periodo (CRUD: 0,185).
    """
    return 0.185


@component.add(
    name="Reduccion media",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "politica_activa": 1,
        "aplica_media": 1,
        "max_reduccion": 1,
        "ef_adaptacion": 1,
        "peso_ada_media": 1,
        "ef_economico": 1,
        "ef_academico": 1,
        "peso_aca_media": 1,
        "peso_eco_media": 1,
    },
)
def reduccion_media():
    """
    Reducción en semestres 3-5.
    """
    return (
        politica_activa()
        * aplica_media()
        * max_reduccion()
        * (
            peso_eco_media() * ef_economico()
            + peso_aca_media() * ef_academico()
            + peso_ada_media() * ef_adaptacion()
        )
    )


@component.add(
    name="Reduccion tardia",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "politica_activa": 1,
        "aplica_tardia": 1,
        "max_reduccion": 1,
        "ef_adaptacion": 1,
        "ef_economico": 1,
        "peso_ada_tardia": 1,
        "peso_eco_tardia": 1,
        "peso_aca_tardia": 1,
        "ef_academico": 1,
    },
)
def reduccion_tardia():
    """
    Reducción en semestres 6-10.
    """
    return (
        politica_activa()
        * aplica_tardia()
        * max_reduccion()
        * (
            peso_eco_tardia() * ef_economico()
            + peso_aca_tardia() * ef_academico()
            + peso_ada_tardia() * ef_adaptacion()
        )
    )


@component.add(
    name="Reduccion temprana",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "politica_activa": 1,
        "aplica_temprana": 1,
        "max_reduccion": 1,
        "cobertura_bienestar": 1,
        "ef_adaptacion": 1,
        "ef_economico": 1,
        "peso_eco_temprana": 1,
        "ef_academico": 1,
        "peso_aca_temprana": 1,
        "peso_ada_temprana": 1,
    },
)
def reduccion_temprana():
    """
    Reducción de la tasa en semestres 1-2. Se multiplica por la cobertura porque la ruta de apoyo empieza con la alerta temprana.
    """
    return (
        politica_activa()
        * aplica_temprana()
        * max_reduccion()
        * cobertura_bienestar()
        * (
            peso_eco_temprana() * ef_economico()
            + peso_aca_temprana() * ef_academico()
            + peso_ada_temprana() * ef_adaptacion()
        )
    )


@component.add(
    name="Retencion 10",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={
        "tasa_1": 1,
        "time_step": 10,
        "tasa_2": 1,
        "tasa_3": 1,
        "tasa_4": 1,
        "tasa_5": 1,
        "tasa_6": 1,
        "tasa_7": 1,
        "tasa_8": 1,
        "tasa_9": 1,
        "tasa_10": 1,
    },
)
def retencion_10():
    """
    Fracción de una cohorte que termina el semestre 10 con las tasas vigentes.
    """
    return (
        (1 - tasa_1() * time_step())
        * (1 - tasa_2() * time_step())
        * (1 - tasa_3() * time_step())
        * (1 - tasa_4() * time_step())
        * (1 - tasa_5() * time_step())
        * (1 - tasa_6() * time_step())
        * (1 - tasa_7() * time_step())
        * (1 - tasa_8() * time_step())
        * (1 - tasa_9() * time_step())
        * (1 - tasa_10() * time_step())
    )


@component.add(
    name="Rezago",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_rezago": 1},
    other_deps={
        "_integ_rezago": {
            "initial": {},
            "step": {"paso_a_rezago": 1, "graduacion_rezago": 1, "desercion_rezago": 1},
        }
    },
)
def rezago():
    """
    Estudiantes que terminaron el semestre 10 sin graduarse.
    """
    return _integ_rezago()


_integ_rezago = Integ(
    lambda: paso_a_rezago() - graduacion_rezago() - desercion_rezago(),
    lambda: 0,
    "_integ_rezago",
)


@component.add(
    name="Ruido desercion",
    units="Dmnl",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"modo_estocastico": 1, "cv_desercion": 1, "time": 1, "semilla": 1},
)
def ruido_desercion():
    """
    Variación de las tasas entre periodos. CV = 0,236, estimado con la deserción de primer semestre de 21 cohortes del CRUD.
    """
    return if_then_else(
        modo_estocastico() == 1,
        lambda: float(
            stats.truncnorm.rvs(
                xidz(0.4 - 1, cv_desercion(), -np.inf),
                xidz(1.6 - 1, cv_desercion(), np.inf),
                loc=1,
                scale=cv_desercion(),
                size=(),
            )
        ),
        lambda: 1,
    )


@component.add(
    name="Sem 1",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_1": 1},
    other_deps={
        "_integ_sem_1": {
            "initial": {},
            "step": {"ingreso": 1, "avance_1": 1, "desercion_1": 1},
        }
    },
)
def sem_1():
    """
    Estudiantes matriculados en primer semestre.
    """
    return _integ_sem_1()


_integ_sem_1 = Integ(
    lambda: ingreso() - avance_1() - desercion_1(), lambda: 0, "_integ_sem_1"
)


@component.add(
    name="Sem 10",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_10": 1},
    other_deps={
        "_integ_sem_10": {
            "initial": {},
            "step": {
                "avance_9": 1,
                "graduacion_oportuna": 1,
                "paso_a_rezago": 1,
                "desercion_10": 1,
            },
        }
    },
)
def sem_10():
    """
    Estudiantes en el semestre 10 (9 del plan más uno de margen).
    """
    return _integ_sem_10()


_integ_sem_10 = Integ(
    lambda: avance_9() - graduacion_oportuna() - paso_a_rezago() - desercion_10(),
    lambda: 0,
    "_integ_sem_10",
)


@component.add(
    name="Sem 2",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_2": 1},
    other_deps={
        "_integ_sem_2": {
            "initial": {},
            "step": {"avance_1": 1, "avance_2": 1, "desercion_2": 1},
        }
    },
)
def sem_2():
    """
    Estudiantes matriculados en el semestre 2.
    """
    return _integ_sem_2()


_integ_sem_2 = Integ(
    lambda: avance_1() - avance_2() - desercion_2(), lambda: 0, "_integ_sem_2"
)


@component.add(
    name="Sem 3",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_3": 1},
    other_deps={
        "_integ_sem_3": {
            "initial": {},
            "step": {"avance_2": 1, "avance_3": 1, "desercion_3": 1},
        }
    },
)
def sem_3():
    """
    Estudiantes matriculados en el semestre 3.
    """
    return _integ_sem_3()


_integ_sem_3 = Integ(
    lambda: avance_2() - avance_3() - desercion_3(), lambda: 0, "_integ_sem_3"
)


@component.add(
    name="Sem 4",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_4": 1},
    other_deps={
        "_integ_sem_4": {
            "initial": {},
            "step": {"avance_3": 1, "avance_4": 1, "desercion_4": 1},
        }
    },
)
def sem_4():
    """
    Estudiantes matriculados en el semestre 4.
    """
    return _integ_sem_4()


_integ_sem_4 = Integ(
    lambda: avance_3() - avance_4() - desercion_4(), lambda: 0, "_integ_sem_4"
)


@component.add(
    name="Sem 5",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_5": 1},
    other_deps={
        "_integ_sem_5": {
            "initial": {},
            "step": {"avance_4": 1, "avance_5": 1, "desercion_5": 1},
        }
    },
)
def sem_5():
    """
    Estudiantes matriculados en el semestre 5.
    """
    return _integ_sem_5()


_integ_sem_5 = Integ(
    lambda: avance_4() - avance_5() - desercion_5(), lambda: 0, "_integ_sem_5"
)


@component.add(
    name="Sem 6",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_6": 1},
    other_deps={
        "_integ_sem_6": {
            "initial": {},
            "step": {"avance_5": 1, "avance_6": 1, "desercion_6": 1},
        }
    },
)
def sem_6():
    """
    Estudiantes matriculados en el semestre 6.
    """
    return _integ_sem_6()


_integ_sem_6 = Integ(
    lambda: avance_5() - avance_6() - desercion_6(), lambda: 0, "_integ_sem_6"
)


@component.add(
    name="Sem 7",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_7": 1},
    other_deps={
        "_integ_sem_7": {
            "initial": {},
            "step": {"avance_6": 1, "avance_7": 1, "desercion_7": 1},
        }
    },
)
def sem_7():
    """
    Estudiantes matriculados en el semestre 7.
    """
    return _integ_sem_7()


_integ_sem_7 = Integ(
    lambda: avance_6() - avance_7() - desercion_7(), lambda: 0, "_integ_sem_7"
)


@component.add(
    name="Sem 8",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_8": 1},
    other_deps={
        "_integ_sem_8": {
            "initial": {},
            "step": {"avance_7": 1, "avance_8": 1, "desercion_8": 1},
        }
    },
)
def sem_8():
    """
    Estudiantes matriculados en el semestre 8.
    """
    return _integ_sem_8()


_integ_sem_8 = Integ(
    lambda: avance_7() - avance_8() - desercion_8(), lambda: 0, "_integ_sem_8"
)


@component.add(
    name="Sem 9",
    units="Estudiantes",
    comp_type="Stateful",
    comp_subtype="Integ",
    depends_on={"_integ_sem_9": 1},
    other_deps={
        "_integ_sem_9": {
            "initial": {},
            "step": {"avance_8": 1, "avance_9": 1, "desercion_9": 1},
        }
    },
)
def sem_9():
    """
    Estudiantes matriculados en el semestre 9.
    """
    return _integ_sem_9()


_integ_sem_9 = Integ(
    lambda: avance_8() - avance_9() - desercion_9(), lambda: 0, "_integ_sem_9"
)


@component.add(
    name="Semilla",
    units="Dmnl",
    limits=(1.0, 100.0, 1.0),
    comp_type="Constant",
    comp_subtype="Normal",
)
def semilla():
    """
    Semilla de números aleatorios. Se cambia en cada réplica (1 a 10).
    """
    return 1


@component.add(
    name="Tasa 1",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_1": 1, "multiplicador_comun": 1, "reduccion_temprana": 1},
)
def tasa_1():
    """
    Tasa de deserción por periodo del semestre 1.
    """
    return tasa_base_1() * multiplicador_comun() * (1 - reduccion_temprana())


@component.add(
    name="Tasa 10",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_10": 1, "multiplicador_comun": 1, "reduccion_tardia": 1},
)
def tasa_10():
    """
    Tasa de deserción por periodo del semestre 10.
    """
    return tasa_base_10() * multiplicador_comun() * (1 - reduccion_tardia())


@component.add(
    name="Tasa 2",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_2": 1, "multiplicador_comun": 1, "reduccion_temprana": 1},
)
def tasa_2():
    """
    Tasa de deserción por periodo del semestre 2.
    """
    return tasa_base_2() * multiplicador_comun() * (1 - reduccion_temprana())


@component.add(
    name="Tasa 3",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_3": 1, "multiplicador_comun": 1, "reduccion_media": 1},
)
def tasa_3():
    """
    Tasa de deserción por periodo del semestre 3.
    """
    return tasa_base_3() * multiplicador_comun() * (1 - reduccion_media())


@component.add(
    name="Tasa 4",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_4": 1, "multiplicador_comun": 1, "reduccion_media": 1},
)
def tasa_4():
    """
    Tasa de deserción por periodo del semestre 4.
    """
    return tasa_base_4() * multiplicador_comun() * (1 - reduccion_media())


@component.add(
    name="Tasa 5",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_5": 1, "multiplicador_comun": 1, "reduccion_media": 1},
)
def tasa_5():
    """
    Tasa de deserción por periodo del semestre 5.
    """
    return tasa_base_5() * multiplicador_comun() * (1 - reduccion_media())


@component.add(
    name="Tasa 6",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_6": 1, "multiplicador_comun": 1, "reduccion_tardia": 1},
)
def tasa_6():
    """
    Tasa de deserción por periodo del semestre 6.
    """
    return tasa_base_6() * multiplicador_comun() * (1 - reduccion_tardia())


@component.add(
    name="Tasa 7",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_7": 1, "multiplicador_comun": 1, "reduccion_tardia": 1},
)
def tasa_7():
    """
    Tasa de deserción por periodo del semestre 7.
    """
    return tasa_base_7() * multiplicador_comun() * (1 - reduccion_tardia())


@component.add(
    name="Tasa 8",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_8": 1, "multiplicador_comun": 1, "reduccion_tardia": 1},
)
def tasa_8():
    """
    Tasa de deserción por periodo del semestre 8.
    """
    return tasa_base_8() * multiplicador_comun() * (1 - reduccion_tardia())


@component.add(
    name="Tasa 9",
    units="1/Semestre",
    comp_type="Auxiliary",
    comp_subtype="Normal",
    depends_on={"tasa_base_9": 1, "multiplicador_comun": 1, "reduccion_tardia": 1},
)
def tasa_9():
    """
    Tasa de deserción por periodo del semestre 9.
    """
    return tasa_base_9() * multiplicador_comun() * (1 - reduccion_tardia())


@component.add(
    name="Tasa base 1", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_1():
    """
    Tasa por periodo del perfil SPADIES, semestre 1.
    """
    return 0.204


@component.add(
    name="Tasa base 10", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_10():
    """
    Tasa por periodo del perfil SPADIES, semestre 10.
    """
    return 0.024


@component.add(
    name="Tasa base 2", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_2():
    """
    Tasa por periodo del perfil SPADIES, semestre 2.
    """
    return 0.117


@component.add(
    name="Tasa base 3", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_3():
    """
    Tasa por periodo del perfil SPADIES, semestre 3.
    """
    return 0.087


@component.add(
    name="Tasa base 4", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_4():
    """
    Tasa por periodo del perfil SPADIES, semestre 4.
    """
    return 0.076


@component.add(
    name="Tasa base 5", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_5():
    """
    Tasa por periodo del perfil SPADIES, semestre 5.
    """
    return 0.074


@component.add(
    name="Tasa base 6", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_6():
    """
    Tasa por periodo del perfil SPADIES, semestre 6.
    """
    return 0.06


@component.add(
    name="Tasa base 7", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_7():
    """
    Tasa por periodo del perfil SPADIES, semestre 7.
    """
    return 0.054


@component.add(
    name="Tasa base 8", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_8():
    """
    Tasa por periodo del perfil SPADIES, semestre 8.
    """
    return 0.033


@component.add(
    name="Tasa base 9", units="1/Semestre", comp_type="Constant", comp_subtype="Normal"
)
def tasa_base_9():
    """
    Tasa por periodo del perfil SPADIES, semestre 9.
    """
    return 0.023


@component.add(
    name="Tasa des rezago",
    units="1/Semestre",
    comp_type="Constant",
    comp_subtype="Normal",
)
def tasa_des_rezago():
    """
    CRUD: 0,039.
    """
    return 0.04


@component.add(
    name="Tasa grad rezago",
    units="1/Semestre",
    comp_type="Constant",
    comp_subtype="Normal",
)
def tasa_grad_rezago():
    """
    CRUD: 0,119.
    """
    return 0.12
