param([switch]$RestartBackend)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
New-Item -ItemType Directory -Force -Path (Join-Path $taskRoot 'private') | Out-Null
function Get-TaskListener([int]$Port) {
    # Access errors must stop startup instead of pretending the port is free.
    Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object LocalPort -eq $Port
}
if ($RestartBackend) {
    $taskIds = Get-TaskListener 58000 | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($taskId in $taskIds) {
        $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $taskId"
        if (-not ($taskProcess.CommandLine.Contains($taskRoot) -and $taskProcess.CommandLine.Contains('backend/manage.py'))) {
            throw 'El puerto 58000 pertenece a otro servicio; no se ha detenido.'
        }
        Stop-Process -Id $taskId
        Wait-Process -Id $taskId -Timeout 10 -ErrorAction SilentlyContinue
    }
    for ($taskAttempt = 0; $taskAttempt -lt 30 -and (Get-TaskListener 58000); $taskAttempt++) {
        Start-Sleep -Milliseconds 100
    }
    if (Get-TaskListener 58000) { throw 'El puerto 58000 no se liberó después del reinicio.' }
}
if (-not (Get-TaskListener 58000)) {
    Start-Process -FilePath (Join-Path $taskRoot '.venv/Scripts/python.exe') -ArgumentList @('backend/manage.py','runserver','127.0.0.1:58000','--noreload') -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot 'private/backend.stdout.log') -RedirectStandardError (Join-Path $taskRoot 'private/backend.stderr.log')
}
if (-not (Get-TaskListener 55173)) {
    Start-Process -FilePath (Get-Command node).Source -ArgumentList @('node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','55173','--strictPort') -WorkingDirectory (Join-Path $taskRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskRoot 'private/frontend.stdout.log') -RedirectStandardError (Join-Path $taskRoot 'private/frontend.stderr.log')
}
for ($taskAttempt = 0; $taskAttempt -lt 30 -and -not (Get-TaskListener 58000); $taskAttempt++) {
    Start-Sleep -Milliseconds 200
}
if (-not (Get-TaskListener 58000)) { throw 'El servidor no inició. Revisa private/backend.stderr.log.' }
Write-Output 'Empaques MESA: http://127.0.0.1:55173/'
