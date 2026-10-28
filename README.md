# Empaques MESA

Aplicación de operación interna: **Django 5.2 LTS + API REST, React 19 y PostgreSQL 17**. Interfaz en español, sin CDN. No modifica Helia, Universo ni los archivos de origen. El catálogo se obtiene mediante la API documentada de Universo; programas, capturas y asignaciones pertenecen a esta aplicación.

## Inicio local (Windows / PowerShell)

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/init_env.py
# Editar .env: UNIVERSO_TOKEN se configura solo en el servidor.
docker compose up -d db
.venv/Scripts/python backend/manage.py migrate
.venv/Scripts/python backend/manage.py bootstrap
.venv/Scripts/python scripts/create_local_admin.py
.venv/Scripts/python backend/manage.py sync_universe
.venv/Scripts/python backend/manage.py preview_sources
.venv/Scripts/python backend/manage.py runserver 127.0.0.1:58000
```

En otra terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Abrir **http://127.0.0.1:55173/**. El primer acceso generado está en `private/primer_acceso.txt` (archivo privado, excluido de Git); cambiar contraseña desde **Usuarios → Editar tu cuenta**. Alternativa: `python backend/manage.py createsuperuser`. No hay contraseñas predeterminadas. Dar de alta empleados reales, inspectores y horarios desde Administración → Administrar catálogos. Las nóminas no son contraseñas.

La base operativa comienza sin programas ni movimientos de demostración. `sync_universe` mantiene una caché de las piezas reales; no importa producción. `preview_sources` deja las cuatro hojas propuestas en previsualización, con sus conflictos visibles y sin aplicar demanda. Los casos sintéticos se ejecutan en la base temporal `test_empaques_<PID>` y archivos temporales separados de operación.

## Docker Compose

```powershell
.venv/Scripts/python scripts/init_env.py
# Completar .env, incluidos hosts y credencial del catálogo.
docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py sync_universe
```

Interfaz: http://127.0.0.1:58080/; backend: 58000; PostgreSQL: 55432. Puertos enlazados solo a loopback; recursos con prefijo `empaques-mesa`. Se puede ejecutar junto a otros proyectos. No modifica proxies ni bases existentes. La imagen backend aplica migraciones y roles al iniciar. Para producción, usar HTTPS con un proxy autorizado, `DJANGO_DEBUG=0`, dominios precisos en `DJANGO_ALLOWED_HOSTS`, cookies seguras y credenciales separadas; no exponer el servidor de desarrollo. PostgreSQL y evidencias privadas requieren almacenamiento persistente. La carpeta `private` nunca se sirve por HTTP.

En Docker Desktop, expanda **empaques-mesa** y abra el puerto **58080** del servicio **frontend**. Deben estar iniciados `db`, `backend` y `frontend`; iniciar solo `db` no abre la aplicación. Los tres servicios tienen reinicio automático, salvo que se detengan manualmente. El servidor local de desarrollo y el backend de Docker comparten el puerto 58000: detenga el servidor Python local antes de iniciar el backend en Docker.

## Operación

1. Sincronizar el catálogo; validar empleados, turnos, clientes y destinos.
2. Crear programa en **Programas**, o usar **Importaciones** con previsualización de una hoja/version y columnas de demanda explícitas.
3. En importaciones, elegir **Importar y mostrar en Captura**. Alternativamente, guardar como borrador y publicar desde ese mismo lote. Los programas manuales se publican explícitamente. El operador registra una cantidad **adicional**.
4. Revisar pieza, compromiso, responsables, fecha, turno y excedente; confirmar. El servidor devuelve folio y saldos.
5. Consultar dashboard e historial; emitir Excel, imprimir o conservar un corte.

Guías: [operador](docs/manual_operador.md), [Planeación](docs/manual_planeacion.md), [reglas](docs/reglas_negocio.md), [fuentes](docs/analisis_fuentes.md), [migración](docs/migracion_y_conciliacion.md), [API y despliegue](docs/api_y_operacion.md).

## Verificación

```powershell
.venv/Scripts/python backend/manage.py check
.venv/Scripts/python backend/manage.py test packing --noinput
.venv/Scripts/python scripts/inspect_sources.py
cd frontend
npm run build
npm audit
```

Las pruebas requieren PostgreSQL real y permiso de crear la base temporal. Cubren concurrencia con conexiones diferentes, no usan SQLite. Los libros reales se leen sin modificación; si no están presentes, las pruebas de esas fuentes se omiten explícitamente. La evidencia y límites de lo probado se registran en `docs/verificacion.md`.

## Respaldo y restauración

```powershell
./scripts/backup.ps1
# Restaurar SOLO en una base vacía de recuperación, no en producción:
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" empaques_restore'
docker compose cp private/backups/ARCHIVO.dump db:/tmp/restore.dump
docker compose exec db sh -c 'pg_restore -U "$POSTGRES_USER" -d empaques_restore --no-owner /tmp/restore.dump'
```

Restaurar también el ZIP de `private/imports` en un entorno aislado y el `.env` desde un almacén seguro. Verificar conteos, un reporte y la evidencia de origen antes de cambiar conexiones. La base y archivos necesitan un respaldo coordinado cuando haya cargas en curso. No escribir automáticamente en Z ni enviar reportes por correo/WhatsApp.

## Pendiente de validación operativa

Calendario ISO, zona America/Monterrey, horarios de turnos, corte oficial inicial, variantes de hojas, significados de AG/AYB y política de liberación. Las capturas nuevas requieren ambas nóminas en la misma ventana y se guardan liberadas, aplicando la cantidad al programa en una sola transacción. No existe un apartado separado de Liberaciones. Los pendientes históricos se conservan y Calidad puede liberarlos desde Historial con su permiso existente; no se modifican automáticamente. Los excedentes se aplican a otro programa mediante acción explícita de Planeación.

La importación de libros históricos es asistida, no una migración automática aprobada. Las discrepancias de resúmenes se conservan; las conciliaciones no crean producción ni ajustan cantidades silenciosamente. No se ha certificado la interfaz en el modelo físico de Smart TV de planta ni se ha desplegado en producción.

La revisión del recorrido real y los cambios están documentados en [revisión del proceso](docs/revision_del_proceso.md).

La interfaz y el recorrido se actualizaron tomando Macros como referencia: [cambios y verificación del 16 de octubre](docs/revision_macros_2026-10-16.md). Incluye Inicio, navegación superior, tema claro/oscuro y captura con prioridades, avance y filtros por cliente.

Actualización de carga: la [plantilla por cliente](docs/carga_por_cliente.md) elimina grupo, año y referencia para órdenes nuevas; asigna año actual y folio automáticamente.

Captura y Balance ahora se consultan desde [Órdenes de empaque](docs/ordenes_empaque.md), con una sola tabla para capturar y revisar cumplimiento.

La [validación pieza–cliente](docs/validacion_pieza_cliente.md) es obligatoria contra el catálogo sincronizado de Universo Ramos en Excel, creación manual, publicación y captura. Las órdenes anteriores incompatibles quedan señaladas y bloqueadas para revisión.

Programas incluye [Eliminar programa](docs/eliminar_programas.md): revisión y motivo obligatorios, auditoría y protección de programas con movimientos.

El [dashboard rediseñado](docs/dashboard_redisenado.md) incluye producción diaria por turno, cumplimiento, pendientes por cliente o semana y accesos a las órdenes.


## Excedentes y semanas

Se retiró la función Pasar a la siguiente semana. Cada orden conserva su semana original; las capturas nuevas se aplican solamente a esa orden hasta cubrirla. La cantidad sobrante se consulta en **Excedentes**, con pieza, cliente, destino, orden y semana de origen, folio, fecha y nóminas. Incluye capturas liberadas y saldos iniciales con remanente, incluso si su orden fue retirada. No incluye capturas pendientes o anuladas.

El saldo mostrado resta las asignaciones activas ya realizadas. Consultar Excedentes, publicar o importar programas no aplica sobrantes a otra orden. Los registros de traslados y asignaciones anteriores se conservan como historial; no se eliminan ni se revierten. No hay migraciones de datos para este cambio.


## Usuarios y roles dentro de Empaques

El apartado **Usuarios** permite crear cuentas, editar nombre y correo, asignar rol, activar/desactivar accesos y restablecer contraseñas. No requiere usar el panel de Django. Desactivar conserva la cuenta y la trazabilidad de sus capturas. Las contraseñas se validan y se guardan mediante hash; nunca se devuelven en la API ni se incluyen en auditoría.

- **Admin:** acceso completo; puede gestionar cuentas Admin, Planer y Operador.
- **Planer:** toda la operación, incluida la administración de cuentas Planer y Operador. Solo Admin puede modificar o asignar Admin.
- **Operador:** consulta de las órdenes y su historial para capturar y liberar; no puede planear, importar, corregir programas ni administrar cuentas.

No se permite desactivar la propia cuenta ni cambiar su propio rol. El cambio de contraseña propia mantiene la sesión; restablecer la de otra cuenta invalida sus sesiones anteriores. Las sesiones actualizan los permisos en la interfaz cada 20 segundos y el servidor verifica permisos en cada acción.

La migración 0007 configura Planer y Operador, incorpora las cuentas operativas anteriores a los roles correspondientes y conserva usuarios, contraseñas e historial. Las cuentas antiguas solo de consulta se conservan sin elevar sus privilegios; aparecen como Sin rol asignado hasta que Admin o Planer les asigne uno.
