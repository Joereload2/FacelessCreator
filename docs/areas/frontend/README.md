

# Frontend

## Lectura obligatoria

[Producto](../../PRODUCT.md), [Arquitectura](../../ARCHITECTURE.md), [UX/UI](../../constitution/UX_UI.md) y [Testing](../../constitution/TESTING.md).

## Implementación actual

HTML, CSS y JavaScript sin dependencias, servidos solo por la aplicación local. La UI ofrece:

- creación y recuperación de proyectos;
- navegación horizontal compacta por producciones, sin barra lateral ni barra permanente de etapas;
- estado actual, una acción primaria contextual y resumen operativo;
- carga o reemplazo visible de audio local y preparación del fixture;
- preview dominante 73/27 con inspector contextual;
- filmstrip narrativo, selección de escenas y alternativas;
- reemplazo visual con nueva versión del plan;
- exportación y apertura externa de artifacts sin reemplazar la aplicación;
- errores estructurados y progreso durable.

El estado persistido siempre se vuelve a consultar por API. Los timers solo actualizan snapshots; no son autoridad.

## Inicio

La distribución principal es la ventana Tauri instalada. `run.cmd` conserva el modo de desarrollo del backend y abre la UI local.
