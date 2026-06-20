# 05. Trazabilidad de requisitos

Este documento traza requisitos del sistema hacia los modulos que los implementan y las
pruebas que los verifican. La trazabilidad es un pilar de IEC 62304 e ISO 13485: cada
requisito debe poder seguirse hasta su diseno, su codigo y su verificacion. **Esta matriz
es educativa** y cubre la biblioteca en su estado de simulacion.

## Convencion

Los requisitos se numeran por dominio: REQ-DX (diagnostico), REQ-MOD (modelado),
REQ-SIG (senal), REQ-CTL (control) y REQ-SAF (seguridad). Cada fila enlaza el requisito
con su archivo de implementacion y su archivo de prueba.

## Matriz

| ID | Requisito | Implementacion | Verificacion |
|---|---|---|---|
| REQ-DX-1 | Clasificar el estado glucemico por FPG, HbA1c y OGTT con umbrales ADA/OMS/NOM-015 | `diagnostics/classifier.py` | `tests/test_diagnostics.py` |
| REQ-DX-2 | Exigir confirmacion ante una sola prueba diabetica, salvo hiperglucemia inequivoca con sintomas | `classifier.py` (logica de confirmacion) | `test_diagnostics.py` (casos de confirmacion y sintomas) |
| REQ-DX-3 | Aceptar entradas en mg/dL y mmol/L | `classifier.py` + `units.py` | `test_diagnostics.py` (caso mmol/L) |
| REQ-MOD-1 | Reproducir el equilibrio basal sano del PDF (x~0.81, y~0.056) | `models/stolwijk_hardy.py` | `test_models.py` (basal sano) |
| REQ-MOD-2 | Diferenciar DM1 (insulina baja) de DM2 (insulina alta) | `stolwijk_hardy.py` (`dm1_params`, `dm2_params`) | `test_models.py` (insulina relativa) |
| REQ-MOD-3 | Proveer un paciente virtual estable para control en lazo cerrado | `models/bergman.py` | `test_models.py` (basal euglucemico estable) |
| REQ-SIG-1 | Estimar la tendencia de glucosa de forma causal | `signal/cgm.py` (`estimate_rate`) | `test_cgm.py` (rampa lineal) |
| REQ-SIG-2 | Evaluar exactitud contra ISO 15197:2013 | `cgm.py` (`iso15197_accuracy`) | `test_cgm.py` (aprueba/reprueba) |
| REQ-SIG-3 | Evaluar exactitud contra la guia FDA 2016 | `cgm.py` (`fda_2016_accuracy`) | `test_cgm.py` (mas estricta que ISO) |
| REQ-SIG-4 | Clasificar errores en la rejilla de Clarke | `cgm.py` (`clarke_error_grid_zone`) | `test_cgm.py` (zona A, distribucion) |
| REQ-CTL-1 | Calcular la infusion con un PID que no infunda valores negativos | `control/pid.py` (saturacion `out_min`) | `test_control_safety.py` (paso normal) |
| REQ-CTL-2 | Evitar la acumulacion del integrador en saturacion (anti-windup) | `pid.py` (clamping condicional) | cubierto por el lazo cerrado en `examples/02` |
| REQ-SAF-1 | Suspender ante dato de sensor invalido o viejo | `control/safety.py` (paso 1) | `test_control_safety.py` (sensor invalido/viejo) |
| REQ-SAF-2 | Suspender por hipoglucemia y reanudar solo sobre umbral seguro | `safety.py` (paso 2) | `test_control_safety.py` (LGS, reanudacion) |
| REQ-SAF-3 | Suspender por prediccion de hipoglucemia | `safety.py` (paso 3) | `test_control_safety.py` (PLGS) |
| REQ-SAF-4 | Limitar la dosis por insulina activa (IOB) | `safety.py` (`InsulinOnBoard`, paso 4) | `test_control_safety.py` (tope IOB, decaimiento) |
| REQ-SAF-5 | Imponer un tope duro de dosis | `safety.py` (paso 5) | `test_control_safety.py` (tope duro) |
| REQ-SAF-6 | Limitar la velocidad de cambio de la infusion | `safety.py` (paso 6) | `test_control_safety.py` (limite de velocidad) |

## Cobertura

Cada requisito de seguridad (REQ-SAF) tiene al menos una prueba dedicada, lo que refleja
la prioridad que la gestion de riesgos asigna a esas funciones. Los requisitos de control
de desempeno fino (anti-windup) se verifican de forma integrada en el ejemplo de lazo
cerrado, que demuestra estabilidad y ausencia de hipoglucemia. En un proceso formal, la
matriz se mantendria viva: todo cambio de codigo actualizaria la fila correspondiente y
toda nueva prueba quedaria enlazada a su requisito.
