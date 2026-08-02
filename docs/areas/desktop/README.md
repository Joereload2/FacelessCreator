# Shell desktop

## Responsabilidad

Tauri provee la ventana propia y administra el proceso backend. No contiene dominio ni coordina trabajos de producción.

## Arranque

1. Reserva un puerto libre en `127.0.0.1`.
2. Resuelve el sidecar empaquetado desde recursos.
3. Inicia `FacelessCreatorBackend.exe` con `--no-browser`, puerto y PID padre.
4. Espera hasta 45 segundos que el puerto responda.
5. Construye una ventana WebView2 apuntando a la URL loopback.

No existe un puerto fijo ni una pestaña del navegador.

## Cierre

Rust mantiene el handle del proceso hijo e intenta terminarlo en eventos de salida. Como defensa independiente, el backend abre un handle Windows al PID del shell; cuando Windows señaliza su terminación, ejecuta `server.shutdown()`. El sidecar usa PyInstaller `onedir` para evitar wrappers intermedios.

La prueba de lifecycle exige: ventana nativa, backend hijo directo, `ffmpeg: true`, cero navegadores nuevos, cierre por `Alt+F4`, desaparición del backend y liberación del puerto.

## Build

- `src-tauri/`: código, configuración, capabilities e icono.
- `FacelessCreatorSidecar.spec`: backend `onedir` con FFmpeg.
- `scripts/build_desktop.ps1`: sidecar, Tauri release e instalador NSIS.
- `package.json`: CLI Tauri precompilada.

WebView2 debe estar instalado. No se descarga durante la instalación actual.
