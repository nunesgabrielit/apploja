$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $projectRoot "_local_postgres\data"
$logFile = Join-Path $projectRoot "_local_postgres\postgres.log"
$pgCtl = "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe"
$pgIsReady = "C:\Program Files\PostgreSQL\18\bin\pg_isready.exe"

if (!(Test-Path $dataDir)) {
    throw "Cluster local nao encontrado em $dataDir"
}

& $pgCtl -D $dataDir -l $logFile -o "-p 5433 -h 127.0.0.1" start | Out-Null
Start-Sleep -Seconds 2
& $pgIsReady -h 127.0.0.1 -p 5433
