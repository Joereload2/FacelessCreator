# Constitución de seguridad y privacidad

- Local-first: no enviar guiones, audios, imágenes, videos o metadata fuera del equipo sin aprobación explícita y proveedor documentado.
- Guardar secretos en el almacenamiento seguro del OS; nunca en SQLite, JSON, manifiestos, logs, código o fixtures.
- Documentar por proveedor datos enviados, finalidad, retención, coste y mecanismo de eliminación.
- Tratar coste desconocido como riesgo, no como cero.
- Normalizar y confinar rutas al workspace; rechazar traversal, rutas reservadas y destinos inesperados.
- Detectar symlinks, junctions y reparse points antes de operaciones recursivas; no atravesarlos implícitamente.
- No sobrescribir archivos existentes sin una política explícita y una acción confirmada.
- No borrar inputs automáticamente; eliminación y retención son acciones explícitas y auditables.
- Limitar limpieza a temporales propios con identidad, tipo y raíz verificados.
- Minimizar logs; excluir secretos y contenido de guiones o media salvo diagnóstico consentido.
- Validar formatos, tamaños y metadata antes de consumir archivos; no confiar en extensión.
- Ejecutar procesos externos con argumentos estructurados, límites y directorio controlado; no interpolar entradas en shell.
- Hacer backups antes de cambios destructivos y comprobar que pueden localizarse.
