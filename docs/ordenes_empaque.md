# Órdenes de empaque · vista unificada

Captura y Balance se sustituyeron por una sola entrada: **Órdenes**. Los enlaces anteriores `#Capturar` y `#Balance` abren la vista unificada.

Cada orden muestra cliente/destino, pieza, diámetro, semana de compromiso, programado, empacado, por liberar, pendiente de cumplir y cumplimiento aplicado. Bajo Empacado se indica lo que falta empacar. Los excedentes se muestran por separado. El botón Capturar y la revisión de demanda dependen de los permisos; los borradores se pueden consultar por Planeación, pero no permiten capturar.

Ejemplo: programa 300, captura física 200 sin liberar: empacado 200, por liberar 200, por empacar 100 y pendiente de cumplir 300. Si se liberan y aplican las 200 piezas, el pendiente de cumplir baja a 100. «Por liberar» suma capturas vigentes sin liberación, no resta empacado menos aplicado, porque esa resta confundiría excedentes o asignaciones entre órdenes.

La vista conserva filtros de cliente, destino, semana, semanas anteriores, prioridad, estado y publicación. Los resúmenes y la exportación Excel usan el mismo alcance. El selector de año solo aparece cuando existen varios años consultables; los programas nuevos siguen usando automáticamente el año actual. Los estados son: todas, por empacar, por liberar, pendientes de cumplir, completadas y con excedente.

Inicio e Importaciones llevan a la misma vista. La pantalla TV conserva su tabla compacta de pendientes y funciona en solo lectura. Historial conserva folios, responsables, liberaciones y correcciones.

Verificación: compilación de producción; pruebas PostgreSQL de pendientes sin liberar, correcciones, excedentes y exportación filtrada; recorrido completo en navegador con importación, capturas parciales, persistencia, exportación, móvil y TV. Inspección visual local de escritorio y tema oscuro, y comprobación adaptable 375/768/1024/1440. No se crearon movimientos en la base operativa.
