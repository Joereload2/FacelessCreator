
# Backend local

## Lectura obligatoria

[Arquitectura](../../ARCHITECTURE.md), [Dominio](../../DOMAIN.md), [Engineering](../../constitution/ENGINEERING.md), [Security](../../constitution/SECURITY.md) y [Testing](../../constitution/TESTING.md).

## Implementación actual

- `config.py`: workspace y configuración fija 1920×1080/30 fps.
- `database.py`: conexión SQLite, migraciones v1–v2 y reconciliación de jobs huérfanos.
- `domain.py`: bloques, escenas, plan e invariantes de rutas/tiempos.
- `jobs.py`: ejecución durable en threads, progreso, retry e idempotencia.
- `service.py`: casos de uso de grano grueso.
- `server.py`: HTTP de loopback, API JSON/binaria, estáticos y artifacts.
- `visuals.py`: puerto visual y adaptador local controlado.

SQLite es autoridad de estado durable y el workspace almacena bytes. El servidor solo escucha loopback por defecto. No hay proveedor externo ni secretos.

## Límites actuales

El guion continúa como fixture hasta recibir un ejemplo real. El audio ya puede importarse y reemplazarse; se valida, copia al workspace y persiste como metadata. La distribución nativa está implementada. Cancelación multimedia cooperativa y alineación temporal real permanecen pendientes.
