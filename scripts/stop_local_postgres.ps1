$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $projectRoot "_local_postgres\data"
$pgCtl = "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe"

if (!(Test-Path $dataDir)) {
    throw "Cluster local nao encontrado em $dataDir"
}

& $pgCtl -D $dataDir stop | Out-Null
