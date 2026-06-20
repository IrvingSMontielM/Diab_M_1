# 03. Ciclo de vida del software (IEC 62304:2006+A1:2015)

IEC 62304 define los procesos del ciclo de vida del software de dispositivos medicos.
Este documento describe como se mapearia la biblioteca a esos procesos y por que el
software de control caeria en la clase de seguridad mas alta. **Es un ejercicio
educativo**, no un expediente de ciclo de vida formal.

## Clases de seguridad

IEC 62304 asigna a cada elemento de software una clase segun el dano posible si el
software falla. La clase A aplica cuando no es posible una lesion ni dano a la salud. La
clase B cuando es posible una lesion no seria. La clase C cuando es posible la muerte o
una lesion seria. La clasificacion considera los mitigantes externos al software, de modo
que una arquitectura con barreras independientes puede reducir la clase de algunos
elementos.

## Clasificacion de los elementos de Diab_M_1

El **controlador de dosificacion** (`control/pid.py`) seria **clase C** en un producto
real, porque una orden de insulina incorrecta puede causar hipoglucemia con riesgo de
muerte. El **supervisor de seguridad** (`control/safety.py`) tambien seria **clase C**:
es la barrera que decide si una dosis se permite, suspende o limita, y su falla expone
directamente al paciente. El **procesamiento de senal CGM** (`signal/cgm.py`) seria
**clase B o C** segun si su salida alimenta decisiones de dosificacion. El modulo de
**diagnostico** (`diagnostics/classifier.py`), si solo informa y no actua, seria **clase
A o B**. El modulado fisiologico (`models/`) es herramienta de simulacion y verificacion,
no software de produccion embarcado.

## Arquitectura como argumento de seguridad

La separacion entre el controlador y el supervisor es deliberada y es un argumento de
diseno reconocido en sistemas AID reales, que incorporan un control de seguridad
redundante que avisa de la hipoglucemia inminente. El controlador optimiza el desempeno;
el supervisor, independiente, impone los limites duros. Esta segregacion permite razonar
sobre la seguridad aunque el controlador tenga un error, porque el supervisor seguiria
cortando dosis peligrosas. En IEC 62304 esta segregacion entre elementos es lo que
habilita un argumento de reduccion de riesgo.

## Procesos del ciclo de vida y su correspondencia

El proceso de **desarrollo** abarca planificacion, analisis de requisitos, diseno
arquitectonico, diseno detallado, implementacion y pruebas unitarias, de integracion y de
sistema. En el repositorio, los requisitos viven en `05_requirements_traceability.md`, la
arquitectura es la estructura de paquetes de `src/diab_m1`, la implementacion es el codigo
y las pruebas unitarias son la suite de `tests/`. El proceso de **gestion de
configuracion** se cubre con el control de versiones en git. El proceso de **resolucion de
problemas** correspondería al seguimiento de issues. Los procesos de **gestion de
riesgos** se enlazan con ISO 14971 en `02_iso_14971_risk_management.md`, y los de
**mantenimiento** definirian como se atienden cambios despues de liberar.

## Verificacion presente y lo que faltaria

La verificacion actual son las 43 pruebas automatizadas que comprueban cada salvaguarda y
la dinamica de los modelos. Un producto de clase C exigiria ademas: un plan de desarrollo
de software documentado, especificacion de requisitos de software trazada a riesgos,
descripcion de la arquitectura con interfaces, analisis de software de origen desconocido
(SOUP) para numpy y scipy con sus versiones y anomalias conocidas, cobertura de pruebas
definida y medida, y pruebas de integracion y de sistema formales con sus registros.
