# Estado del proyecto

- **Fase actual:** shell desktop Tauri completado, instalado y listo para evaluación humana.
- **Última funcionalidad:** workstation supervisada contenida íntegramente en el viewport, sin barras de desplazamiento visibles globales o internas, con medios completos sin recorte.
- **Existe:** Tauri/WebView2, SQLite, jobs/recovery, API loopback dinámica, FFmpeg integrado, UI compacta, importación de audio, fixture 1920×1080, preview, reemplazo, export, tests Python/Rust y build NSIS.
- **Instalación validada:** `C:\Users\jose\AppData\Local\FacelessCreator\FacelessCreator.exe`.
- **Instalador en Escritorio:** `C:\Users\jose\consul\Escritorio\Instalar FacelessCreator Desktop.exe`, 128386372 bytes, SHA-256 `33BB01F32F563B7075983F3C4D7DCE93D30E553D5779B9D0A03706075D4CF84C`.
- **Lifecycle:** puerto libre; espera de salud; cero navegador; backend hijo directo; monitor de PID padre; cierre validado sin procesos ni puertos huérfanos.
- **Datos locales:** `%LOCALAPPDATA%\FacelessCreator\UserData`, separados del directorio de instalación.
- **Constructor de guion (2026-08-06):** UI + API en FC — cargar brief YTM, generar (template/OmniRoute), editar, guardar borrador, aprobar. YTM ya no escribe guion final.
- **No existe aún (producto):** ElevenLabs real sin env key, contrato VL HTTP real, firma de código o CI, Gemini thumbs real.
- **Infra package:** `package_io` (channels + packages), `script_writer`, `packaging_thumbs`, `tts`, gate de lote, `visual_library_port`. Packages en `Documents/FacelessStudio/`.
- **Pruebas:** unitarias, integración, smoke, E2E multimedia, layout workstation, `test_package_io`, `test_script_writer_and_pipeline`.
- **Bloqueos:** ninguno para evaluar shell + constructor de guion con stubs; APIs reales con keys.
- **Riesgos:** SmartScreen puede advertir porque el instalador no está firmado; WebView2 es requisito del sistema.
- **Siguiente tarea:** alinear RenderPlan a beats del package tras aprobar guion; conectar keys reales.
- **Ecosistema:** ver `ECOSYSTEM.md` y YouToMagic `docs/18-ECOSISTEMA-APPS.md`.
- **Estado Git:** entrega desktop validada y preparada para publicación.
