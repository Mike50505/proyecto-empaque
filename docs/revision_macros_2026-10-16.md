# Revisión de Empaque con referencia en Macros · 16 de octubre de 2026

Se revisaron el prompt original, las pantallas y reglas existentes de Empaque, la guía funcional de Macros y sus plantillas y estilos corporativos. La referencia es la versión actual de Macros: navegación superior, identidad MESA azul, encabezados amplios, superficies redondeadas y un recorrido desde la carga del programa hasta los resultados.

## Cambios implementados

- Inicio con resumen de demanda publicada, cumplimiento ponderado y órdenes por atender, indicando el alcance de los filtros personales. Accesos al recorrido según permisos: cargar Excel, publicar semanas, registrar empaque y consultar resultados.
- Navegación superior adaptable con identidad MESA y acceso a los módulos existentes. Conserva el módulo al recargar mediante el fragmento de URL. Los permisos del servidor siguen siendo obligatorios.
- Tema claro y oscuro, guardado localmente. Tipografía del sistema, recursos locales y soporte de movimiento reducido.
- Captura con una fila por orden y una columna fija de compromiso año/semana. Sustituye las columnas vacías por cada semana del resultado, conservando la identidad de cada demanda.
- Prioridad visible; orden por prioridad y antigüedad del compromiso. Filtros por cliente, prioridad alta y pendiente físico. Paginación de 30 órdenes y limpieza conjunta de filtros.
- Programa, avance físico y pendiente físico visibles en captura. El balance y el inicio conservan el cumplimiento aplicado tras liberación. No se confunde empaque físico con aplicación al programa.
- Programas permite cargar Excel y abrir el balance con grupo, cliente, destino, año y semana del programa elegido; incluye borradores en esa consulta para que Planeación pueda revisarlos.
- Exportación del historial con los mismos filtros que su tabla, incluidos responsables y estado.
- Errores de conexión separados de los errores de otras operaciones, para que el refresco no oculte fallos de guardado.

## Verificación

- `npm run build`: correcto.
- `manage.py check`: sin incidencias.
- `RUN_BROWSER_TESTS=1 ... manage.py test packing --noinput`: **38 pruebas, todas correctas**, con PostgreSQL y base temporal. Incluye importación de diez órdenes, publicación, captura incremental, persistencia tras recarga, reporte Excel, dashboard, historial y modo TV.
- `node smoke-local.mjs`: todos los módulos accesibles, persistencia del tema y del módulo, y revisión de anchos 375, 768, 1024 y 1440. La comprobación local solo consulta; no genera capturas ni órdenes.
- Revisión visual de inicio en escritorio y móvil y captura en tema oscuro. Capturas locales en `private/inicio-macros-*.png` y `private/captura-macros-*.png`. Evidencia sintética del recorrido completo en `docs/evidence`.
- Se estabilizó la prueba existente de reimportación: reutiliza los mismos bytes del archivo, evitando que las marcas de tiempo internas de dos Excel recién generados produzcan hashes diferentes.

## Alcance

Se conserva Django + React, las APIs y las reglas de asignación, liberación, excedentes, cierres y auditoría. No se migraron libros ni se modificó Macros. No se desplegó en producción. Los horarios y cortes oficiales continúan sujetos a la validación operativa indicada en el prompt original. La revisión adaptable en navegador no certifica el equipo Smart TV físico de planta.
