# Criterios diagnosticos de diabetes y prediabetes

Este documento resume los criterios que el modulo `diagnostics` implementa, con sus
fuentes. **Tiene fines educativos. El diagnostico de diabetes lo realiza un profesional
de la salud con pruebas de laboratorio validadas y la interpretacion del cuadro clinico
completo.**

## Las tres pruebas y sus umbrales

El diagnostico de diabetes se apoya en tres analisis de sangre. La glucosa plasmatica en
ayunas requiere un ayuno de al menos ocho horas. La hemoglobina glucosilada (HbA1c)
refleja el promedio de glucemia de los dos a tres meses previos. La prueba de tolerancia
oral a la glucosa mide la glucemia dos horas despues de ingerir 75 g de glucosa.

| Categoria | FPG (mg/dL) | HbA1c (%) | OGTT 2 h (mg/dL) | Glucosa casual |
|---|---|---|---|---|
| Normal | < 100 | < 5.7 | < 140 | --- |
| Prediabetes | 100-125 (ADA) | 5.7-6.4 | 140-199 | --- |
| Diabetes | >= 126 | >= 6.5 | >= 200 | >= 200 con sintomas |

La ADA y la OMS coinciden en los umbrales de diabetes. Difieren en la prediabetes por
glucosa en ayunas: la ADA define la glucosa alterada en ayunas desde 100 mg/dL, mientras
la OMS la situa desde 110 mg/dL. El codigo modela ambos marcos a traves del parametro
`criteria`.

## Regla de confirmacion

Un resultado diabetico aislado debe confirmarse con una segunda prueba antes de
diagnosticar, porque un valor unico puede deberse a variabilidad o a error preanalitico.
La excepcion es la hiperglucemia inequivoca con sintomas clasicos (poliuria, polidipsia,
perdida de peso), donde una glucosa casual de 200 mg/dL o mas basta. El clasificador
implementa esta logica: marca `requires_confirmation` cuando una sola prueba resulta
diabetica, no lo exige cuando dos pruebas coinciden, y reconoce el caso de la glucosa
casual con sintomas.

## Conversiones de unidades

El modulo `units` implementa las conversiones de uso clinico. La glucosa pasa de mg/dL a
mmol/L dividiendo entre 18.0182, de modo que el umbral de 126 mg/dL equivale a 6.99
mmol/L y el de 200 mg/dL a 11.1 mmol/L. La HbA1c convierte entre la escala NGSP en
porcentaje y la escala IFCC en mmol/mol mediante la relacion IFCC = 10.929 por (NGSP
menos 2.15). La glucosa promedio estimada (eAG) se obtiene de la HbA1c con la formula
del estudio ADAG, eAG en mg/dL = 28.7 por A1c menos 46.7.

## Fuentes

Los umbrales provienen de los Standards of Care in Diabetes de la American Diabetes
Association, de los criterios de la Organizacion Mundial de la Salud, y de la
NOM-015-SSA2-2010 vigente en Mexico. Las referencias completas estan en
[`references.bib`](references.bib).
