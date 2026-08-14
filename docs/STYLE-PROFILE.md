# Style Profile en FacelessCreator

## Rol

FC **no genera** imágenes. Solicita a VisuaLibrary vía archivos:

`Documents/FacelessStudio/style_jobs/{inbox,outbox,media}/`

Contrato completo: `Documents/FacelessStudio/docs/STYLE-PROFILE-CONTRACT.md`

## Uso

1. En **VisuaLibrary**, crea un Style Profile (canal, `base_prompt`, 3–5 `reference_images`) y márcalo **activo**.
2. En el package / proyecto FC, define `style_profile_id` (meta del package o body de import):
   - `package.meta.style_profile_id`
   - o `package.channel_dna.style_profile_id`
   - o body: `{ "package_path": "...", "style_profile_id": "sp_…" }`
3. Al **import-package / prepare**, FC escribe un request por beat y espera outbox.
4. Para regenerar una escena:  
   `POST /api/projects/{id}/scenes/{scene_id}/regenerate-visual`  
   body: `{ "style_profile_id": "sp_…", "prompt": "opcional override" }`
5. Procesar cola en VL: comando Tauri `process_style_inbox_cmd` (o al abrir VL).

## Preview

Las escenas del RenderPlan usan `image_path` relativo al proyecto (`inputs/{beat_id}.*`).  
Si VL devuelve `needs_review` (p.ej. stub), la imagen igual se copia pero el status queda marcado en metadata del job.

## Recuperación

- Requests quedan en `inbox/*.json` hasta que VL las mueva a `*.done`.
- Responses en `outbox/{request_id}.json` son la fuente de verdad del resultado.
- Regenerar un beat no reescribe los demás (jobs por `request_id` / beat).
