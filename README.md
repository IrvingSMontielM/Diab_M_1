# Diab_M_1

Investigacion-Modelacion para **modelar, diagnosticar y controlar** el
sistema glucosa-insulina, con trazabilidad hacia los marcos regulatorios de
ingenieria biomedica (FDA, COFEPRIS/NOM, ISO, IEC). Basado en el
modelo de Stolwijk-Hardy modificado por Khoo (2018) y lo lleva a una base de código
reproducible, probada y documentada que sirve como cimiento para una futura app y,
mas adelante, para el desarrollo de un dispositivo.

> **Esto es software academico. No es un dispositivo medico, no diagnostica
> pacientes y no debe gobernar una bomba de insulina real.** Lee
> [`DISCLAIMER.md`](DISCLAIMER.md) antes de continuar.

## Que hace
El proyecto cubre cuatro bloques que juntos describen un pancreas artificial en
simulacion, mas el contexto clinico y regulatorio que un sistema asi requiere.

El primero es el **modelado fisiologico**. Implementa el modelo de Stolwijk-Hardy
(Khoo 2018) que reproduce los tres escenarios del PDF (persona sana, DM1 y DM2) y el
modelo minimo de Bergman, que es el paciente virtual estandar en la literatura de
control glucemico. El segundo es el **diagnostico**: clasifica el estado glucemico
segun glucosa en ayunas, HbA1c y curva de tolerancia oral, aplicando los umbrales de
la ADA, la OMS y la NOM-015-SSA2 con su logica de confirmacion. El tercero es el
**procesamiento de senal CGM**: filtrado, estimacion de tendencia y, sobre todo,
evaluacion de exactitud contra ISO 15197:2013 y la guia FDA 2016, ademas de la
rejilla de error de Clarke. El cuarto es el **control en lazo cerrado**: un PID con
anti-windup y un **supervisor de seguridad** que imita las salvaguardas reales de un
sistema AID (suspension por hipoglucemia, suspension predictiva, tope de insulina
activa, tope de dosis y limite de velocidad).

## Los tres examenes que detectan diabetes

El modulo `diagnostics` codifica los tres analisis de sangre de referencia y sus
umbrales diagnosticos. Estos valores provienen de los Standards of Care de la ADA, la
OMS y la NOM-015-SSA2-2010.

| Examen | Umbral de diabetes | Prediabetes |
|---|---|---|
| Glucosa plasmatica en ayunas (FPG) | >= 126 mg/dL, confirmada en dos pruebas | 100-125 mg/dL (ADA) |
| Hemoglobina glucosilada (HbA1c) | >= 6.5 % | 5.7-6.4 % |
| Tolerancia oral a la glucosa (2 h) | >= 200 mg/dL | 140-199 mg/dL |

La regla de confirmacion importa: una sola prueba diabetica aislada exige una segunda
prueba para confirmar, salvo hiperglucemia inequivoca con sintomas clasicos. El codigo
implementa exactamente esa logica. Detalle completo en
[`docs/clinical/diagnostic_criteria.md`](docs/clinical/diagnostic_criteria.md).

## Instalacion

Requiere Python 3.10 o superior.

```bash
git clone https://github.com/IrvingSMontielM/Diab_M_1.git
cd Diab_M_1
pip install -e .            # instala el paquete y sus dependencias (numpy, scipy)
pip install -e ".[plot,dev]"  # opcional: matplotlib para los ejemplos y pytest
```

## Inicio rapido

Clasificar un caso diagnostico:

```python
from diab_m1.diagnostics import classify, Criteria

reporte = classify(fpg_mg_dl=131, a1c_percent=6.8, criteria=Criteria.ADA)
print(reporte.summary())
```

Ejemplos:

```bash
PYTHONPATH=src python3 examples/01_simulate_scenarios.py   # sano / DM1 / DM2
PYTHONPATH=src python3 examples/02_closed_loop_pid.py       # PID + seguridad
```

