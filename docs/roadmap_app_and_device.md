# Ruta hacia la app y el dispositivo

Este documento traza el camino de tres etapas desde la biblioteca de investigacion actual
hasta un eventual dispositivo, con las compuertas regulatorias que separan cada etapa.
El punto clave es que las etapas no se saltan: cada una habilita la siguiente solo cuando
cumple sus criterios de salida.

## Etapa 1: biblioteca de investigacion (estado actual)

Ya existe. Contiene los modelos validados contra el PDF, el clasificador diagnostico, el
procesamiento de senal con metricas de exactitud, el controlador PID y el supervisor de
seguridad, todo cubierto por 43 pruebas y dos ejemplos reproducibles. Su proposito es
explorar algoritmos, generar material academico y servir de portafolio. No interactua con
pacientes ni con hardware.

El criterio de salida hacia la etapa 2 es tener los algoritmos estables, probados y
documentados, que es justo lo que esta base entrega.

## Etapa 2: aplicacion

La aplicacion convierte la biblioteca en una herramienta interactiva, todavia de
simulacion y educacion. La recomendacion tecnica es empezar con un panel en **Streamlit**
porque permite envolver el codigo Python existente sin reescribirlo, iterar rapido y
mostrar las simulaciones y las clasificaciones diagnosticas de inmediato. Si mas adelante
se busca una experiencia de producto con autenticacion, multiples usuarios y despliegue
movil, conviene migrar el frontend a **React** consumiendo una API que exponga la misma
biblioteca.

El alcance razonable de la app incluye un explorador de escenarios glucosa-insulina con
parametros ajustables, un asistente educativo de interpretacion diagnostica que aplique
los umbrales con sus advertencias, un visor de exactitud que cargue datos y reporte ISO
15197 y la rejilla de Clarke, y una demostracion de lazo cerrado con su capa de
seguridad. La app debe mantener el aviso de uso educativo en un lugar visible.

El criterio de salida hacia la etapa 3 es una decision deliberada de construir un
producto clinico, con asesoria regulatoria contratada y financiamiento, porque la etapa 3
es de otra naturaleza y otro costo.

## Etapa 3: dispositivo

Aqui el proyecto deja de ser software academico y se convierte en el desarrollo de un
dispositivo medico regulado. Esta etapa no se improvisa: arranca estableciendo un sistema
de gestion de calidad antes de escribir codigo de produccion.

Las compuertas regulatorias, en orden, son las siguientes. Primero, implantar un sistema
de gestion de calidad conforme a **ISO 13485** y a la **NOM-241-SSA1-2025** mexicana.
Segundo, abrir el expediente de gestion de riesgos **ISO 14971** y mantenerlo vivo.
Tercero, desarrollar el software bajo **IEC 62304** como clase C para el control y el
supervisor, con requisitos trazables, verificacion y validacion. Cuarto, si hay hardware,
cumplir la seguridad electrica de **IEC 60601-1** y la ingenieria de usabilidad de **IEC
62366-1**. Quinto, ejecutar los estudios de exactitud analitica frente a **ISO 15197** con
sangre real y metodo de referencia trazable. Sexto, conducir la evaluacion clinica que
demuestre seguridad y eficacia. Septimo, presentar ante la autoridad: en Mexico el
registro sanitario ante **COFEPRIS** segun la clase II o III, y en Estados Unidos la via
**De Novo** o **510(k)** dentro de la arquitectura de pancreas artificial interoperable de
la **FDA**.

## Una nota de realismo

Llevar un algoritmo de control de glucosa a un dispositivo aprobado toma anos, equipos
multidisciplinarios y capital significativo. Los sistemas comerciales que hoy existen son
el resultado de esa inversion sostenida. Esta biblioteca es un primer eslabon legitimo y
bien construido de esa cadena, no un atajo que la reemplace. El valor inmediato y real
esta en las etapas 1 y 2: aprender, demostrar dominio tecnico y construir un portafolio
solido.
