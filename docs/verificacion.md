# Verificación de la implementación

Datos de operación: catálogo Universo de lectura, 302 piezas al momento de la sincronización. No se publicaron balances oficiales ni se generaron capturas reales. Datos sintéticos utilizados exclusivamente en la base PostgreSQL temporal del runner de Django.

## Comprobado

Última ejecución completa: **38 pruebas correctas**, incluidas las de navegador y rendimiento, en PostgreSQL. No hubo pruebas omitidas en esa ejecución. El recorrido de navegador incluye importar diez órdenes, publicarlas desde la carga, abrirlas en Captura, guardar avance y recargar comprobando persistencia. También verifica que la cantidad semanal permanezca fija y el balance de piso disminuya de 300 a 100 y después a 0 con las capturas. Se probaron correcciones, liberación pendiente y créditos reasignados en ese cálculo. Véase `revision_del_proceso.md`.

- Migraciones 0001 y 0002 aplicadas en PostgreSQL 17; `manage.py check` sin incidencias.
- Suite del núcleo en PostgreSQL: parcial/cierre, incrementos, asignaciones, crédito compatible, simultaneidad de semanas, arrastres sin duplicación, reintentos/conflictos, dos capturas simultáneas, dos consumidores simultáneos de crédito, correcciones entre semanas, liberación una sola vez, revisión de demanda, turno/fecha, permisos y CSRF, corte inmutable y exportación, ponderación, bloqueo de periodos y watermark de importación.
- Importación idempotente y saldo inicial sin producción física; conciliación 3,200 − 2,500 = 700 sin eventos nuevos; libros irregulares reales y semana Daikin ambigua.
- Recorrido real de React + Django + PostgreSQL en Edge/Chromium headless: login con CSRF, 200 + 100 piezas, pendiente 0, exportación XLSX, dashboard, historial, móvil 375 px sin desbordamiento de página, UI de TV sin acción de captura y preferencia de movimiento reducido.
- Medición sintética de 1,001 renglones, 1,000 capturas y 1,000 asignaciones; 8 consultas, aproximadamente 0.112 s en la medición inicial local. El resultado reproducible más reciente queda en `evidence/performance.json`. No es una prueba de capacidad concurrente de usuarios.
- `npm run build` correcto; npm audit sin vulnerabilidades tras actualizar Vite y esbuild en el lockfile.
- `docker compose config --quiet` correcto. PostgreSQL se ejecuta en el Compose del proyecto, separado de los servicios existentes.
- `scripts/backup.ps1` generó un dump y se restauró con pg_restore en `empaques_restore_check`, sin sobrescribir la base operativa. Conteos comparados en `evidence/restore.json`.
- API Universo autenticada HTTP 200; catálogo inicial y replay del cursor completados. No hubo escritura remota.

Evidencia: [balance escritorio](evidence/balance-desktop.png), [captura](evidence/captura-revision.png), [móvil](evidence/balance-mobile.png), [dashboard](evidence/dashboard.png), [pantalla](evidence/modo-tv.png), [recorrido](evidence/e2e.json). Las imágenes y Excel de evidencia contienen únicamente pruebas sintéticas.

## Reproducir

```powershell
$env:RUN_BROWSER_TESTS='1'
.venv/Scripts/python backend/manage.py test packing --noinput
```

El recorrido de navegador necesita `npm ci` en frontend y Edge/Chrome instalado; puede usar Chromium de Playwright si se instala de forma explícita. Sin RUN_BROWSER_TESTS, esa prueba se omite y no debe reportarse como ejecutada. Los tests de libros reales se omiten si se distribuye código sin los archivos empresariales.

## No certificado todavía

No se validaron los saldos oficiales con Planeación ni los horarios/calendarios de planta. No se probó la Smart TV física ni una carga de usuarios representativa. No se construyó o publicó una instancia productiva ni se cambió el proxy del servidor existente. La extracción programada Power BI requiere mecanismo de cuenta de servicio validado por TI. La configuración centralizada de pantallas no está implementada; cada cuenta Consulta conserva sus filtros en su navegador.

El importador es asistido: detecta encabezados y conserva evidencia de formatos reales; no reconstruye automáticamente eventos ambiguos de todas las semanas. Las resoluciones de identidad y diferencias siguen siendo decisiones de Planeación. No se afirma equivalencia documental aprobada con FO-CP-03.
