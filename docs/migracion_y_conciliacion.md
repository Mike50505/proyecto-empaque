# Migración asistida y conciliación

1. Elegir con Planeación una hoja oficial por alcance, semana y fecha/hora de corte. No importar todas las pestañas y arrastres como demanda nueva. Conservar los originales, hashes y discrepancias.
2. Usar **Histórico de consulta** para evidencia ambigua. No convierte fechas TODAY, AYB o acumulados de papel en eventos físicos.
3. Para programa nuevo, mapear solamente demanda nueva y agregados validados. Excluir arrastres cuya demanda original sigue activa. Para deuda de origen no reconstruible, Planeación debe definir un programa legado explícito y documentar que su semana es de migración, no el origen histórico; no atribuir una semana ficticia. Este caso no se importa automáticamente.
4. Previsualizar cada hoja. Resolver conflictos de semana/version, piezas desconocidas, referencias y columnas. Año y semana siempre se proporcionan; el nombre de hoja no es autoridad. Las cantidades son enteras; los errores no se sustituyen por cero.
5. En saldo inicial, establecer demanda vigente y saldo firmado al corte. Se registra aplicado = demanda − pendiente positivo; excedente = negativo del saldo si existe. Esto no crea captura física. Exige renglón sin eventos, asignaciones o saldo anterior. Un saldo que excede la demanda mapeada bloquea y requiere revisar alcance/arrastres.
6. Confirmar el lote revisado y publicarlo por separado. Los archivos se guardan en private/imports. Las reimportaciones exactas son idempotentes. Un archivo revisado no crea otra demanda sobre la misma identidad: usar revisión.
7. Conciliar en paralelo con el Excel, pieza por pieza y con corte compatible. 3,200 programadas y 2,500 capturadas contra saldo Excel 700 da diferencia 0; no crea 700 nuevas ni descuenta otras 2,500.
8. Para un corte histórico, proporcionar `snapshot` en el mapeo avanzado: el balance se compara contra esa fotografía inmutable. Sin snapshot, la comparación es contra el estado de previsualización; Planeación debe asegurar que el Excel corresponde a ese momento. El formulario no certifica por sí solo la simultaneidad de los cortes.
9. La conciliación guarda diferencias y explicación sin movimientos automáticos. Corregir el origen del error mediante revisión o corrección autorizada y motivo; emitir otro corte. El watermark rechaza confirmaciones si hubo operación desde la previsualización. Volver a previsualizar conserva las capturas posteriores.

Mapeo avanzado (JSON):

```json
{
  "program_id": 12,
  "line_resolutions": {"11": 48},
  "part_resolutions": {"11": 103},
  "snapshot": 7
}
```

Los números son ejemplos, no IDs válidos de producción. `line_resolutions` liga fila Excel a ID de demanda cuando la referencia manual no coincide con número de parte. `part_resolutions` resuelve múltiples UUID centrales con un mismo número. No se mezclan clientes ni destinos por compartir número.

El importador no reconstruye automáticamente toda la historia horizontal ni certifica las diferencias de resúmenes manuales. Conserva todas las celdas de las filas candidatas para revisión. La habilitación de operación oficial depende de la validación del corte y del catálogo de empleados, no de cargar indiscriminadamente los cuatro libros.
