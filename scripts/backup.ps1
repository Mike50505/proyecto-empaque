param([string]$Destination = "private/backups")
$ErrorActionPreference = "Stop"
$taskBackupPath = Join-Path (Get-Location) $Destination
New-Item -ItemType Directory -Force -Path $taskBackupPath | Out-Null
$taskStamp = Get-Date -Format "yyyyMMdd-HHmmss"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/empaques.dump'
if ($LASTEXITCODE -ne 0) { throw "Falló pg_dump" }
docker compose cp db:/tmp/empaques.dump (Join-Path $taskBackupPath "$taskStamp.dump")
if ($LASTEXITCODE -ne 0) { throw "Falló copia de base" }
if (Test-Path -LiteralPath "private/imports") {
    Compress-Archive -LiteralPath "private/imports" -DestinationPath (Join-Path $taskBackupPath "$taskStamp-imports.zip")
}
Write-Output "Respaldo creado en $taskBackupPath. Conserva .env por separado y en almacenamiento protegido."
