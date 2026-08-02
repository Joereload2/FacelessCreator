# FacelessCreator

Aplicación local de escritorio para ensamblar y supervisar videos horizontales faceless.

## Aplicación de escritorio Windows

El instalador nativo está en:

```text
src-tauri\target\release\bundle\nsis\FacelessCreator_0.1.0_x64-setup.exe
```

Instala una ventana Tauri propia, sin pestaña ni URL de navegador. La ventana inicia un backend privado en un puerto loopback dinámico, espera su salud y lo detiene al cerrar. Los proyectos viven en `%LOCALAPPDATA%\FacelessCreator\UserData`, separados de los archivos instalados.

Para reconstruir:

```powershell
npm.cmd install
python -m pip install -r requirements-build.txt
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\build_desktop.ps1
```

## Desarrollo del backend

Requisitos: Python 3.12 o posterior y FFmpeg/ffprobe en `PATH`.

```powershell
.\run.cmd
```

## Probar

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s . -v
cargo test --manifest-path src-tauri\Cargo.toml
```

Empieza por [docs/00-START-HERE.md](docs/00-START-HERE.md).
