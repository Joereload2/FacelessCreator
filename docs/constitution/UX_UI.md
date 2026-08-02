# Constitución UX/UI

FacelessCreator debe sentirse como una fábrica supervisada, no como un editor generalista.

## Layout

- Ningún componente sale del contenedor principal y no existe scroll horizontal global.
- Desktop-first; validar capturas y uso a 1366×768, 1440×900 y 1920×1080.
- Cuando preview es la tarea central, ocupa al menos 70% del workspace útil; el panel secundario, aproximadamente 30% como máximo y con scroll interno.
- No dejar áreas grandes vacías sin función, estado o guía.

## Flujo

Toda estación comunica sin documentación externa: qué hace el usuario, qué hace la aplicación, qué necesita del usuario, qué falta, siguiente paso y si terminó o procesa. Mostrar una acción primaria por estado y mantener disponibles las acciones seguras de recuperación.

## Navegación

- Una sola navegación principal organizada por flujo/estación.
- No exponer nombres de entidades técnicas ni módulos irrelevantes.
- Evitar tabs anidados y rutas paralelas al mismo estado.
- No convertir la navegación en una línea de tiempo editable arbitraria.

## Preview y selección

- Ninguna decisión visual se aprueba sin preview.
- El primer MVP genera un archivo temporal mediante acción explícita y permite abrirlo externamente; la UI muestra versión, estado y vigencia del preview.
- Recurso seleccionado claramente visible; miniaturas compactas; clic selecciona; hover nunca cambia estado.
- El preview principal concentra detalles, reemplazo, encuadre permitido y aprobación.

## Estados obligatorios

Cada estación diseña, cuando aplique: vacío, carga, procesamiento, esperando revisión, éxito, sin resultados, error, interrupción y cancelación. Cada estado presenta explicación, impacto y siguiente acción. No mostrar éxito mientras el job o artifact no esté validado.

## Accesibilidad

- Operable por teclado, orden de foco lógico y foco visible.
- Contraste suficiente y semántica/ARIA apropiada al framework.
- Estado y errores nunca dependen solo del color.
- Etiquetas y mensajes describen acciones y recuperación en lenguaje del usuario.
- Respetar reducción de movimiento; ninguna animación bloquea una acción.

## Verificación

Para cambios de UI se requieren capturas en las tres resoluciones, recorrido por teclado, inspección de overflow y prueba de todos los estados tocados. Una pantalla nueva falla revisión si necesita explicar entidades internas para poder usarse.
