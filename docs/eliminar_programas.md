# Eliminar programas desde Planeación

Cada tarjeta de Programas incluye **Eliminar programa**. La acción abre una revisión del cliente, destino, semana, folios, números de parte y cantidades. El usuario debe indicar un motivo y pulsar **Eliminar definitivamente**. Cancelar o cerrar la ventana no modifica datos.

Solo Planeación puede revisar y ejecutar la eliminación. Se permiten programas publicados o en borrador sin historial operativo, incluidos los programas anteriores con una relación pieza–cliente incorrecta. Se elimina el programa junto con sus órdenes; el catálogo de Universo no se toca.

El servidor rechaza programas con cualquier captura, incluso anulada, saldo inicial, asignación de producción/excedentes o revisión de demanda. También respeta el cierre de la fecha operativa actual. En esos casos la ventana muestra el motivo y no ofrece la confirmación de eliminación. Se conserva la alternativa de ocultar el programa de piso.

La eliminación utiliza la misma exclusión transaccional que capturas, importaciones y cierres. El servidor vuelve a verificar los movimientos y una huella de lo revisado; si aparecieron capturas u órdenes nuevas, o cambiaron sus datos, se exige volver a revisar. La operación se confirma de forma atómica y conserva en auditoría el motivo, el usuario, el programa y las órdenes eliminadas. Los cortes ya emitidos conservan su contenido.

Los archivos y lotes importados permanecen como evidencia. Una carga con programas eliminados se marca como tal; volver a abrir o confirmar el mismo lote no recrea las órdenes ni permite republicar sus programas eliminados. Una carga nueva requiere una revisión y una descripción nueva explícitas.

Verificación: pruebas de permisos, motivo y confirmación obligatorios, eliminación de programas incorrectos sin movimientos, historial protegido, cambio posterior a la revisión, periodos cerrados, auditoría y conservación de lotes. En una base temporal, el navegador cancela una eliminación, elimina un programa sintético y comprueba el bloqueo de otro con capturas. En la instancia local se abrió y canceló la confirmación sin eliminar programas reales.

Resultado: 66 pruebas del servidor correctas y recorrido completo de navegador correcto con cancelación, borrado sintético y bloqueo por capturas. La confirmación local se abrió y canceló sin borrar programas reales. Durante las pruebas, Vite desactiva recargas por cambios de archivos para no interrumpir formularios abiertos.
