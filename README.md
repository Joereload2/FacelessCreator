# FacelessCreator

Aplicación local para ensamblar y supervisar videos horizontales faceless.

## Requisitos

- Windows para la validación inicial.
- Python 3.12 o posterior.
- FFmpeg y ffprobe disponibles en `PATH`.

## Iniciar

```bat
run.cmd
```

La aplicación abre `http://127.0.0.1:8765` y guarda su workspace en `.facelesscreator/`. No utiliza servicios externos.

## Probar

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s . -v
```

Empieza por [docs/00-START-HERE.md](docs/00-START-HERE.md).
