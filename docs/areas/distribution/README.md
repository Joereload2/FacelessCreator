# Distribución Windows

## Objetivo

Entregar un único `FacelessCreator.exe` que funcione sin una instalación separada de Python o FFmpeg. PyInstaller extrae el runtime a un temporal al iniciar y la aplicación guarda estado durable en `%LOCALAPPDATA%\FacelessCreator`.

## Construcción

Requiere Python 3.12, PyInstaller y FFmpeg/ffprobe en `PATH`:

```powershell
python -m pip install pyinstaller
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

`FacelessCreator.spec` incluye los recursos web, FFmpeg, ffprobe y el runtime hook que expone los binarios empaquetados al adapter multimedia. El resultado es `dist\FacelessCreator.exe`.

## Validación obligatoria

1. Ejecutar el `.exe` con workspace temporal y puerto aislado.
2. Confirmar `/api/health`, `ffmpeg: true` y SQLite escribible.
3. Crear proyecto y fixture.
4. Generar preview 1920×1080.
5. Detener el proceso de smoke.
6. Comparar SHA-256 después de copiar al destino.

## Limitaciones

- El binario no está firmado y Windows puede mostrar SmartScreen.
- Pesa aproximadamente 182 MB porque incluye el runtime multimedia.
- El primer inicio tarda más que `onedir` por la extracción temporal.
