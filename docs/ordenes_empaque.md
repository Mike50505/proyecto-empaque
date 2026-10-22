# Órdenes de empaque · vista unificada

Captura y Balance se sustituyeron por una sola entrada: **Órdenes**. Los enlaces anteriores `#Capturar` y `#Balance` abren la vista unificada.

## Pasar a la siguiente semana

Planeación dispone de **Pasar a la siguiente semana** en cada fila publicada que tenga pendiente o sobrante liberado. Sustituye al botón general Aplicar sobrantes. La confirmación muestra pieza, destino, semanas y cantidades; cada envío tiene identidad propia para no duplicar movimientos si se reintenta.

El traslado cambia la semana de trabajo de las órdenes elegidas, conservando intactos su programa, folio, demanda original y semana de compromiso. En destino se agrupan con órdenes publicadas de la misma identidad de Universo, cliente y destino: los pendientes se suman y los sobrantes liberados se asignan para reducirlos. El trabajo sin liberar reserva capacidad y no se trata como crédito. Las capturas de una fila agrupada cumplen primero los compromisos más antiguos y luego los nuevos; cada asignación queda en su orden original.

Si no existe una orden compatible, la pieza aparece en la semana destino con su pendiente o sobrante y la etiqueta **Origen año/semana**. No se inventa otra demanda ni una captura física. Si después se publica una orden compatible en esa semana, se aplica el sobrante disponible. Al quedar cumplida y sin sobrantes ni liberaciones pendientes, la orden deja de participar en la semana de trabajo y vuelve a consultarse en su semana original. Una corrección que reabra su saldo la vuelve a mostrar en la semana trasladada. Se puede trasladar otra vez lo que siga pendiente, también al cambiar de año ISO.

La exportación distingue **Semana de trabajo** de **Trasladado desde**. Los periodos cerrados, permisos de Planeación y validación de Universo se mantienen. Los movimientos se registran en auditoría y los programas con traslados no se pueden eliminar. La revisión de demanda está deshabilitada en filas agrupadas para evitar cambiar por error una orden usando el total del grupo.

Cada orden muestra cliente/destino, pieza, diámetro, semana de compromiso, programado, empacado, por liberar, pendiente de cumplir y cumplimiento aplicado. Bajo Empacado se indica lo que falta empacar. Los excedentes se muestran por separado. El botón Capturar y la revisión de demanda dependen de los permisos; los borradores se pueden consultar por Planeación, pero no permiten capturar.

Ejemplo: programa 300, captura física 200 sin liberar: empacado 200, por liberar 200, por empacar 100 y pendiente de cumplir 300. Si se liberan y aplican las 200 piezas, el pendiente de cumplir baja a 100. «Por liberar» suma capturas vigentes sin liberación, no resta empacado menos aplicado, porque esa resta confundiría excedentes o asignaciones entre órdenes.

La vista conserva filtros de cliente, destino, semana, semanas anteriores, prioridad, estado y publicación. Los resúmenes y la exportación Excel usan el mismo alcance. El selector de año solo aparece cuando existen varios años consultables; los programas nuevos siguen usando automáticamente el año actual. Los estados son: todas, por empacar, por liberar, pendientes de cumplir, completadas y con excedente.

Inicio e Importaciones llevan a la misma vista. La pantalla TV conserva su tabla compacta de pendientes y funciona en solo lectura. Historial conserva folios, responsables, liberaciones y correcciones.

Verificación: compilación de producción; pruebas PostgreSQL de pendientes sin liberar, correcciones, excedentes y exportación filtrada; recorrido completo en navegador con importación, capturas parciales, persistencia, exportación, móvil y TV. Inspección visual local de escritorio y tema oscuro, y comprobación adaptable 375/768/1024/1440. No se crearon movimientos en la base operativa.
