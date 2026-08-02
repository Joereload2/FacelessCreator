# Flujos de trabajo

Las etapas persisten su estado. Un fallo no invalida etapas anteriores cuyos inputs no cambiaron.

## Flujo A — Guion y audio existentes

- **Entrada:** guion estructurado válido, audio existente válido, receta y acceso al contrato visual mediante adaptador controlado.
- **Estado inicial:** proyecto Draft con inputs importados y hashes calculados.
- **Automático:** validar; sincronizar bloques con audio; formular necesidades visuales; resolver referencias; agrupar escenas; construir y validar `RenderPlan`; generar preview temporal; tras aprobación, renderizar, validar y manifestar.
- **Humano:** revisar bloques dudosos y preview; corregir excepciones; aprobar render.
- **Fallos:** formato inválido, desalineación, visual ausente, plan incoherente, falta de espacio o fallo multimedia.
- **Recuperación:** conservar último snapshot válido; reintentar desde la primera etapa fallida o invalidada.
- **Salida:** video horizontal válido, SRT opcional, plan y manifiesto.
- **Terminado:** artefactos validan formato/duración, trazabilidad completa y proyecto recuperable.

## Flujo B — Generar audio (pospuesto)

- **Entrada:** guion válido, configuración y consentimiento explícito para el proveedor aprobado.
- **Estado inicial:** proyecto con ScriptVersion activa.
- **Automático:** crear job idempotente; enviar solo datos aprobados; recibir, almacenar y validar audio; alinear; continuar por resolución visual y render.
- **Humano:** aprobar proveedor/coste y revisar pronunciación o fallo.
- **Fallos:** secreto ausente, coste no permitido, red, límite, contenido rechazado o audio inválido.
- **Recuperación:** no duplicar solicitudes cobrables; reconciliar estado del proveedor cuando sea posible.
- **Salida:** AudioAsset trazable y flujo A continuable.
- **Terminado:** audio validado, coste/procedencia registrados sin secretos y ninguna solicitud ambigua.

## Flujo C — Reemplazar una imagen

- **Entrada:** proyecto con `RenderPlan`, escena seleccionada y alternativa resoluble.
- **Estado inicial:** WaitingReview o Completed.
- **Automático:** consultar alternativas por contrato; validar referencia y resolución; crear nueva selección y revisión del plan; invalidar preview/render y pasos posteriores, no transcript ni resolución ajena; generar nuevo preview.
- **Humano:** seleccionar alternativa, ajustar encuadre si procede y aprobar.
- **Fallos:** sin resultados, referencia perdida, dimensiones incompatibles o generación de preview fallida.
- **Recuperación:** conservar plan y artefactos anteriores hasta publicar correctamente la revisión.
- **Salida:** plan revisado, preview y posteriormente video revisado.
- **Terminado:** selección visible, plan válido, procedencia preservada y etapas previas no repetidas.

## Flujo D — Recuperación

- **Entrada:** estado persistido después de cierre normal, cierre forzado, fallo de proceso o reinicio.
- **Estado inicial:** proyecto y jobs leídos desde almacenamiento; filesystem reconciliado sin borrar.
- **Automático:** detectar jobs Running huérfanos; verificar inputs, temporales y outputs; marcar Interrupted o finalizar si el output ya es válido; ofrecer/reintentar solo operaciones idempotentes; limpiar temporales propios cuando sea seguro.
- **Humano:** decidir ante input externo ausente, output ambiguo, corrupción o reintento con coste.
- **Fallos:** DB ilegible, archivo perdido, hash distinto, espacio insuficiente o permisos.
- **Recuperación:** backup antes de reparación destructiva; diagnóstico accionable; nunca borrar inputs.
- **Salida:** estado consistente y siguiente acción explícita.
- **Terminado:** ningún job queda falsamente Running y todo artifact Ready existe y valida.
