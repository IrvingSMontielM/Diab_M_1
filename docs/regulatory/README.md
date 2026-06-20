# Marco regulatorio de Diab_M_1

Esta carpeta mapea como el proyecto se relaciona con los estandares y normas que
regirian un dispositivo de manejo de diabetes. **El mapeo es orientativo y educativo.**
Documentar la intencion de uso, los riesgos o la clase de software no convierte al
codigo en un producto conforme: el cumplimiento real exige un sistema de gestion de
calidad, verificacion y validacion trazables, evaluacion clinica y auditorias dentro de
una organizacion fabricante. Ver [`../../DISCLAIMER.md`](../../DISCLAIMER.md).

## Por que estos estandares

Un pancreas artificial integra tres elementos regulados: un sensor continuo de glucosa,
un algoritmo de control y una bomba de infusion. Cada uno cae bajo normas especificas, y
el sistema completo bajo marcos de calidad, riesgo y software.

## Mexico

La **NOM-015-SSA2-2010**, "Para la prevencion, tratamiento y control de la diabetes
mellitus", es la norma vigente que define criterios de diagnostico y manejo. Fija los
umbrales que el modulo `diagnostics` implementa.

La **NOM-241-SSA1-2025**, "Buenas practicas de fabricacion de dispositivos medicos", se
publico en el Diario Oficial de la Federacion el 4 de abril de 2025 y entra en vigor 240
dias naturales despues de su publicacion. Es obligatoria para fabricantes y
distribuidores de dispositivos medicos en Mexico, y pone el acento en el sistema de
gestion de calidad, el control de proveedores y el analisis de riesgo a lo largo del
ciclo de vida del producto.

**COFEPRIS** es la autoridad sanitaria. Clasifica los dispositivos por riesgo en clases
I, II y III, donde la clase III corresponde a dispositivos nuevos o implantables por mas
de 30 dias. COFEPRIS reconoce el Medical Device Single Audit Program (MDSAP), lo que
facilita la convergencia con otras jurisdicciones.

## Estados Unidos (FDA)

La FDA estructuro el pancreas artificial interoperable en tres componentes que se
autorizan por separado y luego se integran. El **iCGM** (monitor continuo de glucosa
interoperable) se estableci con el Dexcom G6 por la via De Novo en marzo de 2018. La
**ACE pump** (bomba de infusion de alternancia controlada) se establecio con la Tandem
t:slim X2 en febrero de 2019. El **iAGC** (controlador automatico de glucemia
interoperable) se establecio con Control-IQ de Tandem el 13 de diciembre de 2019, y mas
tarde con Omnipod 5 de Insulet en enero de 2022. Tras una autorizacion De Novo, los
dispositivos siguientes de la misma categoria pueden despejarse por la via 510(k). La
expansion a diabetes tipo 2 llego con Omnipod 5 en agosto de 2024 y Control-IQ+ en
febrero de 2025.

## Internacional (ISO / IEC)

Cuatro estandares estructuran el desarrollo. **ISO 13485:2016** define el sistema de
gestion de calidad para dispositivos medicos. **ISO 14971:2019** rige la gestion de
riesgos. **IEC 62304:2006+A1:2015** define el ciclo de vida del software de dispositivos
medicos y sus clases de seguridad A, B y C. **ISO 15197:2013** fija los criterios de
exactitud de los sistemas de medicion de glucosa. Complementan **IEC 60601-1**
(seguridad de equipo electromedico) e **IEC 62366-1** (ingenieria de usabilidad).

## Contenido de esta carpeta

El archivo `01_intended_use_and_classification.md` plantea la intencion de uso y una
clasificacion tentativa por riesgo. El `02_iso_14971_risk_management.md` contiene un
analisis de riesgos preliminar con su tabla. El `03_iec_62304_software_lifecycle.md`
asigna la clase de seguridad del software y describe el ciclo de vida. El
`04_iso_15197_analytical_performance.md` detalla los criterios de exactitud analitica y
como el codigo los evalua. El `05_requirements_traceability.md` traza requisitos hacia
modulos y pruebas.
