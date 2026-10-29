param([switch]$UseSqlite)

$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Virtual environment missing. Run: py -m venv .venv, then install core-api/requirements-dev.txt.'
}
if ($UseSqlite) {
    $env:DATABASE_URL = "sqlite:///$((Join-Path $PSScriptRoot 'core-api\.local\matchmaker-local.db').Replace('\', '/'))"
    Write-Host 'Using the isolated SQLite database for this local run.'
} elseif (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'core-api\.local\postgres\PG_VERSION')) {
    try {
        & (Join-Path $PSScriptRoot 'start-local-db.ps1')
    } catch {
        # Preserve the existing PostgreSQL data directory.  A blocked local
        # port must not prevent the web application from being demonstrated.
        $env:DATABASE_URL = "sqlite:///$((Join-Path $PSScriptRoot 'core-api\.local\matchmaker-local.db').Replace('\', '/'))"
        Write-Warning "PostgreSQL is unavailable; using an isolated SQLite database for this run. $($_.Exception.Message)"
    }
}
Push-Location (Join-Path $PSScriptRoot 'core-api')
try {
    & $projectPython -m app.cli bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'Database setup failed. See the error above.' }
    Write-Host 'Matchmaker: http://127.0.0.1:8000   Swagger: http://127.0.0.1:8000/docs'
    & $projectPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
    if ($LASTEXITCODE -ne 0) { throw 'Server stopped with an error.' }
} finally {
    Pop-Location
}
