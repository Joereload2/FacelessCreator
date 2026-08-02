# Distribución Windows

## Distribución actual

El producto principal es el instalador NSIS Tauri. Instala una ventana propia en `%LOCALAPPDATA%\FacelessCreator` y conserva datos en `%LOCALAPPDATA%\FacelessCreator\UserData`.

El backend se empaqueta como PyInstaller `onedir` con Python, frontend, FFmpeg y ffprobe. Tauri lo incluye como recurso y produce:

```text
src-tauri\target\release\bundle\nsis\FacelessCreator_0.1.0_x64-setup.exe
```

## Construcción

```powershell
npm.cmd install
python -m pip install -r requirements-build.txt
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\build_desktop.ps1
```

## Validación obligatoria

1. Tests Python y Rust.
2. Build sidecar, shell release e instalador.
3. Instalar silenciosamente por usuario en QA.
4. Confirmar ventana nativa y cero navegadores nuevos.
5. Confirmar backend hijo, puerto dinámico, `/api/health` y FFmpeg.
6. Ejecutar fixture/preview 1920×1080.
7. Cerrar con `Alt+F4`; comprobar proceso y puerto liberados.
8. Verificar que DB esté bajo `UserData` y comparar SHA-256 del instalador copiado.

## Limitaciones

- El instalador no está firmado y Windows puede mostrar SmartScreen.
- WebView2 debe estar instalado; no se descarga en el modo actual.
- El build tarda por la compresión de los binarios multimedia.
