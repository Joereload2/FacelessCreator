# Dominio

Este lenguaje describe el producto, no tablas. Solo se aprueban conceptos necesarios para el primer camino completo; las clases y el esquema se decidirán al implementar.

## Agregados y entidades aprobadas

### ContentProject

- **Propósito e identidad:** raíz de una producción horizontal, identificada por un ID estable.
- **Campos mínimos:** nombre, estado, resolución objetivo, referencias a versiones activas y receta, timestamps.
- **Estados:** Draft, Planning, Review, ReadyToRender, Rendering, Completed, Failed, Archived.
- **Relaciones:** posee versiones de guion, fuentes de audio, plan activo, trabajos y artefactos.
- **Invariantes:** un plan activo referencia inputs existentes y compatibles; un resultado completo conserva su manifiesto.
- **Propietario:** dominio de proyecto.
- **Mutabilidad/versionado:** metadata mutable; cambios significativos generan nuevas versiones de inputs o plan.
- **Persistencia:** metadata transaccional; bytes fuera de la base.

### ScriptVersion

Combina `ScriptDocument` y `ScriptVersion`: no se necesita una entidad separada hasta existir edición compleja.

- **Propósito e identidad:** snapshot inmutable de un guion estructurado.
- **Campos mínimos:** ID, número/fecha, contenido original o referencia, lista ordenada de bloques, hash.
- **Estados:** Draft, Valid, Superseded.
- **Relaciones:** contiene `NarrativeBlock`; es input de transcript y plan.
- **Invariantes:** orden estable, IDs de bloque estables dentro de la versión, hash verificable.
- **Propietario:** `ContentProject`.
- **Mutabilidad/versionado:** una versión validada no cambia; una edición crea otra.
- **Persistencia:** metadata y contenido normalizado; original preservado como input.

### NarrativeBlock

- **Propósito e identidad:** unidad narrativa con texto e instrucciones visuales; ID estable dentro de `ScriptVersion`.
- **Campos mínimos:** orden, texto narrado, intención/instrucción visual, notas temporales opcionales.
- **Estados:** Invalid, Ready, Timed, Resolved.
- **Relaciones:** obtiene tiempos y una o más selecciones visuales; puede contribuir a una escena.
- **Invariantes:** texto o intención explícita; orden no ambiguo; no presupone una imagen por frase.
- **Propietario:** `ScriptVersion`.
- **Mutabilidad:** inmutable dentro de una versión.
- **Persistencia:** embebido o relacionado según el diseño posterior.

### AudioAsset

Combina `AudioSource` y `AudioArtifact` mientras no exista generación de voz.

- **Propósito e identidad:** audio de narración importado o generado y validado.
- **Campos mínimos:** ID, origen, ruta administrada/referencia segura, hash, duración, formato, metadata técnica.
- **Estados:** Referenced, Validating, Valid, Invalid, Superseded.
- **Relaciones:** input de `TimedTranscript` y `RenderPlan`.
- **Invariantes:** un asset válido tiene hash, duración y formato comprobados.
- **Propietario:** `ContentProject`; el input original nunca se borra automáticamente.
- **Mutabilidad/versionado:** bytes inmutables; reemplazo crea otro asset.
- **Persistencia:** metadata transaccional y bytes en filesystem.

### TimedTranscript

- **Propósito e identidad:** alineación versionada entre el audio y los bloques del guion.
- **Campos mínimos:** ID, referencias exactas a guion/audio, intervalos ordenados, método, confianza/diagnósticos.
- **Estados:** Pending, Ready, NeedsReview, Failed, Superseded.
- **Relaciones:** asigna tiempos a bloques y alimenta escenas.
- **Invariantes:** intervalos no negativos, ordenados y dentro de la duración; procedencia completa.
- **Propietario:** servicio de planificación temporal.
- **Mutabilidad/versionado:** snapshot inmutable; corrección crea revisión.
- **Persistencia:** metadata estructurada.

### VisualSelection

Combina `VisualRequirement`, `VisualSelection` y `VisualAssetReference`: el requisito vive junto a la selección y la referencia es un value object.

- **Propósito e identidad:** resolución de una necesidad visual para uno o más bloques.
- **Campos mínimos:** ID, instrucciones, bloques cubiertos, referencia externa/local opaca, estado, encuadre y procedencia.
- **Estados:** Unresolved, Proposed, Selected, Rejected, Missing, Superseded.
- **Relaciones:** forma escenas y usa un contrato de catálogo visual.
- **Invariantes:** no accede a internals del proveedor; una selección activa es resoluble y compatible con la resolución.
- **Propietario:** `ContentProject`.
- **Mutabilidad/versionado:** reemplazar crea una revisión y conserva la anterior.
- **Persistencia:** metadata y referencia; una copia administrada solo cuando la política futura lo requiera.

