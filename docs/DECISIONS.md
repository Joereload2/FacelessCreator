# Registro de decisiones

Formato: ID, título, estado, contexto, decisión, alternativas y consecuencias. Las decisiones no se borran; una nueva decisión puede marcarlas como `Superseded`.

## F0-001 — Aplicación local para una persona

- **Estado:** Accepted
- **Contexto:** El valor está en el contenido producido, no en vender software ni coordinar usuarios.
- **Decisión:** FacelessCreator será local-first, independiente y de usuario único.
- **Alternativas:** SaaS; plataforma distribuida; aplicación multiusuario.
- **Consecuencias:** Menor complejidad operativa; cloud y colaboración quedan fuera del alcance.

## F0-002 — Fábrica supervisada, no editor generalista

- **Estado:** Accepted
- **Contexto:** El trabajo manual debe limitarse a revisar y corregir excepciones.
- **Decisión:** La unidad de interacción es un flujo de producción con preview y correcciones puntuales, no una línea de tiempo arbitraria.
- **Alternativas:** Editor tradicional; automatización sin revisión.
- **Consecuencias:** Menor flexibilidad creativa a cambio de velocidad, consistencia y una UI enfocada.

## F0-003 — Visual Library mediante contrato independiente

- **Estado:** Accepted
- **Contexto:** Visual Library es una aplicación separada y no debe compartir internals.
- **Decisión:** FacelessCreator depende de un puerto grueso. El MVP prueba el contrato con un adapter controlado; la integración real se evalúa después.
- **Alternativas:** Acceso directo a tablas; incluir Visual Library; integración inmediata.
- **Consecuencias:** Desacoplamiento y pruebas simples; queda una incógnita hasta conocer su API.

## F0-004 — Plan audiovisual reproducible y trazable

- **Estado:** Accepted
- **Contexto:** Un resultado debe poder explicarse, recuperarse y regenerarse.
- **Decisión:** El `RenderPlan` versionado referencia guion, audio, visuales, tiempos, receta y trabajo creador.
- **Alternativas:** Comandos desde UI; guardar solo el archivo final.
- **Consecuencias:** Se requieren snapshots e inputs verificables, habilitando recuperación y diagnóstico.

## F0-005 — Jobs persistidos y UI no propietaria

- **Estado:** Accepted
- **Contexto:** Sincronización, preview y render duran más que una interacción.
- **Decisión:** Los trabajos se persisten antes de ejecutar y se recuperan independientemente de UI.
- **Alternativas:** Procesos efímeros ligados a pantalla.
- **Consecuencias:** Estados, idempotencia y recovery son requisitos tempranos.

## F0-006 — Recalcular desde la etapa afectada

- **Estado:** Accepted
- **Contexto:** Una corrección puntual no debe repetir trabajo válido.
- **Decisión:** Invalidar desde la primera dependencia afectada, no todo el proyecto.
- **Alternativas:** Render completo siempre; caché por fragmentos inicial.
- **Consecuencias:** El MVP reutiliza etapas; render parcial interno queda pospuesto.

## F0-007 — Resolución fija del proyecto

- **Estado:** Accepted
- **Contexto:** Las imágenes serán creadas para el tamaño de salida.
- **Decisión:** Un proyecto usa resolución horizontal fija y valida imágenes contra ella.
- **Alternativas:** Resolución dinámica; escalado silencioso.
- **Consecuencias:** Salida consistente. La implementación inicial usa 1920×1080.

## F0-008 — Selección tecnológica después de una prueba

- **Estado:** Accepted
- **Contexto:** El repositorio inicial no ofrecía evidencia tecnológica.
- **Decisión:** Foundation 0 fijó responsabilidades y M1 cerró stack con una prueba multimedia.
- **Alternativas:** Elegir por preferencia; copiar otro proyecto.
- **Consecuencias:** La decisión concreta está en M1-001.

## F0-009 — Autoridad documental única con lectura por área

- **Estado:** Accepted
- **Contexto:** Una IA debe leer contexto relevante sin normas duplicadas.
- **Decisión:** Foundation 0 conserva autoridades transversales; implementación se documenta bajo `docs/areas/` enlazándolas.
- **Alternativas:** Documento gigante; copias por frontend/backend; ausencia de jerarquía.
- **Consecuencias:** Menos contexto y menor divergencia; tareas cruzadas leen ambas áreas.

## F0-010 — SQLite para metadata y filesystem para bytes

- **Estado:** Accepted
- **Contexto:** Se necesitan metadata transaccional y artifacts grandes.
- **Decisión:** SQLite guarda estado y filesystem guarda bytes con hashes y rutas confinadas.
- **Alternativas:** JSON; DB servidor; blobs SQLite.
- **Consecuencias:** Operación simple; se coordina consistencia por snapshots y publicación atómica.

## F0-011 — Contratos gruesos y arquitectura sin microservicios

- **Estado:** Accepted
- **Contexto:** Aplicación local para una persona con multimedia.
- **Decisión:** Módulos en una aplicación desplegable y ports/adapters de grano grueso.
- **Alternativas:** Microservicios; llamadas finas desde UI.
- **Consecuencias:** Desarrollo y recuperación simples con fronteras comprobables.

## F0-012 — Preview mediante archivo temporal

- **Estado:** Accepted
- **Contexto:** La primera versión no depende de un editor audiovisual embebido.
- **Decisión:** Crear archivo temporal validado, reproducible en UI y abrible externamente.
- **Alternativas:** Player complejo; preview estático.
- **Consecuencias:** Menor riesgo con revisión audiovisual real.

## F0-013 — Ejecución autónoma hasta interfaz operativa

- **Estado:** Accepted
- **Contexto:** Revisiones humanas entre cada milestone reducirían eficiencia.
- **Decisión:** Tras aprobar Foundation 0, continuar hasta M7 salvo STOP Rule; no hacer push antes de una interfaz operativa.
- **Alternativas:** Revisión entre milestones; avance sin controles técnicos.
- **Consecuencias:** Autonomía limitada por pruebas, Task Cards y loops.

## M1-001 — Python estándar, frontend web local y FFmpeg

- **Estado:** Accepted
- **Contexto:** Python 3.12 y FFmpeg 8.1 estaban disponibles; Node tenía wrappers PowerShell restringidos y Rust aumentaba el coste del primer slice.
- **Decisión:** Aplicación Python sin dependencias, SQLite, HTTP loopback, frontend HTML/CSS/JS y adapter FFmpeg. Windows valida primero; adapters preservan portabilidad.
- **Alternativas:** Rust/Tauri; Electron; híbrido.
- **Consecuencias:** Inicio rápido y cero dependencias de aplicación; la UI usa navegador local y el empaquetado nativo se reevalúa después de uso real.

## M1-002 — Parámetros audiovisuales iniciales

- **Estado:** Accepted
- **Contexto:** Se necesitaba una salida fija verificable para la interfaz.
- **Decisión:** 1920×1080, 30 fps, MP4 H.264/yuv420p, AAC 192 kbps y `faststart`; imágenes cubren y recortan al centro si incumplen.
- **Alternativas:** 4K inicial; resolución dinámica; codecs dependientes de hardware.
- **Consecuencias:** Compatibilidad y render rápido. 4K puede adoptarse por proyecto después de fixtures reales y medición.
