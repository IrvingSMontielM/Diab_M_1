# 04. Desempeno analitico (ISO 15197:2013 y guia FDA 2016)

Este documento detalla los criterios de exactitud que un sistema de medicion de glucosa
debe cumplir y como el modulo `signal/cgm.py` los evalua sobre datos sinteticos. **El
codigo evalua el criterio; no sustituye un estudio de exactitud con sangre real frente a
un metodo de referencia trazable.**

## Criterio de ISO 15197:2013

ISO 15197:2013 (adoptada como EN ISO 15197:2015) exige que **al menos el 95 %** de los
resultados del sistema caigan dentro de **+/-15 mg/dL** respecto al valor de referencia
cuando la glucosa es menor a 100 mg/dL, o dentro de **+/-15 %** cuando es de 100 mg/dL o
mas. A esto se suma un criterio de consenso: el 99 % de los resultados debe ubicarse en
las zonas A o B de una rejilla de error de consenso.

La funcion `iso15197_accuracy(measured, reference)` implementa el primer criterio:
calcula la diferencia absoluta por par, aplica la tolerancia que corresponde segun el
umbral de 100 mg/dL, y devuelve el porcentaje dentro de tolerancia con la bandera de
aprobacion en 95 %.

## Criterio de la guia FDA 2016 (SMBG)

La guia de la FDA de octubre de 2016 para medidores de uso casero (SMBG) es mas estricta:
exige que el **95 %** de los resultados caiga dentro de **+/-15 %** en todo el intervalo y
que el **99 %** caiga dentro de **+/-20 %**. La funcion `fda_2016_accuracy(measured,
reference)` evalua ambas condiciones y solo aprueba si las dos se cumplen.

La diferencia practica es que la FDA elimina la tolerancia absoluta holgada en
hipoglucemia y endurece la cola del 99 %, lo que exige mejor desempeno en valores bajos,
justo donde un error es mas peligroso.

## Rejilla de error de Clarke

La rejilla de error de Clarke clasifica cada par medicion-referencia en cinco zonas. La
zona A corresponde a error clinicamente irrelevante, la B a desviaciones que no llevan a
un tratamiento inapropiado, y las zonas C, D y E a errores con consecuencias clinicas
crecientes. La funcion `clarke_error_grid_zone(reference, measured)` devuelve la zona, y
`clarke_zone_distribution` reparte un conjunto de pares en porcentajes por zona. Es la
herramienta clasica para comunicar la relevancia clinica de los errores, mas alla del
porcentaje agregado.

## Como se usa en el proyecto

Las pruebas en `tests/test_cgm.py` verifican que un sistema perfecto alcanza 100 % dentro
de tolerancia y aprueba, que un sesgo del 30 % reprueba, que el criterio FDA es mas
estricto que el de ISO en datos limitrofes, y que una coincidencia exacta cae en zona A.
En un desarrollo real, estas funciones se aplicarian a los datos de un estudio de
exactitud con muestras de sangre frente a un analizador de laboratorio trazable, no a
datos sinteticos, y el estudio seguiria el diseno de muestreo y los rangos de
concentracion que la propia ISO 15197 especifica.
