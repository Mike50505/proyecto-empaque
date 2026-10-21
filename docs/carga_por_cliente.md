# Carga de órdenes por cliente · 16 de octubre de 2026

Esta actualización sustituye las indicaciones anteriores sobre pedir grupo, año y referencia al crear órdenes.

## Plantilla para órdenes nuevas

Las columnas son `cliente`, `destino_o_ambito`, `semana_programa`, `numero_parte` y `cantidad_programada`. Destino puede quedar vacío si no aplica. El usuario elige la semana; el servidor asigna el año calendario actual de la planta, incluso si un archivo antiguo contiene otra columna de año. No se deduce la semana a partir de la fecha de captura.

La aplicación asigna a cada orden un folio permanente al guardar: `ORD-2026-000123`, por ejemplo. Identifica la orden, no cada pieza física. Dos renglones de la misma pieza pueden tener folios diferentes. La previsualización muestra «Se asigna al importar» y, al confirmar, muestra el folio definitivo. Reconfirmar o volver a cargar el mismo archivo con el mismo motivo conserva su lote y folios; no vuelve a crear órdenes. Si cambia el año entre revisión y confirmación, se exige una nueva revisión.

La creación manual aplica las mismas reglas. No solicita grupo, año ni referencias. Los valores de esos campos enviados por clientes antiguos no deciden la identidad de una orden nueva.

## Consulta y compatibilidad

Captura, balance y dashboard se organizan por cliente. Los filtros guardados de grupos anteriores se descartan al abrir la aplicación. No se modifican identidades, capturas ni fechas de las órdenes existentes. El campo de grupo de la base permanece como compatibilidad técnica para los datos anteriores, sin clasificación adicional en las pantallas nuevas. Los excedentes siguen exigiendo misma pieza, cliente y destino; un grupo anterior no impide aplicar crédito a una orden compatible.

Los filtros de año en las consultas permiten revisar los registros conservados cuando avance el calendario; no son campos de creación. Las revisiones de cantidades conservan el folio ya asignado: la plantilla de revisión incluye `referencia`, que se copia de la orden existente y nunca se inventa. Los modos de saldo inicial, conciliación e histórico conservan sus datos de origen y su tratamiento específico.

## Verificación

La suite incluye plantilla de cinco columnas, año automático en servidor, varias semanas del mismo año, folios distintos para órdenes repetidas de una pieza, reintentos sin duplicados, creación manual, compatibilidad con columnas antiguas, revisión sin cambiar folio, cambio de año y crédito entre clasificaciones antiguas. El navegador importa diez órdenes con la nueva plantilla y registra una captura en una de ellas. Las pruebas se ejecutan en una base PostgreSQL temporal separada.

Resultado: compilación correcta; suite completa de 45 pruebas con navegador real correcta, más un caso adicional correcto para reimportación de lotes anteriores (46 casos distintos). La comprobación de lectura de todos los módulos y tamaños 375/768/1024/1440 también pasó. No se crearon órdenes ni capturas en la base operativa.

Corrección de la descarga: se confirmó que la instancia local seguía sirviendo el código anterior. El inicio local ahora detiene la operación si no puede consultar puertos, espera a que se libere el puerto tras detener el servidor y comprueba que vuelva a escuchar. Se reinició la instancia real y se descargó la plantilla desde el botón del navegador: cinco columnas verificadas con openpyxl. El archivo se llama plantilla-ordenes-por-cliente.xlsx y la respuesta impide almacenamiento en caché.
