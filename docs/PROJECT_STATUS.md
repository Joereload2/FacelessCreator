# Estado del proyecto

- **Fase actual:** M7 completado; ejecutable portable Windows validado y disponible en el Escritorio.
- **Última funcionalidad completada:** distribución Windows en un único `.exe`.
- **Existe:** aplicación Python local, SQLite, jobs/recovery, API loopback, FFmpeg integrado, UI, fixture 1920×1080, preview, reemplazo, export, 15 pruebas y build PyInstaller reproducible.
- **Ejecutable:** `C:\Users\jose\consul\Escritorio\FacelessCreator.exe`, 191270773 bytes, SHA-256 `701A81FB914EF2EDE18905355D6ABB431BD7405EC90FC319D9536BD3754220E1`.
- **Datos locales:** `%LOCALAPPDATA%\FacelessCreator`; puede sobrescribirse con `FACELESSCREATOR_HOME` o `--workspace`.
- **No existe:** importación de guion/audio reales, Visual Library real, voz, proveedor IA, firma de código o CI.
- **Pruebas disponibles:** unitarias, integración, smoke, E2E multimedia, regresión, launcher y smoke end-to-end del `.exe` portable.
- **Bloqueos:** ninguno para evaluar la interfaz desde el Escritorio.
- **Riesgos:** Windows puede mostrar SmartScreen porque el ejecutable no está firmado; el formato real del guion sigue pendiente.
- **Siguiente tarea:** evaluación humana del ejecutable y definición de importación real.
- **Estado Git:** cambios de distribución validados, pendientes de commit y push.
