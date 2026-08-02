# Frontend

## Lectura obligatoria

[Producto](../../PRODUCT.md), [Arquitectura](../../ARCHITECTURE.md), [UX/UI](../../constitution/UX_UI.md) y [Testing](../../constitution/TESTING.md).

## Implementación actual

HTML, CSS y JavaScript sin dependencias, servidos solo por la aplicación local. La UI ofrece:

- creación y recuperación de proyectos;
- navegación única por producciones;
- progreso por estaciones e indicador del sistema;
- preparación del fixture;
- preview visual y audiovisual;
- selección de escenas y alternativas;
- reemplazo visual con nueva versión del plan;
- exportación y descarga de artifacts;
- errores estructurados y progreso durable.

El estado persistido siempre se vuelve a consultar por API. Los timers solo actualizan snapshots; no son autoridad.

## Inicio

En Windows, ejecutar `run.cmd`. `run.ps1` es equivalente cuando la política de PowerShell permite scripts. Se abre `http://127.0.0.1:8765`.

