# Arquitectura

Foundation 0 fija responsabilidades y dependencias, no un stack definitivo.

## Contexto

```text
Persona usuaria
      |
      v
FacelessCreator local ---- contrato visual ----> Visual Library (independiente, futuro)
      |          |
      |          +---- contrato de voz -------> proveedor aprobado (futuro)
      |
      +---- adaptador multimedia -------------> herramienta local, por validar
      |
      +---- workspace administrado + metadata local

Salida: preview temporal, MP4 horizontal, SRT y manifiesto
```

VigilCut consume resultados posteriormente mediante una frontera futura; no forma parte de este sistema.

## Módulos y responsabilidades

- **Project:** ciclo de vida, configuración y versiones activas.
- **Script:** importación, normalización y validación de bloques.
- **Timing:** validación de audio y alineación temporal.
- **Visual Resolution:** necesidades, consultas por contrato, selecciones y reemplazos.
- **Planning:** escenas, receta y `RenderPlan` reproducible.
- **Jobs:** cola durable, progreso, cancelación, retry y recovery.
- **Artifacts:** rutas, hashes, validación, publicación atómica y manifiestos.
- **Multimedia:** frontera gruesa para probe, preview, render y validación.
- **Application:** casos de uso que coordinan módulos y transacciones.
- **API/Bridge:** contratos tipados y gruesos entre UI y aplicación.
- **Frontend:** estaciones de flujo, snapshots, comandos explícitos y preview externo.

## Capas y dirección de dependencias

```text
UI -> API/Bridge -> Application -> Domain
                         |           ^
                         v           |
                 Ports / contracts --+
                         |
           Adapters: persistence, filesystem,
           multimedia, visual library, voice
```

Dominio no conoce UI, framework, DB, filesystem ni proveedores. Adaptadores dependen de puertos internos. No hay llamadas directas desde UI a FFmpeg, DB o Visual Library.

## Fuentes de verdad

- Metadata y estado durable: repositorio transaccional local.
- Bytes: workspace administrado.
- Inputs y planes: versiones/hashes referenciados, no estado efímero de UI.
- Eventos y progreso en memoria: proyecciones; nunca autoridad.
- Artifacts: Ready solo cuando metadata y archivo validado coinciden.

## Almacenamiento de archivos

Una raíz administrada contendrá proyectos, inputs copiados o referenciados según política, temporales y outputs en namespaces separados. Rutas normalizadas, IDs internos y allowlists evitan traversal. Se valida que el destino permanezca en el workspace y no sea symlink/reparse point inesperado. Escritura a temporal en el mismo volumen, validación y rename atómico cuando el sistema lo permita. Nunca se sobrescribe ni elimina un input automáticamente.

La topología exacta y si se admiten varias raíces quedan para Milestone 2.

## Jobs, invalidación y recuperación

Un job se persiste con un snapshot de inputs antes de ejecutar. Estados y transiciones se definen en [DOMAIN.md](DOMAIN.md). La clave idempotente deriva del tipo, inputs versionados y receta. Cambiar un input invalida la etapa que lo consume y sus descendientes; no sus antecesores. El primer MVP reutiliza artefactos de etapas completas, sin exigir render parcial por segmentos.

Al iniciar, un reconciliador detecta ejecuciones huérfanas, valida outputs y decide finalizar, marcar Interrupted o permitir retry. Las operaciones cobrables nunca se reintentan sin reconciliación o confirmación.

## Artifacts y contratos externos

Los adapters reciben solicitudes de grano grueso y devuelven resultados estructurados, diagnósticos y procedencia. Los contratos se versionan. Ningún proveedor recibe datos sin aprobación documentada.

- **Visual Library:** consulta por intención y restricciones; devuelve referencias opacas y metadata pública. Sin acceso a tablas. En MVP se valida el puerto con fake/adaptador controlado.
- **Voz:** generar una narración a partir de input aprobado; proveedor y contrato concreto pospuestos.
- **Multimedia:** probe, crear preview, renderizar plan y validar salida. FFmpeg es candidato, no decisión en Foundation 0.

## Frontend y backend local

“Backend” significa application/domain y workers locales, no un servidor cloud. La frontera con frontend puede ser IPC o API local según el shell elegido. Comandos explícitos inician trabajos; consultas devuelven snapshots reconstruibles. La UI puede cerrarse sin cancelar jobs salvo orden explícita.

## Estrategia local-first

Operación principal sin cloud. Solo adaptadores aprobados pueden usar red. Configuración, proyecto, historial y artifacts permanecen locales. Secretos usan almacenamiento seguro del OS.

## Opciones tecnológicas a validar

| Opción | Ventaja | Riesgo | Evidencia requerida |
|---|---|---|---|
| Rust + Tauri | binario compacto, seguridad y control de procesos | mayor coste inicial y ecosistema multimedia/IA menos directo | shell, jobs y proceso multimedia en Windows |
| Python + shell web | velocidad para multimedia/IA | empaquetado, procesos y distribución local | build reproducible y UI robusta |
| Híbrido | usar cada lenguaje donde aporta | complejidad de frontera y empaquetado | beneficio medido que justifique dos runtimes |
| Electron | ecosistema UI maduro | tamaño y consumo | ventaja real frente a Tauri para preview/jobs |

SQLite es el candidato inicial para metadata y filesystem para bytes. Milestone 1 decide shell/runtime y herramienta multimedia; Milestone 2 valida persistencia. Compatibilidad futura con macOS/Linux se conserva evitando rutas y procesos específicos fuera de adapters, pero Windows es la plataforma de validación inicial inferida del entorno actual.
