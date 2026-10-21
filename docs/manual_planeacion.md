# Planeación

Para una carga ordinaria, elegir Excel → **Revisar Excel** → **Importar y mostrar en Captura** → **Ver órdenes en Captura**. La publicación se realiza en la misma transacción que la importación; el botón final abre la carga con su grupo/semana y limpia filtros anteriores. **Guardar como borrador** es una alternativa explícita: no aparece en piso y puede publicarse desde el mismo lote sin volver a cargar el Excel.

Si no hay trabajadores registrados, Captura muestra el formulario de alta de empacador para Planeación. Registrar nómina y nombre reales antes de intentar guardar movimientos. No se necesita salir a otra aplicación para completar ese primer registro.

Antes de operar, dar de alta empleados/inspectores reales, asignar usuarios a roles y revisar turnos, zona y calendario. Sin empleados no se permite inventar nóminas en captura. Roles iniciales: Planeación, Operador, Calidad y Consulta. Administración completa de usuarios requiere usuario staff con permisos Django apropiados o superusuario.

Crear programa con grupo, cliente, ámbito, año/semana y referencia única. Elegir piezas del catálogo y cantidades por renglón; referencias distintas conservan pedidos distintos. El programa empieza en borrador. Publicar explícitamente para ponerlo a disposición de piso. Se admiten varias semanas publicadas. Un grupo puede desactivarse para nuevas publicaciones conservando historia.

Para Excel usar Importaciones. Primero puede dejarse hoja vacía para obtener inventario; después elegir hoja exacta, año, semana, columnas de demanda y saldo. Escribir motivo de selección y resolver semana/versión y piezas provisionales. Los errores bloqueantes impiden confirmar. El mapeo avanzado permite vincular programa/renglón y pieza central sin asumir equivalencias por número. Una plantilla nueva descargable reduce ambigüedades.

Una revisión modifica vigente con motivo, no la cantidad física. En Balance el engrane del renglón permite revisar demanda. En Historial aplicar excedente exige el ID del renglón compatible y cantidad; si no hay pendiente/crédito o es otro ámbito se rechaza. Las capturas y saldos originales permanecen identificados. Las correcciones conservan evento original anulado, reemplazo y asignaciones reversadas, incluso si el crédito se aplicó a otra semana.

En Administración revisar solicitudes, auditoría y estado de Universo; ejecutar sincronización cuando sea necesario. La app continúa con piezas conocidas si la API no responde. No se crean libremente piezas desde Operador.

Emitir cortes de los filtros actuales; cada versión conserva lo entregado. Cerrar una fecha impide cambiar su operación. Reabrir con motivo antes del ajuste autorizado; emitir una versión nueva después. Las conciliaciones de Excel registran diferencias y no modifican producción por sí mismas.

Validar oficialmente corte inicial, grupos, equivalencias, calendarios, horarios, significado de AG/AYB y modo de liberación antes de usar los reportes como balance oficial. El formato imprimible cita FO-CP-03 como referencia del origen, sin declararse documento aprobado.
