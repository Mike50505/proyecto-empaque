# API, despliegue y decisiones pendientes

La SPA y Django se sirven bajo un mismo origen. Autenticación por sesión Django y CSRF; no hay token de Universo en navegador. `GET /api/session/` entrega identidad, permisos y token CSRF. Login POST y logout DELETE requieren CSRF; el login tiene límite por IP mediante throttle anónimo. Operación detrás de HTTPS en producción.

| Endpoint | Uso |
|---|---|
| GET /api/catalog/ | Catálogos locales, empleados, turnos y programas visibles |
| GET /api/balance/ | Mismos servicios que Excel/cortes: group, client, scope, year, week, view=operational, search, date |
| POST /api/programs/ | Crear programa borrador y renglones (Planeación) |
| POST /api/programs/ID/publication/ | Publicar/ocultar |
| POST /api/captures/ | Nuevo evento idempotente |
| POST /api/captures/ID/release/ | Calidad libera una vez |
| POST /api/captures/ID/correct/ | Planeación revierte/reemplaza |
| POST /api/captures/ID/request-correction/ | Solicitud de operador |
| POST /api/demands/ID/revise/ | Revisar demanda con motivo |
| POST /api/transfer/ | Asignar crédito de captura o saldo inicial a demanda compatible |
| POST /api/imports/ | Multipart file, mode, mapping JSON; previsualización |
| POST /api/imports/ID/ | Confirmación atómica y revalidación de watermark |
| POST /api/cuts/ | Fotografía versionada, cierre opcional |
| GET /api/cuts/ID/ | Reproducción inmutable |
| POST /api/reopen/ | Reapertura autorizada con motivo |
| GET /api/export/, /api/production-export/ | Excel seguro de balance o movimientos |
| GET /api/template/ | Plantilla programa nuevo |
| GET /api/audit/ | Auditoría/solicitudes/cierres (Planeación) |
| POST /api/universe/sync/ | Sincronización central de lectura (Planeación) |

Lectura para Power BI: balance JSON y Excel están disponibles con cuenta de Consulta/sesión autorizada. **No se ha configurado un conector programado de Power BI ni credenciales de servicio independientes**; no colocar el token de Universo para acceder a Empaques. Establecer el mecanismo de servicio con TI antes de automatizar extracción.

Universo v1: bootstrap → páginas de parts incluyendo inactivas → replay de changes → cursor guardado en la misma transacción que cada página de cambios. Identidad central UUID; número no es único entre clientes/destinos. Redirects se rechazan para no reenviar credenciales a otro origen. Errores HTTP se registran por código sin token ni cuerpo. Si falla una página, se conserva la caché y se reintenta idempotentemente. Desactivar una pieza en catálogo no elimina referencias históricas. No se hace scraping autenticado ni se accede a tablas internas.

Límites: no metas diarias automáticas hasta definir jornadas laborables; no se infieren horarios A/B; no se aplican créditos a futuro sin una acción de Planeación. Permisos iniciales son por rol para todos los grupos de esta planta; si se requieren restricciones por cliente/área, agregar autorización por alcance antes de conceder ese acceso. La cuenta TV debe tener exclusivamente Consulta y ejecutarse en perfil separado.

No se ha desplegado en el servidor existente ni certificado el navegador físico de Smart TV. El modo TV rota pendientes cada 15 segundos y conserva filtros por navegador; no hay consola central de pantallas. No se ha implementado firma electrónica ni sincronización offline completa.

Las imágenes Docker de Python/PostgreSQL/Nginx están definidas en Compose/Dockerfiles; antes de un despliegue oficial TI debe validar parches de imagen, TLS, dominios, permisos del volumen privado y restauración fuera del equipo. Evitar `docker compose down -v` en operación: eliminaría el volumen de la base.
