# Playbook para IA

## 1. Definition of Ready

Antes de implementar debe existir: objetivo, alcance, no objetivos, criterios de aceptación, riesgo, capas afectadas, documentos aplicables, pruebas obligatorias y punto de detención. Para LOW basta una versión breve. Si una ausencia puede cambiar producto, dominio, datos o arquitectura, detenerse.

Foundation 0 aprobado autoriza avanzar según `IMPLEMENTATION_PLAN.md` hasta una interfaz operativa, usando pausas internas para analizar y validar. No autoriza ampliar alcance ni ocultar decisiones.

## 2. Task Card

Mostrar antes de cambiar archivos:

- nombre y objetivo;
- alcance y no objetivos;
- riesgo y capas;
- archivos previstos;
- pruebas y restricciones;
- punto de detención.

## 3. Riesgo

- **LOW:** cambio local, reversible, sin contrato/persistencia/flujo ni dependencia nueva.
- **MEDIUM:** un módulo o flujo conocido, contrato compatible, migración aditiva o integración interna acotada.
- **HIGH:** datos durables, seguridad, multimedia, recovery, proveedor externo, UX principal o varias capas coordinadas.
- **ARCHITECTURE:** cambia fronteras, autoridad, tecnología base, contrato externo, modelo central o estrategia de persistencia.

Ante duda, usar el nivel mayor.

## 4. STOP Rules

Detener la implementación y documentar cuando el requerimiento ambiguo afecta producto; requiere cambiar arquitectura; contradice una decisión Accepted; exige dependencia importante; implica migración destructiva; afecta tres o más capas principales y puede dividirse; carece de criterios de aceptación; enviaría datos a un servicio no aprobado; requiere secretos ausentes; descubre pérdida/corrupción potencial; o aparecen más de tres decisiones nuevas de producto.

Si existe una alternativa segura dentro de alcance, puede avanzarse en trabajo independiente sin asumir la decisión bloqueada.

## 5. Orden por vertical slice

Producto → Dominio → Persistencia → Jobs → Backend/Application → API/Bridge → Frontend → UX/UI → QA → refactorización limitada.

Aplicar el orden al slice pequeño que entrega valor. No construir capas globales por anticipado ni una UI que invente el dominio.

## 6. Tamaño de tareas

Dividir si afecta tres o más capas separables, varios módulos independientes, mezcla infraestructura/feature/refactor, o crece de forma material. Cohesión, reversibilidad y riesgo importan más que líneas de código.

## 7. Dos loops

Después de implementar:

1. **Corrección:** buscar y corregir errores, estados incompletos, violaciones, regresiones y riesgos.
2. **Simplificación:** eliminar duplicación introducida, mejorar nombres y reducir pasos/complejidad sin rediseñar el sistema.

No añadir una tercera auditoría ceremonial; las pruebas normales no cuentan como loop.

## 8. Revisión por roles

HIGH y ARCHITECTURE se revisan desde PM/PO, UX/UI, Frontend, Backend, Multimedia, QA, Seguridad y Arquitectura. Cada rol registra bloqueo, problema, riesgo, mejora pequeña y aprobación/rechazo; puede declarar “no aplica” con motivo. LOW/MEDIUM usan solo roles afectados. El resultado es una sola decisión coherente.

## 9. Git

Por defecto no commit, push, rebase, reset destructivo ni limpieza ajena. Tras la aprobación de Foundation 0, los commits pueden agrupar funcionalidades completas y funcionando; hasta aclarar autorización permanente, cada commit se solicita explícitamente. El push queda prohibido hasta que la interfaz esté operativa y funcional, momento en que debe verificarse y anunciarse antes de publicar.

## 10. Entrega

Mostrar resumen, archivos modificados, pruebas ejecutadas, omitidas y motivo, fallos, riesgos, capturas si existe UI, migraciones, resultado de `git diff --check`, `git status`, estado de commit/push y siguiente punto de control. No afirmar éxito con pruebas fallidas u omitidas sin explicación.

## Rutas de lectura mínima

- **Producto/flujo:** `PRODUCT.md`, `DOMAIN.md`, `WORKFLOWS.md`, decisiones aplicables.
- **Backend/datos/jobs:** `ARCHITECTURE.md`, `DOMAIN.md`, `constitution/ENGINEERING.md`, `constitution/SECURITY.md`, `constitution/TESTING.md`.
- **Frontend/UX:** `PRODUCT.md`, contrato relevante de `ARCHITECTURE.md`, `constitution/UX_UI.md`, testing aplicable.
- **Multimedia:** `ARCHITECTURE.md`, plan/artefactos de `DOMAIN.md`, Engineering, Security y Testing.
- **QA:** flujo afectado, `constitution/TESTING.md` y `constitution/DONE.md`.

Leer además `PROJECT_STATUS.md` y ADRs aplicables. Los documentos futuros por área deben tener un índice propio y enlazar, no copiar, estas reglas.