El primer ejemplo genera la respuesta de 24 h a tres comidas. El sano se mantiene en
euglucemia con picos moderados; la DM1 y la DM2 muestran hiperglucemia sostenida con
una diferencia clave en la insulina: baja en DM1 (secrecion deficiente) y alta en DM2
(hiperinsulinemia compensatoria). En este modelo reducido la glucosa depende del
producto de la sensibilidad de secrecion por la captacion dependiente de insulina, asi
que reducir cualquiera de las dos al 20 % da la misma glucosa pero insulina muy
distinta, que es justo la distincion clinica entre ambos tipos.

El segundo ejemplo controla un paciente DM1 virtual. El lazo cerrado recorta los picos
posprandiales frente al lazo abierto (de ~231 a ~201 mg/dL), mantiene un tiempo en
rango 70-180 del 96.5 % y **cero tiempo en hipoglucemia**. El supervisor de seguridad
suspende la infusion durante el descenso posprandial para evitar la sobrecorreccion,
que es exactamente el valor que aporta esa capa.

## Mapa de modulos

```
src/diab_m1/
  units.py                 conversiones mg/dL <-> mmol/L, HbA1c <-> IFCC/eAG
  meals.py                 perfiles de comida y absorcion intestinal (gamma)
  models/
    stolwijk_hardy.py      modelo de Khoo 2018 (sano, DM1, DM2)
    bergman.py             modelo minimo (paciente virtual para control)
  diagnostics/
    classifier.py          clasificacion ADA / OMS / NOM-015 con confirmacion
  signal/
    cgm.py                 filtrado, tendencia, ISO 15197, FDA 2016, Clarke
  control/
    pid.py                 PID discreto con anti-windup
    safety.py              supervisor de seguridad (LGS, PLGS, IOB, topes)
docs/
  regulatory/              mapeo a FDA, COFEPRIS, ISO 14971, IEC 62304, ISO 15197
  clinical/                criterios diagnosticos y bibliografia
  roadmap_app_and_device.md  ruta hacia app y dispositivo
examples/                  scripts reproducibles que generan figuras
tests/                     43 pruebas (pytest)
```

## Pruebas

```bash
PYTHONPATH=src python3 -m pytest -q
```

Las 43 pruebas cubren conversiones de unidades, equilibrios y dinamica de ambos
modelos, la logica de confirmacion diagnostica, las metricas de exactitud CGM y cada
salvaguarda del supervisor de seguridad.

## Marco regulatorio

El proyecto se documenta pensando en los estandares que rigen un dispositivo de manejo
de diabetes. En Mexico, la **NOM-015-SSA2-2010** norma la prevencion y el tratamiento
de la diabetes, y la **NOM-241-SSA1-2025** (publicada en el DOF el 4 de abril de 2025)
fija las buenas practicas de fabricacion de dispositivos medicos; **COFEPRIS** clasifica
los dispositivos por riesgo en clases I, II y III. En Estados Unidos, la **FDA** definio
la arquitectura de pancreas artificial interoperable con las categorias iCGM, ACE pump e
iAGC. A nivel internacional aplican **ISO 13485** (calidad), **ISO 14971** (gestion de
riesgos), **IEC 62304** (ciclo de vida del software medico) e **ISO 15197** (exactitud de
medidores de glucosa). El detalle y la trazabilidad estan en
[`docs/regulatory/`](docs/regulatory/). Ese mapeo es orientativo: el codigo apoya el
cumplimiento, pero no lo sustituye.

## Hacia la app y el dispositivo

La ruta de tres etapas (biblioteca de investigacion, aplicacion, dispositivo) con sus
compuertas regulatorias esta en
[`docs/roadmap_app_and_device.md`](docs/roadmap_app_and_device.md). La biblioteca es la
etapa uno y ya esta aqui.


## Licencia

MIT. Ver [`LICENSE`](LICENSE). Software de investigacion, no es un dispositivo medico.
