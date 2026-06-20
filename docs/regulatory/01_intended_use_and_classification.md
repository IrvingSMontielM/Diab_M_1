# 01. Intencion de uso y clasificacion por riesgo

## Estado actual del proyecto

Hoy `Diab_M_1` es una **biblioteca de simulacion e investigacion**. Opera sobre
pacientes virtuales y no toca hardware ni pacientes. En este estado no constituye un
dispositivo medico bajo ninguna jurisdiccion y no requiere autorizacion. Lo que sigue
describe la intencion de uso **hipotetica** de un producto derivado, util para anticipar
la ruta regulatoria, no para afirmar conformidad presente.

## Intencion de uso hipotetica de un producto derivado

Un sistema derivado de esta biblioteca buscaria ayudar a personas con diabetes mellitus
a mantener la glucosa en rango mediante la dosificacion automatica de insulina, tomando
como entrada la senal de un monitor continuo de glucosa y actuando sobre una bomba de
infusion, con un supervisor de seguridad que limite la dosis. La poblacion objetivo
serian adultos con DM1, y eventualmente DM2 insulinodependiente, bajo prescripcion y
seguimiento medico.

## Clasificacion tentativa por riesgo

Un sistema de dosificacion automatica de insulina es de **alto riesgo** porque una falla
puede provocar hipoglucemia o hiperglucemia graves. La clasificacion tentativa por
jurisdiccion seria la siguiente.

| Jurisdiccion | Marco | Clase tentativa | Via probable |
|---|---|---|---|
| Estados Unidos | FDA, sistema interoperable | iAGC (controlador) y ACE pump | De Novo si no hay predicado; luego 510(k) |
| Mexico | COFEPRIS | Clase II o III segun integracion e invasividad | Registro sanitario; MDSAP facilita la ruta |
| Union Europea | MDR 2017/745 | Clase IIb o III | Evaluacion de conformidad con organismo notificado |

El componente de software de control, al gobernar una decision que puede causar dano
serio, exige el nivel de rigor mas alto en gestion de riesgos y ciclo de vida del
software.

## Funciones y su naturaleza regulatoria

El modulo `diagnostics` aplica umbrales diagnosticos publicados. Como herramienta
informativa y educativa no diagnostica; un producto que emitiera un diagnostico seria
software como dispositivo medico (SaMD) y caeria bajo el marco de SaMD de la IMDRF. El
modulo `signal/cgm` evalua exactitud analitica, funcion ligada a ISO 15197. El modulo
`control` toma decisiones de dosificacion, el corazon del riesgo del sistema. El
supervisor de seguridad en `control/safety.py` implementa los mitigantes que la gestion
de riesgos exigiria.

## Que falta para que esto fuera un dispositivo

Un sistema de gestion de calidad ISO 13485, el expediente de gestion de riesgos ISO
14971 completo, la documentacion de ciclo de vida IEC 62304 con verificacion y
validacion trazables, los estudios de exactitud y de evaluacion clinica, la ingenieria
de usabilidad IEC 62366-1, la seguridad electrica IEC 60601-1 del hardware, y la
sumision regulatoria correspondiente en cada jurisdiccion.
