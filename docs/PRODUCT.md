# Producto

## 1. Visión

FacelessCreator es una estación local de ensamblaje audiovisual automatizada y supervisable. Convierte entradas estructuradas en un primer video horizontal completo, reproducible y trazable, para que el usuario corrija excepciones en vez de editar manualmente una línea de tiempo generalista.

## 2. Usuario principal

Una sola persona opera una fábrica de canales faceless. El producto no se vende, no gestiona clientes y no necesita colaboración multiusuario.

## 3. Problema

Producir videos horizontales exige coordinar guion, narración, imágenes, tiempos, revisión y exportación. La coordinación manual es lenta, repetitiva y difícil de reproducir. FacelessCreator debe automatizar ese ensamblaje sin ocultar su trazabilidad.

## 4. Jobs to Be Done

- Obtener rápidamente un montaje completo a partir de insumos preparados.
- Entender qué está haciendo el sistema y qué excepciones requieren atención.
- Sustituir una imagen, encuadre, duración o transición sin repetir etapas anteriores válidas.
- Recuperar un proyecto y sus trabajos después de interrupciones.
- Exportar un video y sus artefactos asociados con procedencia verificable.

## 5. Entradas

- Guion estructurado en bloques narrativos con instrucciones sobre las imágenes que deben proyectarse. La sintaxis queda abierta hasta disponer de ejemplos reales.
- Audio existente o, en una fase posterior, texto destinado a un proveedor de voz.
- Referencias visuales resueltas mediante un contrato de biblioteca visual. En el primer MVP se prepara y prueba el contrato; la conexión real con Visual Library se pospone.
- Configuración del proyecto y reglas temporales.

## 6. Salidas

- `RenderPlan` reproducible.
- Preview como archivo temporal reproducible externamente.
- Video horizontal en resolución fija por proyecto; la resolución exacta queda pendiente de validar contra las imágenes fuente y la prueba multimedia.
- SRT opcional.
- Metadata y manifiesto de trazabilidad.
- Diagnósticos y estado recuperable del trabajo.

## 7. Flujos principales

1. Guion y audio existentes hasta video terminado.
2. Generación de audio desde texto, pospuesta fuera del primer MVP.
3. Reemplazo puntual de una imagen y regeneración desde la etapa afectada.
4. Recuperación después de cierre normal, cierre forzado, fallo multimedia o reinicio.

Los detalles normativos están en [WORKFLOWS.md](WORKFLOWS.md).

## 8. Primer MVP

El MVP acepta un guion estructurado y audio existente, resuelve referencias visuales a través de un contrato probado con un adaptador controlado, construye un `RenderPlan`, genera preview temporal, permite revisar y reemplazar imágenes, exporta video horizontal y SRT opcional, y conserva trazabilidad y recuperación. Incluye la frontera preparada para Visual Library, no su integración real. No incluye generación de voz.

## 9. Criterios de éxito

- Un fixture representativo recorre el flujo completo sin edición audiovisual externa, salvo abrir el preview temporal.
- El usuario puede identificar y corregir una selección visual incorrecta.
- Rehacer una corrección no repite sincronización ni resolución ya válidas.
- El video, SRT y manifiesto son válidos y trazables a sus entradas.
- Un proyecto interrumpido se recupera hasta el último estado persistido consistente.
- El sistema comunica estado, fallo y siguiente acción sin exponer entidades técnicas innecesarias.

No se fijan métricas de tiempo o calidad sin una línea base medible.

## 10. Prioridades

1. Camino completo a un video real.
2. Reproducibilidad y recuperación.
3. Supervisión y corrección de excepciones.
4. Integraciones externas.
5. Automatización avanzada.

## 11. No objetivos

Editor generalista, reemplazo de Premiere, motion graphics arbitrario, edición manual compleja, SaaS, cloud obligatorio, portal de clientes, colaboración multiusuario, Shorts y acceso directo a tablas de Visual Library.

## 12. Funciones pospuestas

- Integración real con Visual Library.
- ElevenLabs u otro proveedor de voz.
- Selección definitiva de proveedor de IA.
- Subtítulos quemados y overlays complejos.
- Recuperación avanzada y optimizaciones de render por segmentos.
- Integración con VigilCut o aplicaciones de Shorts.

## 13. Supuestos

- Las imágenes se producirán para una resolución objetivo fija y deberán cumplirla.
- Una imagen puede cubrir varias frases; los cambios dependen del contenido, no de un intervalo universal.
- Las imágenes normalmente ocupan pantalla completa.
- La UI supervisa trabajos persistidos; no los posee.
- Existe una única persona usuaria y una raíz de trabajo local administrada por la aplicación puede contener varios proyectos. Este último detalle requiere confirmación durante el diseño de persistencia.

## 14. Preguntas abiertas

- Resolución, frame rate, codecs y límites exactos de exportación.
- Sintaxis del guion estructurado y ejemplos representativos.
- Contrato concreto que Visual Library podrá ofrecer.
- Estrategia provisional para resolver imágenes antes de esa integración.
- Ubicación y política exacta de la raíz de trabajo.
- Umbrales verificables de rapidez y calidad.