### Scene

- **Propósito e identidad:** tramo audiovisual revisable que asocia intervalo, contenido narrativo y visual.
- **Campos mínimos:** ID estable, intervalo, bloques, selección visual, encuadre, transición opcional.
- **Estados:** Draft, Ready, NeedsReview, Invalid.
- **Relaciones:** ordenada dentro de `RenderPlan`; agrupa uno o más bloques.
- **Invariantes:** duración positiva, cobertura temporal definida, visual válido; las escenas no se solapan salvo regla explícita futura.
- **Propietario:** `RenderPlan`.
- **Mutabilidad/versionado:** inmutable dentro de un plan; una corrección crea nueva revisión del plan.
- **Persistencia:** parte estructurada del plan.

### RenderPlan

`TimelineItem` y `Transition` no son entidades raíz: se modelan inicialmente como `Scene` y value objects.

- **Propósito e identidad:** snapshot ejecutable y reproducible del montaje.
- **Campos mínimos:** ID/versión, inputs con hashes/versiones, resolución, escenas ordenadas, audio, receta, duración, timestamps.
- **Estados:** Draft, Valid, NeedsReview, Approved, Superseded.
- **Relaciones:** referencia guion, audio, transcript, selecciones y `ProductionRecipe`; crea artifacts mediante jobs.
- **Invariantes:** cobertura coherente, inputs resolubles, configuración completa y validación antes de render.
- **Propietario:** dominio de planificación.
- **Mutabilidad/versionado:** inmutable tras validación; cambios crean versión.
- **Persistencia:** snapshot estructurado y manifiesto exportable.

### ProductionRecipe

- **Propósito e identidad:** configuración versionada que hace determinista la transformación.
- **Campos mínimos:** resolución, frame rate, reglas de ajuste, transiciones permitidas, parámetros de exportación y versiones de adaptadores.
- **Estados:** Draft, Valid, Superseded.
- **Relaciones:** referenciada por `RenderPlan` y jobs.
- **Invariantes:** valores completos y soportados; no contiene secretos.
- **Propietario:** configuración de aplicación/proyecto.
- **Mutabilidad/versionado:** versionada e inmutable cuando se usa.
- **Persistencia:** metadata estructurada.

### Job

- **Propósito e identidad:** ejecución durable e idempotente de una etapa larga.
- **Campos mínimos:** ID, tipo, estado, inputs/versiones, progreso, intentos, timestamps, error y outputs.
- **Estados:** Queued, Running, CancelRequested, Cancelled, Succeeded, Failed, Interrupted.
- **Relaciones:** consume snapshots y produce `Artifact`.
- **Invariantes:** persistido antes de ejecutar; transición válida; éxito solo con outputs validados.
- **Propietario:** subsistema de jobs.
- **Mutabilidad/versionado:** estado mutable mediante transiciones; inputs inmutables.
- **Persistencia:** transaccional.

### Artifact

`HorizontalArtifact` y `SubtitleArtifact` son tipos de Artifact, no entidades separadas.

- **Propósito e identidad:** resultado verificable de una etapa.
- **Campos mínimos:** ID, tipo, ruta segura, hash, tamaño, metadata técnica, procedencia, estado.
- **Estados:** Temporary, Validating, Ready, Invalid, Superseded, Deleted.
- **Relaciones:** producido por Job y referenciado por proyecto/plan.
- **Invariantes:** `Ready` implica archivo existente y validado; publicación atómica; no sobrescribe inputs.
- **Propietario:** workspace administrado.
- **Mutabilidad/versionado:** bytes inmutables; ciclo de vida explícito.
- **Persistencia:** metadata transaccional y archivo.

### ReviewDecision

- **Propósito e identidad:** registro de aprobación, rechazo o corrección humana sobre una versión concreta.
- **Campos mínimos:** ID, target y versión, decisión, motivo opcional, timestamp.
- **Estados:** Accepted, Rejected, ReplacementRequested.
- **Relaciones:** afecta plan o selección y puede disparar una nueva versión.
- **Invariantes:** nunca modifica silenciosamente el target revisado.
- **Propietario:** `ContentProject`.
- **Mutabilidad/versionado:** inmutable y append-only.
- **Persistencia:** metadata transaccional.

## Conceptos pospuestos

Proveedor de voz, solicitud de generación, modelo de IA, composición de overlays, subtítulo quemado, caché de segmentos y entidades específicas de Visual Library. Se introducirán solo con un flujo aprobado.
