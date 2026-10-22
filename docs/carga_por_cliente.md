# Carga de órdenes por cliente · 16 de octubre de 2026

Esta actualización sustituye las indicaciones anteriores sobre pedir grupo, año y referencia al crear órdenes.

## Plantilla para órdenes nuevas

Las columnas son `numero_parte`, `cantidad_programada` y `semana_programa`. Cliente y destino se completan desde el catálogo sincronizado de Universo Ramos. Cada número debe identificar una pieza oficial y activa; si no existe o tiene varias identidades, la revisión muestra el problema antes de guardar. Si Universo no tiene destino, se conserva vacío. Las plantillas anteriores con cliente y destino siguen siendo compatibles y se valida que la pieza pertenezca al cliente indicado. El usuario elige la semana; el servidor asigna el año calendario actual de la planta, incluso si un archivo antiguo contiene otra columna de año. No se deduce la semana a partir de la fecha de captura.

La aplicación asigna a cada orden un folio permanente al guardar: `ORD-2026-000123`, por ejemplo. Identifica la orden, no cada pieza física. Dos renglones de la misma pieza pueden tener folios diferentes. La previsualización muestra «Se asigna al importar» y, al confirmar, muestra el folio definitivo. Reconfirmar o volver a cargar el mismo archivo con el mismo motivo conserva su lote y folios; no vuelve a crear órdenes. Si cambia el año entre revisión y confirmación, se exige una nueva revisión.

La creación manual aplica las mismas reglas. No solicita grupo, año ni referencias. Los valores de esos campos enviados por clientes antiguos no deciden la identidad de una orden nueva.

## Consulta y compatibilidad

Captura, balance y dashboard se organizan por cliente. Los filtros guardados de grupos anteriores se descartan al abrir la aplicación. No se modifican identidades, capturas ni fechas de las órdenes existentes. El campo de grupo de la base permanece como compatibilidad técnica para los datos anteriores, sin clasificación adicional en las pantallas nuevas. Los excedentes siguen exigiendo misma pieza, cliente y destino; un grupo anterior no impide aplicar crédito a una orden compatible.

Los filtros de año en las consultas permiten revisar los registros conservados cuando avance el calendario; no son campos de creación. Las revisiones de cantidades conservan el folio ya asignado: la plantilla de revisión incluye `referencia`, que se copia de la orden existente y nunca se inventa. Los modos de saldo inicial, conciliación e histórico conservan sus datos de origen y su tratamiento específico.

## Verificación

La suite incluye plantilla de tres columnas, cliente y destino desde Universo, cantidades y semanas inválidas, piezas desconocidas/inactivas/ambiguas, año automático en servidor, varias semanas del mismo año, folios distintos para órdenes repetidas de una pieza, reintentos sin duplicados, creación manual, compatibilidad con columnas antiguas, revisión sin cambiar folio, cambio de año y crédito entre clasificaciones antiguas. Las pruebas se ejecutan en una base PostgreSQL temporal separada.

Resultado: compilación correcta; suite completa de 45 pruebas con navegador real correcta, más un caso adicional correcto para reimportación de lotes anteriores (46 casos distintos). La comprobación de lectura de todos los módulos y tamaños 375/768/1024/1440 también pasó. No se crearon órdenes ni capturas en la base operativa.

La descarga de órdenes nuevas se llama `plantilla-ordenes.xlsx`, contiene las tres columnas y la respuesta impide almacenamiento en caché. La plantilla de revisión conserva `referencia` para identificar órdenes existentes. El inicio local comprueba los puertos antes y después de reiniciar el backend para que se sirva la versión actualizada.
