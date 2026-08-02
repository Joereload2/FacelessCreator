# FacelessCreator

Aplicación local para ensamblar y supervisar videos horizontales faceless.

## Ejecutable de Windows

El build portable produce un único `FacelessCreator.exe` con Python, frontend, FFmpeg y ffprobe incluidos. Los proyectos se guardan en `%LOCALAPPDATA%\FacelessCreator`.

Para reconstruirlo:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

El resultado queda en `dist\FacelessCreator.exe`.

## Desarrollo

Requisitos: Python 3.12 o posterior y FFmpeg/ffprobe en `PATH`.

```powershell
.\run.cmd
```

La aplicación abre `http://127.0.0.1:8765` y no utiliza servicios externos.

## Probar

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s . -v
```

Empieza por [docs/00-START-HERE.md](docs/00-START-HERE.md).
