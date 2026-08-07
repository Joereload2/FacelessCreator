# AGENTS.md — FacelessCreator

Fuente de verdad para agentes en este repo.

## Rol en el ecosistema (no negociable)

Estación de **ensamblaje long horizontal** faceless.

| Hace | No hace |
|------|---------|
| Guion final (brief YTM → draft → approve) | Elegir nichos / discovery YouTube |
| TTS (ElevenLabs o stub) + voice_id | Library canónica de conceptos (VisuaLibrary) |
| Import package → RenderPlan → preview/export MP4 | Shorts 9:16 (VigilCut) |
| Thumbs packaging (stub / providers) | Analytics de canal (YouToMagic) |

**Credenciales ElevenLabs y OmniRoute (guion LLM): solo aquí**  
Panel UI Credenciales → `UserData/credentials.json` (+ env override).  
No configurar ElevenLabs en YouToMagic.

## Flujo package

```
list packages → cargar brief → escribir/aprobar guion → TTS → importar y planificar → preview/export
```

Path: `%USERPROFILE%\Documents\FacelessStudio\packages\`  
`package.yaml` = JSON schema **0.1** (`Documents/FacelessStudio/schemas/package.schema.json`).  
`load_package` valida nivel `import`. Audio/imágenes en `media/`.

Sin keys: plantilla de guion + TTS stub + silencio si no hay mp3 real.  
Con ElevenLabs inválido: fallback a stub por beat (no tumbar el job).

## Stack

- Backend: Python 3.12 (`faceless_creator`)
- Shell: Tauri 2 + WebView (UI estática en `web/`)
- FFmpeg/ffprobe embebidos o en PATH
- Datos: `%LOCALAPPDATA%\FacelessCreator\UserData`

## Comandos

```powershell
.\run.cmd
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
python -m unittest discover -s tests -v
cargo test --manifest-path src-tauri\Cargo.toml
powershell -File scripts\build_desktop.ps1
```

## Código clave

- `package_io.py` / `package_state.py` — packages
- `service.py` — `prepare_from_package`, jobs
- `tts.py` — Stub + ElevenLabs + fallback
- `script_writer.py` — template + OmniRoute
- `credentials.py` — keys locales
- `web/app.js` + `index.html` — UI

## Docs clave

- `docs/PRODUCT.md`, `docs/ECOSYSTEM.md`, `docs/PROJECT_STATUS.md`
- YouToMagic `docs/18-ECOSISTEMA-APPS.md`

## Al cambiar código

- No mover discovery de nichos a este repo.
- Mantener banner/honestidad stub vs real.
- Actualizar este archivo si cambian ports o lifecycle del backend.
