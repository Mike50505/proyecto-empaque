# Fuentes, evidencia y decisiones

Se revisaron los cuatro XLSX originales, `POWER BI PLANEACION.pbix`, el prompt y las transcripciones `gemini-code-1792096123482.txt` y `gemini-code-1792096134950.txt`. Los nombres `Markdown pegado.md` y `Markdown pegado (2).md` no están presentes; las dos transcripciones disponibles sirven como levantamiento. No se modificaron originales.

La inspección reproducible `scripts/inspect_sources.py` produjo `inventario_fuentes.json`: hashes SHA-256, 64 hojas, encabezados, rangos combinados, conteos de fórmulas, referencias externas y **354 celdas con errores almacenados**. No se recalcularon fórmulas. Los resultados almacenados no prueban vigencia del documento.

| Familia | Hojas | Mapeo inicial observado, sujeto a previsualización |
|---|---:|---|
| Lennox | 17 | En hojas recientes encabezado fila 10; pieza D; programa H; saldo N; I puede ser arrastre o AG1. Nunca sumar I sin revisar la hoja. |
| Daikin | 15 | Pieza D; programa I; saldo O; J puede tener alcance/arrastre; SLP y USA permanecen separados. |
| Monterrey | 18 | Pieza D; programa I; saldo O; J:N combinan agregados y posibles arrastres. `SEMANA 42 (2)` exige versión explícita. |
| Rheem | 14 | Transferencia, Falcon, CIP y Niples; encabezados detectados por contenido; validar las columnas en cada hoja. `SEMANA 34 OK` no reemplaza automáticamente `SEMANA 34`. |

El importador busca CLIENTE y NÚMERO DE PARTE en las primeras 30 filas, normalizando acentos y espacios. La plantilla nueva usa encabezados explícitos. Se registran celdas con valor original, resultado almacenado y formato; los errores en cantidad/identidad/saldo requerido bloquean. Los errores de atributos auxiliares son advertencias. No se ejecutan macros, fórmulas ni enlaces. Las filas sin identidad suficiente se omiten con motivo, conservando valores de identidad: resúmenes de programado/pendiente, calendarios, días de semana, clientes numéricos y fechas no se aceptan como piezas. Una estructura fuera de estos patrones requiere ampliar el mapeo, no rellenar datos ficticios.

Las variantes de semanas, versiones y formularios se conservan en previsualización. La Daikin `SEMANA 42` tiene 39 en el encabezado; debe resolverse explícitamente. No se interpreta TODAY() como fecha de trabajo. AYB ambiguo permanece como evidencia; no se reparte entre A y B. Los destinos que son contactos se conservan literalmente. Diámetro es texto, incluidos `A - 3/8` y `SOLDADURA 7/8`.

El PBIX es contenedor ZIP y se leyó Report/Layout: página BALANCE GENERAL, comparación programa/producción por pieza, filtros semana/fecha/cliente y tabla de pendientes/programado. El JSON accesible queda en el inventario. No se extrajo DataModel, M ni inventario DAX completo. El PBIX no es dependencia de ejecución. La nueva app calcula cumplimiento ponderado mediante sumas, separa físico y asignado y no equipara producción de máquinas a empaque.

Las conversaciones priorizan cuatro grupos, balance semejante al programa, captura incremental al terminar la pieza y consulta por ambos turnos. Se conservó Rheem con posibilidad de desactivar publicaciones. No se construyó un MES de soldadura ni se modificó Helia. La interfaz es independiente: no se comprobó la interfaz autenticada de Helia.

La API central se comprobó contra el contrato local del proyecto hermano `proyecto universo ramos/docs/API.md` y `catalog/api.py`, sin acceder a tablas internas. `GET /api/v1/parts/?page_size=1` devolvió HTTP 200 y count 302 usando Bearer. Se ejecutó carga completa y replay de cambios. No se almacenan claves en React ni en documentación; la credencial local está en `.env`, excluido de Git.

Quedan por conciliar los ejemplos del prompt: Lennox 42 (neto 1,185 frente a pendientes 11,769 y excedentes 10,584), Lennox 43 (26,884 frente a resumen 22,268/18,966), Daikin (5,541 pendientes / 1,320 excedentes frente a neto 4,221), Monterrey (versiones y 42,766/13,939/56,705/38,705). No se oficializaron estas cifras en la base de operación.
