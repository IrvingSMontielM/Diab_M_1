# 02. Gestion de riesgos (ISO 14971:2019)

Este documento esboza un analisis de riesgos preliminar para un sistema de dosificacion
automatica de insulina derivado de la biblioteca. **Es un ejercicio educativo**, no un
expediente de gestion de riesgos formal. ISO 14971 exige un proceso documentado,
revisado y mantenido durante todo el ciclo de vida, con politica de aceptabilidad de
riesgo, evaluacion de riesgo residual y reporte de produccion y posproduccion.

## Proceso

ISO 14971 estructura la gestion de riesgos en analisis (identificar peligros y estimar
riesgos), evaluacion (compararlos con criterios de aceptabilidad), control (implementar
mitigantes y verificar su eficacia) y evaluacion del riesgo residual global, mas la
informacion de produccion y posproduccion que retroalimenta el ciclo.

## Peligro central

El peligro dominante es la **dosificacion incorrecta de insulina**. Demasiada insulina
causa hipoglucemia, que puede llevar a convulsiones, coma o muerte. Muy poca insulina
causa hiperglucemia y, sostenida, cetoacidosis. El analisis prioriza la prevencion de la
hipoglucemia porque su dano es agudo e inmediato.

## Tabla de analisis de riesgos preliminar

La estimacion usa una escala simple de severidad (S: 1 menor a 5 catastrofico) y
probabilidad (P: 1 raro a 5 frecuente). El indice de riesgo es S por P. Los mitigantes
implementados en codigo viven en `control/safety.py` y `control/pid.py`.

| ID | Peligro / situacion | Causa | S | P | Mitigante de diseno | Implementacion |
|---|---|---|---|---|---|---|
| R1 | Sobredosis de insulina por lectura de glucosa erronea alta | Falla o ruido del sensor | 5 | 3 | Rechazo de dato fuera de rango fisiologico y suspension por falla | `SafetySupervisor` paso 1 (sensor fault) |
| R2 | Hipoglucemia por acumulacion de insulina | Dosificacion repetida sin contabilizar insulina activa | 5 | 3 | Tope de insulina a bordo (IOB) | `InsulinOnBoard` + paso 4 |
| R3 | Hipoglucemia inminente no anticipada | Glucosa descendiendo rapido | 4 | 3 | Suspension predictiva (PLGS) con horizonte de prediccion | `SafetySupervisor` paso 3 |
| R4 | Hipoglucemia ya presente | Glucosa por debajo del umbral | 5 | 2 | Suspension reactiva (LGS) y reanudacion solo sobre umbral seguro | `SafetySupervisor` paso 2 |
| R5 | Dosis unica excesiva | Pico del controlador, windup | 5 | 2 | Tope duro de dosis y anti-windup del integrador | paso 5 + clamping en `PIDController` |
| R6 | Cambio brusco de infusion | Transitorio del controlador | 3 | 3 | Limite de velocidad de cambio por minuto | `SafetySupervisor` paso 6 |
| R7 | Actuacion sobre dato viejo | Perdida de comunicacion con el sensor | 4 | 3 | Suspension si la antiguedad del dato supera el limite | paso 1 (stale data) |
| R8 | Oscilacion sostenida de glucosa | Mala sintonia del PID | 3 | 3 | Sintonia validada en simulacion y filtro derivativo | `derivative_tau` en `PIDController` |

## Orden de las salvaguardas

El supervisor aplica los mitigantes en orden de prioridad: primero la integridad del
sensor, luego la proteccion reactiva contra hipoglucemia, despues la predictiva, en
seguida el limite de insulina activa, el tope duro de dosis y por ultimo el limite de
velocidad. Este orden asegura que las protecciones de mayor severidad dominen sobre las
de ajuste fino.

## Riesgo residual y validacion

El ejemplo `examples/02_closed_loop_pid.py` evidencia el efecto de los mitigantes:
elimina el tiempo en hipoglucemia y reduce los picos posprandiales. En un proceso real
esto seria apenas el inicio: se requeririan simulaciones con cohortes de pacientes
virtuales (por ejemplo el simulador UVA/Padova aceptado por la FDA), pruebas de
inyeccion de fallas, y finalmente evaluacion clinica. El riesgo residual global tendria
que evaluarse contra una politica de aceptabilidad definida antes de iniciar.
