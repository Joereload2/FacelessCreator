# QA

## Lectura obligatoria

[Testing](../../constitution/TESTING.md), [Done](../../constitution/DONE.md) y el flujo afectado en [Workflows](../../WORKFLOWS.md).

## Ejecutar

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s . -v
python -m compileall -q src tests
node --check src\faceless_creator\web\app.js
git diff --check
```

## Cobertura actual

- Unit: validación de bloques, paths y continuidad del plan.
- Integración: SQLite/migración, recovery, jobs/retry y FFmpeg/ffprobe.
- Smoke: health, shell HTML, errores API y creación de proyecto.
- E2E: fixture → plan → preview → reemplazo → export → MP4/SRT/manifiesto.
- Regresión: ruta segura de imágenes y retry con misma clave idempotente.

Las pruebas multimedia usan resolución pequeña para velocidad; la validación manual automatizada de milestone ejecuta además 1920×1080.

