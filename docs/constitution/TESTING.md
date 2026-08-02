# Constitución de pruebas

## Unitarias

Cubrir reglas de dominio, transiciones, validaciones, cálculo de tiempos, mappings, invariantes de `RenderPlan`, paths seguros e idempotencia. Deben ser deterministas, rápidas y sin red/procesos reales salvo que el adapter bajo prueba lo exija explícitamente.

## Integración

Cubrir SQLite, migraciones, filesystem temporal aislado, jobs/recovery, fakes de proveedores, application layer y adapters multimedia. Verificar fallos parciales y consistencia entre metadata y archivos.

## Smoke

Cuando existan las capacidades, comprobar: app inicia; DB abre; migraciones aplican; directorios se crean; proyecto se crea; fixture carga; preview básico produce archivo válido; render básico produce archivo válido.

## E2E objetivo

Crear proyecto → cargar guion → cargar audio → resolver imágenes mediante adapter controlado → crear `RenderPlan` → generar/abrir preview → reemplazar imagen → renderizar → validar MP4/SRT/manifiesto → cerrar → abrir → recuperar proyecto.

El E2E crece por milestone; no se simula una capacidad inexistente para declarar el flujo completo.

## Regresión

Todo bug significativo incluye una prueba que falla antes y pasa después en la capa más baja que lo reproduzca, más una prueba superior si falló un contrato entre capas.

## Proveedores

No usar APIs reales en la suite normal. Usar fakes y contract tests. Pruebas reales son manuales o explícitas, protegidas por variables de entorno, consentimiento y límites de coste; nunca parte automática de CI normal.

## Matriz por riesgo

- **LOW:** unit relevante, smoke aplicable y diff check.
- **MEDIUM:** unit, integración y smoke aplicables.
- **HIGH:** unit, integración, smoke, E2E relevante y regresión si es bugfix.
- **ARCHITECTURE:** todas las aplicables, documentación, ADR y revisión multi-rol.

“Aplicable” exige una justificación concreta cuando se omite. No se crean pruebas vacías para satisfacer categorías.

## Fixtures y multimedia

Fixtures pequeños, versionables y sin datos sensibles; declarar resolución, duración, formato y licencia/origen. Validar salidas por probe, streams, duración tolerada, resolución, codec y exit status, no solo por existencia del archivo.
