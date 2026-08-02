# Constitución de ingeniería

## General

- Elegir la solución más simple que cumpla el requerimiento y sus fallos conocidos.
- No añadir flexibilidad especulativa ni optimizar sin medición.
- Mantener una fuente de verdad por dato y contratos explícitos entre módulos.
- Entregar cambios pequeños y cohesivos; no mezclar refactor masivo con feature.
- Hacer específicas de plataforma solo las implementaciones de adapters.

## Backend y aplicación

- Dominio independiente de frameworks, transporte y persistencia.
- Casos de uso de grano grueso; ninguna UI coordina transacciones internas.
- Validar en fronteras y expresar errores estructurados, accionables y sin secretos.
- Delimitar transacciones; no afirmar éxito antes de persistir el estado coherente.
- Diseñar idempotencia para comandos repetibles y jobs.
- Encapsular multimedia, IA y proveedores detrás de puertos.
- Prohibidos panic/unwrap o equivalentes sobre entradas y fallos de producción; propagar contexto controlado.

## Frontend

- Separar estado efímero de snapshots persistidos.
- Usar contratos tipados y versionados.
- No ubicar reglas de negocio ni acceso directo a filesystem/proveedores en componentes.
- No iniciar trabajos al montar; toda ejecución requiere comando explícito e idempotente.
- Proteger doble envío y reflejar el ID durable del job.
- Reconstruir pantallas desde snapshots; eventos solo disparan refresco, no son fuente de verdad.

## Datos y filesystem

- Usar SQLite si satisface la prueba; justificar una opción más compleja.
- Migraciones numeradas, probadas e inmutables una vez publicadas; foreign keys activas.
- Backup verificado antes de migración destructiva.
- Guardar bytes en filesystem y metadata/hashes en almacenamiento transaccional.
- Resolver rutas dentro del workspace; validar symlinks/reparse points y colisiones.
- Escribir temporales propios, validar y finalizar atómicamente.

## Jobs

- Persistir antes de ejecutar y usar transiciones explícitas.
- Soportar progreso persistido, cancelación cooperativa, retry clasificado e idempotencia.
- Recuperar ejecuciones huérfanas al iniciar.
- Validar outputs antes de Succeeded.
- La UI observa y comanda; no posee el ciclo de vida.

## Multimedia

- Ejecutar planes reproducibles con versiones y hashes de inputs.
- Separar inputs, temporales y outputs; nunca modificar inputs.
- Usar probe o validación equivalente antes y después.
- Capturar argumentos, exit status y diagnóstico seguro, no contenido sensible.
- Limpiar solo temporales identificados dentro del workspace propio.
