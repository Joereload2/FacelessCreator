# Plan de implementación

Cada milestone termina con sus criterios y una pausa técnica de análisis. Tras la aprobación de Foundation 0 se puede continuar sin revisión humana entre milestones hasta alcanzar una interfaz operativa y funcional, siempre que no se active una STOP Rule. No se hace push antes de ese punto.

## M0 — Foundation 0

- **Valor:** autoridades coherentes para ejecutar sin improvisación.
- **Alcance:** documentos canónicos; sin producto.
- **Documentos/capas:** todos los documentos Foundation 0; transversal.
- **Pruebas:** rutas/nombres, enlaces relativos, dos loops, `git diff --check`, `git status`.
- **Riesgo:** arquitectura documental inconsistente.
- **Salida:** aprobación humana explícita.

## M1 — Shell mínimo y prueba multimedia

- **Valor:** demuestra en Windows el camino mínimo desde imágenes/audio fixture a un archivo horizontal válido y expone una interfaz mínima que informa el resultado.
- **Alcance:** comparar el mínimo stack viable; scaffold; invocación controlada del candidato multimedia; probe/render de fixture; UI sin flujo de negocio completo.
- **Documentos/capas:** ADR tecnológica, arquitectura por área, multimedia, shell y QA.
- **Pruebas:** unit de comandos/rutas, integración del proceso, smoke de inicio y archivo válido.
- **Riesgo:** empaquetado, procesos, resolución y codecs.
- **Salida:** una opción tecnológica aceptada por evidencia, build reproducible y fixture renderizado/probado.

## M2 — Workspace, proyecto y jobs mínimos

- **Valor:** crear, cerrar y recuperar un proyecto durable.
- **Alcance:** raíz administrada, metadata local, migraciones, artifacts, job runner mínimo y pantalla de estado.
- **Capas:** dominio, persistencia, filesystem, jobs, API y UI del proyecto.
- **Pruebas:** unit, integración SQLite/filesystem/jobs, migraciones, smoke de recuperación.
- **Riesgo:** consistencia DB/archivos y cierres forzados.
- **Salida:** proyecto y job sobreviven reinicio; outputs se publican atómicamente.

## M3 — Guion estructurado y audio existente

- **Valor:** importar y validar los dos inputs narrativos reales.
- **Alcance:** cerrar formato desde fixtures, versionar guion, validar audio, alineación mínima verificable y estación de revisión.
- **Capas:** script, timing, artifacts, jobs, API y frontend.
- **Pruebas:** parser/validación/tiempos, integración de probe y job, smoke con fixture, E2E parcial.
- **Riesgo:** formato real del guion y precisión temporal.
- **Salida:** bloques y tiempos inspeccionables, recuperables y trazables.

## M4 — Contrato visual, escenas y RenderPlan

- **Valor:** convertir instrucciones visuales en un plan completo usando un fake/adaptador controlado.
- **Alcance:** puerto de Visual Library, referencias opacas, selecciones, escenas, receta y validación de plan; no integración real.
- **Capas:** dominio visual, planning, application, adapters fake y UI de estado.
- **Pruebas:** contrato, mapping, reglas temporales, invariantes de RenderPlan e integración del slice.
- **Riesgo:** contrato prematuro sin API real.
- **Salida:** plan reproducible para el fixture y contrato versionado reemplazable.

## M5 — Preview temporal y revisión visual

- **Valor:** primer montaje supervisable y corrección de imagen.
- **Alcance:** render temporal externo, workspace de preview, selección/reemplazo/encuadre básico e invalidación desde la etapa afectada.
- **Capas:** multimedia, jobs, artifacts, API, frontend y UX.
- **Pruebas:** integración de preview, idempotencia/invalidation, smoke y E2E de reemplazo; capturas a tres resoluciones.
- **Riesgo:** feedback del reproductor externo y coherencia de estados.
- **Salida:** preview válido, una excepción corregible y etapas previas reutilizadas.

## M6 — Export horizontal, SRT y manifiesto

- **Valor:** video horizontal final utilizable.
- **Alcance:** parámetros fijos cerrados por evidencia, export, validación, SRT opcional, metadata/manifiesto y recuperación.
- **Capas:** planning, jobs, multimedia, artifacts, UI y QA.
- **Pruebas:** tiempos/SRT, integración render/probe, smoke, E2E completo y recuperación por interrupción.
- **Riesgo:** compatibilidad de codecs, espacio y atomicidad.
- **Salida:** fixture produce MP4/SRT/manifiesto válidos y recuperables.

## M7 — Interfaz operativa y endurecimiento

- **Valor:** flujo completo comprensible y estable para uso real; punto autorizado para considerar push.
- **Alcance:** estados UX completos, accesibilidad, diagnósticos, cancel/retry, recuperación de cierres y empaquetado local.
- **Capas:** todas las del MVP.
- **Pruebas:** suite completa, E2E de flujo y recovery, smoke empaquetado, capturas 1366×768, 1440×900 y 1920×1080.
- **Riesgo:** integración transversal y deuda oculta.
- **Salida:** interfaz operativa y funcional, checklist Done cumplida y revisión multi-rol aprobada.

## M8 — Integración real con Visual Library

- **Valor:** sustituir el adaptador controlado por consultas reales sin cambiar el dominio.
- **Alcance:** descubrir/validar API local, adapter, errores y contract tests.
- **Pruebas:** contract/integration protegidas y E2E relevante.
- **Riesgo:** contrato externo aún desconocido.
- **Salida:** integración aprobada sin acceso directo a tablas.

## M9 — Voz y automatización avanzada

- **Valor:** generar audio y reducir excepciones adicionales.
- **Alcance:** elegir proveedor, consentimiento/coste, adapter, reconciliación cobrable y mejoras de recovery medidas.
- **Pruebas:** fakes por defecto; reales manuales protegidas; regresión y E2E relevante.
- **Riesgo:** privacidad, secretos, red, coste e idempotencia.
- **Salida:** flujo B seguro y verificable; automatizaciones adicionales solo con métricas.
