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
- **Decisión:** FacelessCreator dependerá de un puerto de grano grueso. El MVP prepara y prueba el contrato con un adaptador controlado; la integración real se evalúa después.
- **Alternativas:** Acceso directo a sus tablas; incluir Visual Library dentro de FacelessCreator; integrar desde Foundation 0.
- **Consecuencias:** Desacoplamiento y pruebas simples; queda una incógnita hasta conocer su API real.

## F0-004 — Plan audiovisual reproducible y trazable

- **Estado:** Accepted
- **Contexto:** Un resultado debe poder explicarse, recuperarse y regenerarse.
- **Decisión:** El `RenderPlan` versionado referencia versiones de guion, audio, visuales, tiempos, receta y trabajo creador.
- **Alternativas:** Construir comandos multimedia directamente desde la UI; guardar solo el archivo final.
- **Consecuencias:** Se requiere manifestación explícita y validación de inputs, pero se habilitan recuperación y diagnóstico.

## F0-005 — Jobs persistidos y UI no propietaria

- **Estado:** Accepted
- **Contexto:** Sincronización, preview y render pueden durar más que una sesión de UI.
- **Decisión:** Los trabajos se persisten antes de ejecutarse y se recuperan independientemente de la UI.
- **Alternativas:** Promesas o procesos efímeros ligados a una pantalla.
- **Consecuencias:** Aparecen estados, idempotencia y recovery como requisitos tempranos.

## F0-006 — Recalcular desde la etapa afectada

- **Estado:** Accepted
- **Contexto:** Una corrección puntual no debe repetir trabajo anterior válido.
- **Decisión:** Cada etapa tendrá inputs versionados y artefactos verificables; al cambiar algo se invalida desde la primera dependencia afectada, no todo el proyecto.
- **Alternativas:** Render completo siempre; caché por fragmentos desde el inicio.
- **Consecuencias:** El MVP evita repetir etapas; optimizar fragmentos internos del render queda pospuesto.

## F0-007 — Resolución fija del proyecto

- **Estado:** Accepted
- **Contexto:** Las imágenes serán creadas para el tamaño de salida y no deberían incumplirlo.
- **Decisión:** Un proyecto usa una resolución horizontal fija y valida sus imágenes contra ella.
- **Alternativas:** Resolución dinámica por imagen; escalado silencioso sin regla.
- **Consecuencias:** Salida consistente. El valor exacto se decidirá tras revisar fixtures y la prueba multimedia.

## F0-008 — Selección tecnológica después de una prueba

- **Estado:** Accepted
- **Contexto:** El repositorio está vacío y no existe evidencia para elegir Rust, Python, Tauri, Electron o una combinación.
- **Decisión:** Foundation 0 fija responsabilidades y criterios; Milestone 1 compara la mínima combinación viable mediante una prueba multimedia y un shell de aplicación.
- **Alternativas:** Elegir ahora por preferencia; copiar otro proyecto.
- **Consecuencias:** Se evita lock-in prematuro; Milestone 1 debe cerrar la decisión con una ADR.

## F0-009 — Autoridad documental única con lectura por área

- **Estado:** Accepted
- **Contexto:** Una IA debe leer solo el contexto relevante, sin crear normas duplicadas.
- **Decisión:** Los documentos de Foundation 0 son autoridades transversales. Los documentos futuros se agruparán dentro de `docs/` por etapa o área y enlazarán a la autoridad, sin copiarla. `00-START-HERE.md` ofrece rutas de lectura.
- **Alternativas:** Un documento gigante; copias independientes por frontend/backend; ausencia de jerarquía.
- **Consecuencias:** Menor contexto por tarea y menor riesgo de divergencia; las fronteras cruzadas exigen leer más de un área.

## F0-010 — Estrategia conceptual de persistencia

- **Estado:** Accepted
- **Contexto:** Se necesitan metadata transaccional y artefactos multimedia grandes.
- **Decisión:** Tratar SQLite como opción por defecto suficiente para metadata y filesystem para bytes, sujetos a validación en Milestone 2. No se diseña aún el esquema.
- **Alternativas:** Solo archivos JSON; base de datos cliente-servidor; blobs en SQLite.
- **Consecuencias:** Favorece operación local simple y atomicidad; requiere coordinar referencias, hashes y limpieza.

## F0-011 — Contratos gruesos y arquitectura sin microservicios

- **Estado:** Accepted
- **Contexto:** Es una aplicación local para una persona con procesamiento multimedia.
- **Decisión:** Usar módulos dentro de una aplicación desplegable, dirección de dependencias hacia dominio y contratos de grano grueso para procesos y proveedores.
- **Alternativas:** Microservicios; llamadas finas desde UI a herramientas externas.
- **Consecuencias:** Desarrollo y recuperación más simples; los módulos mantienen fronteras comprobables.

## F0-012 — Preview mediante archivo temporal

- **Estado:** Accepted
- **Contexto:** El primer preview no necesita reproducción embebida.
- **Decisión:** Generar un archivo temporal validado y abrirlo con un reproductor externo mediante una acción explícita.
- **Alternativas:** Player embebido; preview solo estático.
- **Consecuencias:** Reduce riesgo del primer camino vertical; la experiencia depende parcialmente del reproductor del sistema.
