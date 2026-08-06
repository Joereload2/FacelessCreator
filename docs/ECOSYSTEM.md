# FacelessCreator en el ecosistema

**Rol:** producción **long horizontal** faceless (no analysis, no Library canónica, no shorts).

## Dueños

| Qué | App |
|-----|-----|
| Nicho / ficha / brief / lote de 10 | YouToMagic |
| **Guion final** (escribir/editar/aprobar) | **FacelessCreator** |
| Imágenes lección approved | VisuaLibrary → `package/media/images` |
| TTS ElevenLabs + thumbs packaging + FFmpeg MP4 | **FacelessCreator** |
| Shorts | VigilCut |
| Analytics canal | YouToMagic |

## Package path

`Documents/FacelessStudio/packages/{package_id}/package.yaml`

Código:

- `faceless_creator.package_io` — list/load/blocks
- `faceless_creator.tts` — `StubTtsAdapter` + skeleton `ElevenLabsTtsAdapter`
- `faceless_creator.visual_library_port` — resolve local media; HTTP stub para VL

## Infra lista / API pendiente

| Pieza | Estado |
|-------|--------|
| Load package + narrative blocks | Listo |
| Stub TTS (markers + duration) | Listo |
| ElevenLabs HTTP real | **Conectar API key** (NotImplemented hasta entonces) |
| Resolve images from package | Listo (si VL copió archivos) |
| VL HTTP resolve | Skeleton |
| Constructor de guion (brief → draft → approved) | Listo (UI + API) |
| Wire import package → RenderPlan | Listo parcial |
| Render FFmpeg desde package beats | Parcial (alinear post-approve) |

## Estado UI

Ver `PROJECT_STATUS.md`. Este doc no sustituye PRODUCT/ARCHITECTURE.
