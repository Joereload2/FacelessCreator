# FacelessCreator — Inicio

FacelessCreator será una aplicación local para ensamblar videos horizontales faceless a partir de un guion estructurado, audio, referencias visuales y reglas temporales. Su modelo es una fábrica supervisada: produce un resultado completo y pide intervención solo ante excepciones.

## Estado actual

Foundation 0 en revisión. El repositorio no contiene producto, stack, infraestructura ni pruebas. Solo existen la documentación de esta fase, `README.md` y `.gitignore`.

La siguiente fase permitida, tras aprobación humana explícita, es Milestone 1: scaffold mínimo y prueba multimedia. Foundation 0 no autoriza implementar producto.

## Autoridades y orden de lectura

1. [DECISIONS.md](DECISIONS.md): decisiones aceptadas y reemplazadas.
2. [PRODUCT.md](PRODUCT.md): producto, alcance y prioridades.
3. [ARCHITECTURE.md](ARCHITECTURE.md): módulos y fronteras.
4. [DOMAIN.md](DOMAIN.md): lenguaje y reglas del dominio.
5. [AI_PLAYBOOK.md](AI_PLAYBOOK.md): proceso obligatorio para IA.
6. [Constituciones](constitution/): normas obligatorias de ingeniería, UX/UI, pruebas, seguridad y terminado.
7. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): secuencia aprobable.
8. [PROJECT_STATUS.md](PROJECT_STATUS.md): fotografía no normativa.

[WORKFLOWS.md](WORKFLOWS.md) concreta los recorridos del producto bajo esas autoridades. Ante conflicto se corrige el documento de menor autoridad o se registra una decisión.

## Cómo iniciar una tarea

Leer este archivo, `PROJECT_STATUS.md`, la autoridad del área afectada y su constitución. Después aplicar Definition of Ready y mostrar la Task Card de `AI_PLAYBOOK.md`. No es necesario cargar documentación de áreas ajenas si la tarea no cruza sus fronteras.

## Documentos que aún no existen

No existen especificaciones de API, esquema SQL, contratos de proveedores, runbooks, diseño visual detallado ni documentación de frontend/backend implementados. Se crearán dentro de `docs/` y agrupados por etapa o área solo cuando una tarea aprobada los necesite; deberán enlazar a estas autoridades sin repetirlas.
