# AVISO IMPORTANTE: software de investigacion, NO es un dispositivo medico

**Lee esto antes de usar el codigo.**

`Diab_M_1` es un proyecto de **investigacion y educacion** en ingenieria biomedica.
Contiene modelos fisiologicos, algoritmos de control y rutinas de procesamiento de
senal que se ejecutan **solo en simulacion**, con pacientes virtuales.

## Lo que este proyecto NO es

- **No es un dispositivo medico.** No tiene marcado CE, ni autorizacion de la FDA,
  ni registro sanitario ante COFEPRIS. No ha pasado verificacion ni validacion
  clinica de ningun tipo.
- **No sirve para diagnosticar.** El modulo `diagnostics` aplica los umbrales
  publicados (ADA, OMS, NOM-015) con fines didacticos. Un diagnostico real lo
  emite un profesional de la salud con pruebas de laboratorio validadas.
- **No debe gobernar una bomba de insulina real ni dosificar a una persona.**
  El controlador PID y el supervisor de seguridad operan sobre modelos
  matematicos, no sobre pacientes. Conectarlos a hardware de infusion en un ser
  humano es peligroso y puede causar **hipoglucemia severa o la muerte**.

## Por que el codigo no equivale a cumplimiento normativo

Cumplir con FDA, COFEPRIS, ISO 13485, ISO 14971, IEC 62304 o ISO 15197 exige un
sistema de gestion de calidad, gestion de riesgos documentada, verificacion y
validacion trazables, evaluacion clinica y auditorias. El codigo es, a lo sumo,
**evidencia tecnica de apoyo** dentro de ese proceso. Tener el codigo no acredita
nada por si solo. La carpeta `docs/regulatory/` mapea como este repositorio se
relaciona con esos marcos, pero ese mapeo es **orientativo**, no una certificacion.

## Uso responsable

Usa este proyecto para aprender, prototipar algoritmos, preparar material academico
y construir portafolio. Si en el futuro buscas trasladar algo de aqui a un producto
clinico, hazlo dentro de un sistema de calidad formal, con asesoria regulatoria y
los estudios de verificacion, validacion y evaluacion clinica que la ley exige.

Si necesitas evaluar tu propia glucosa, acude a un laboratorio y a un medico.
