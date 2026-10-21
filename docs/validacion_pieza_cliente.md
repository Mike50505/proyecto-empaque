# Validación obligatoria pieza–cliente contra Universo Ramos

Cada orden operativa debe usar una pieza con UUID central, confirmada y activa en la caché sincronizada de la API de Universo Ramos. La interfaz agrupa los nombres oficiales en cuatro clientes: DAIKIN, LENNOX 1, MESA MTY (BRAZEWAY, CARRIER, CARRIER A, CARRIER D, LENNOX 2 y TRANE) y RHEEM (CIP-3501, FALCON, NIPLES y TRANSFERENCIA). La validación compara la pieza con su grupo permitido, conserva el nombre oficial de Universo en la pieza y muestra las órdenes históricas bajo el grupo correspondiente. Los nombres fuera de estas equivalencias no se mezclan.

## Bloqueos

- Excel: cada fila se valida por número de parte y cliente. Se eliminó la búsqueda alternativa solo por número que admitía piezas de otro cliente.
- Una selección explícita por ID tampoco puede saltarse la relación de cliente. Una pieza desconocida o provisional no se convierte automáticamente en una pieza del cliente escrito en Excel; la opción de autorización provisional se retiró del formulario.
- La confirmación vuelve a validar el catálogo, incluso si la previsualización anterior era correcta. Un error revierte el lote completo.
- La creación manual valida todos los renglones en servidor y guarda el nombre del grupo. El selector siempre muestra los cuatro clientes aunque todavía no tengan piezas o programas cargados; ofrece únicamente piezas confirmadas y activas de ese grupo y limpia la selección al cambiar de cliente.
- La publicación de programas y las nuevas capturas validan la misma relación. Las asignaciones de producción liberada y excedentes también comprueban el catálogo.
- Las órdenes anteriores con incompatibilidad siguen visibles con el motivo, pero no permiten nuevas capturas. No se cambian sus cantidades, cliente ni movimientos automáticamente.

## Sincronización

La API documentada de Universo ofrece nombres en `/parts/` e IDs de catálogos en `/changes/`. El adaptador ahora resuelve esos IDs con `/catalogs/`; cuando un ID no se encuentra allí, consulta la pieza por UUID. Así un cambio de cliente no conserva silenciosamente el nombre anterior. `manage.py sync_universe --full` refresca la caché completa mediante la API oficial, sin escribir en Universo. La validación usa esa caché local; no depende de una petición remota por cada pieza al capturar.

## Auditoría local

Se refrescaron 302 piezas desde la API. La auditoría encontró 11 órdenes con piezas de LENNOX 1 y cliente RHEEM TRANSFERENCIA; ninguna tenía capturas. El reporte privado está en `private/auditoria-clientes-piezas.json`. `scripts/audit_part_customers.py` permite repetir la consulta sin cambiar datos operativos. Estas órdenes se marcan y bloquean para revisión, sin corregir su cliente por suposición ni eliminarlas.

## Pruebas

Los casos sintéticos incluyen Excel con cliente incorrecto, intento de forzar ID, autorización provisional, pieza desconocida/inactiva, API manual, normalización de nombre, cambio del catálogo entre revisión y confirmación, publicación y captura de órdenes antiguas incompatibles, números iguales entre clientes y actualización de nombres desde eventos de Universo. El recorrido de navegador comprueba que la fila incompatible bloquea la publicación y que el selector manual no ofrece piezas de otro cliente; después completa una importación válida y una captura.
