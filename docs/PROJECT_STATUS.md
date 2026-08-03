# Estado del proyecto

- **Fase actual:** shell desktop Tauri completado, instalado y listo para evaluación humana.
- **Última funcionalidad:** workstation supervisada contenida íntegramente en el viewport, sin barras de desplazamiento visibles globales o internas, con medios completos sin recorte.
- **Existe:** Tauri/WebView2, SQLite, jobs/recovery, API loopback dinámica, FFmpeg integrado, UI compacta, importación de audio, fixture 1920×1080, preview, reemplazo, export, tests Python/Rust y build NSIS.
- **Instalación validada:** `C:\Users\jose\AppData\Local\FacelessCreator\FacelessCreator.exe`.
- **Instalador en Escritorio:** `C:\Users\jose\consul\Escritorio\Instalar FacelessCreator Desktop.exe`, 128386372 bytes, SHA-256 `33BB01F32F563B7075983F3C4D7DCE93D30E553D5779B9D0A03706075D4CF84C`.
- **Lifecycle:** puerto libre; espera de salud; cero navegador; backend hijo directo; monitor de PID padre; cierre validado sin procesos ni puertos huérfanos.
- **Datos locales:** `%LOCALAPPDATA%\FacelessCreator\UserData`, separados del directorio de instalación.
- **No existe:** importación de guion real, Visual Library real, voz, proveedor IA, firma de código o CI.
- **Pruebas:** unitarias, integración, smoke, E2E multimedia, regresiones de navegación, layout workstation, densidad vertical, contratos DOM, audio y subsistema gráfico, parent monitor, Rust, captura nativa y smoke del instalador/copia instalada.
- **Bloqueos:** ninguno para evaluar.
- **Riesgos:** SmartScreen puede advertir porque el instalador no está firmado; WebView2 es requisito del sistema y fue detectado instalado.
- **Siguiente tarea:** evaluación humana de la workstation y definición del formato real de guion.
- **Estado Git:** entrega desktop validada y preparada para publicación.
