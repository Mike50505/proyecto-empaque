# Dashboard de empaque · rediseño

El dashboard ahora tiene una vista propia, separada de la tabla de Órdenes y de la pantalla TV. Conserva las paletas MESA y muestra únicamente programas publicados en el alcance elegido.

- Cuatro indicadores: programa vigente, empaque físico registrado, pendiente de liberación y pendiente por cumplir.
- Producción diaria en barras apiladas por turno, con periodos de 7 o 14 días. Cada barra permite consultar sus cantidades y abrir las capturas del día.
- Cumplimiento circular ponderado por piezas aplicadas respecto a las programadas, con cantidades aplicadas, pendientes y excedentes separados.
- Pendientes agrupados por cliente o por año/semana, ordenados por cantidad. Cada grupo abre sus órdenes.
- Siguientes cinco órdenes según prioridad, semana y pendiente. Los accesos llevan a Órdenes con los filtros correspondientes.
- Historial de cortes desplegable con sus cantidades y versiones, y revisiones de demanda disponibles.
- Filtros principales de cliente, semana y fecha final de la gráfica. Destino, búsqueda, año cuando hay varios y prioridades quedan en Más filtros. Se muestran el alcance y la hora de actualización.

La fecha final delimita la gráfica de producción física. Las cifras del programa conservan su semana de compromiso. La gráfica pide la serie agregada a la API de analytics y no vuelve a sumar registros reasignados como nueva producción. Los periodos sin capturas muestran un estado vacío explícito. No se inventaron metas, comparaciones contra periodos anteriores ni datos de ejemplo en operación.

Los valores se conservan separados: empacado no equivale a aplicado; la liberación no representa un embarque. Las órdenes con relación pieza–cliente inválida mantienen su aviso y acceso de revisión.

Se usan gráficas nativas, recursos locales y etiquetas con cantidades; no hay dependencias nuevas ni CDN. Las barras admiten teclado y muestran el mismo detalle al seleccionarlas. La distribución se adapta a móvil y a las seis paletas existentes. Al cambiar de módulo se vuelve al inicio de la página.

Verificación: compilación de producción correcta; cinco pruebas de agregación (pendientes sin compensar excedentes, separación de años/semanas, fecha/turno, prioridades y escala de gráfica); recorrido completo React + Django + PostgreSQL en base temporal; comprobación local de periodos, agrupación, acceso a Órdenes, modo oscuro y anchos 375/768/1024/1440. Las vistas revisadas están en private/dashboard-renovado-desktop.png, private/dashboard-renovado-mobile.png y private/dashboard-renovado-oscuro.png. No se modificaron órdenes ni capturas reales.
