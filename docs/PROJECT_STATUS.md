# Estado del proyecto

- **Fase actual:** shell desktop Tauri completado, instalado y listo para evaluación humana.
- **Última funcionalidad:** ventana nativa propia con backend sidecar administrado.
- **Existe:** Tauri/WebView2, SQLite, jobs/recovery, API loopback dinámica, FFmpeg integrado, UI, fixture 1920×1080, preview, reemplazo, export, tests Python/Rust y build NSIS.
- **Instalación validada:** `C:\Users\jose\AppData\Local\FacelessCreator\FacelessCreator.exe`.
- **Instalador en Escritorio:** `C:\Users\jose\consul\Escritorio\Instalar FacelessCreator Desktop.exe`, 128392392 bytes, SHA-256 `362B0E78E51C3490981AC631EF14C2CA81EAEB95EEEA92DF9BEEB1E679154758`.
- **Lifecycle:** puerto libre; espera de salud; cero navegador; backend hijo directo; monitor de PID padre; cierre validado sin procesos ni puertos huérfanos.
- **Datos locales:** `%LOCALAPPDATA%\FacelessCreator\UserData`, separados del directorio de instalación.
- **No existe:** importación de guion/audio reales, Visual Library real, voz, proveedor IA, firma de código o CI.
- **Pruebas:** unitarias, integración, smoke, E2E multimedia, regresión, parent monitor, Rust, captura nativa y smoke del instalador/copia instalada.
- **Bloqueos:** ninguno para evaluar.
- **Riesgos:** SmartScreen puede advertir porque el instalador no está firmado; WebView2 es requisito del sistema y fue detectado instalado.
- **Siguiente tarea:** evaluación humana de la ventana y definición del formato real de guion.
- **Estado Git:** entrega desktop validada y preparada para publicación.
