# Revisión del proceso de órdenes y captura

## Problemas comprobados en la operación

La carga del Excel de diez órdenes se guardó en el lote 7. Existían diez demandas, pero su programa tenía `published=false`. El operador solo puede capturar programas publicados: el listado vacío era consecuencia de ese estado oculto. La interfaz decía «Lote confirmado» sin distinguir guardado y publicado, y obligaba a descubrir otra pantalla para completar el proceso.

La validación anterior probaba confirmar un lote, pero terminaba antes de comprobar que sus demandas aparecieran en Captura. También faltaban trabajadores en el catálogo operativo: aun resolviendo la publicación, la siguiente captura habría fallado por nómina. No se inventaron empleados para ocultar esa falta de configuración.

Otros problemas corregidos: el formulario mezclaba la plantilla simple con mapeos de balances históricos; mostraba una columna de diferencias sin su celda correspondiente; la selección personal de filtros podía esconder la nueva carga; respuestas anteriores a un cambio de filtros podían sobrescribir resultados recientes; el refresco periódico podía borrar un error de otra operación.

## Recorrido principal

1. **Elegir Excel y revisar.** La plantilla identifica sus campos y su hoja automáticamente si es única. No se guarda demanda al revisar. Los balances históricos siguen requiriendo selección y resolución explícitas.
2. **Revisar órdenes.** Mostrar referencia, número de parte, cliente/destino, semana y cantidad. Los errores bloqueantes impiden confirmar. Los ajustes de históricos son un apartado opcional.
3. **Importar y mostrar en Captura.** Una transacción crea demanda y publica los programas. Si no se puede publicar, se revierte todo el lote. La alternativa es «Guardar como borrador», que avisa que aún no está disponible para el operador.
4. **Ver órdenes en Captura.** El resultado incluye los programas y su estado real. El botón establece el grupo/semana de la carga y limpia filtros anteriores. Un borrador ya guardado puede publicarse desde el mismo lote, sin reimportar ni duplicar.
5. **Registrar trabajador, si falta.** Planeación puede dar de alta nómina y nombre reales desde Captura. Operador no puede crear empleados ni programas. No se crean responsables ficticios.
6. **Capturar cantidad adicional.** Seleccionar orden, cantidad y responsables. Al confirmar, el servidor guarda un movimiento con clave idempotente y devuelve folio. La tabla vuelve a consultar la producción física. Liberación y aplicación a demanda se conservan separadas.
7. **Recargar y comprobar.** Las órdenes, su publicación y sus capturas deben permanecer en PostgreSQL. Los reportes siguen usando los mismos movimientos y asignaciones.

La carga de ejemplo previamente aplicada se publicó mediante el mismo servicio, conservando sus diez demandas originales. Los cuatro balances empresariales originales continúan en previsualización sin publicación automática.

## Verificación

La prueba de navegador se extendió para importar diez órdenes, publicar en la misma acción, abrirlas desde el resultado, comprobar diez filas, capturar 25 piezas y recargar comprobando que persisten. El backend verifica borrador/publicación, reintentos sin duplicados, visibilidad para operador y reversión atómica cuando un grupo no permite publicación. También se comprueban permisos e idempotencia del alta de trabajadores.

La suite de invariantes de capturas, créditos, revisiones, cierres y concurrencia se conserva. Que estas pruebas pasen no certifica los cortes históricos oficiales ni los horarios de planta; esos datos siguen sujetos a validación operativa.
