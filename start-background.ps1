$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$localDir = Join-Path $PSScriptRoot 'core-api\.local'
if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 8000 is already in use. Check http://127.0.0.1:8000/health before starting another server.'
}
if (Test-Path -LiteralPath (Join-Path $localDir 'postgres\PG_VERSION')) {
    & (Join-Path $PSScriptRoot 'start-local-db.ps1')
}
Push-Location (Join-Path $PSScriptRoot 'core-api')
try {
    & $projectPython -m app.cli bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'Database setup failed.' }
} finally { Pop-Location }
New-Item -ItemType Directory -Path $localDir -Force | Out-Null
$process = Start-Process -FilePath $projectPython -ArgumentList @('-m','uvicorn','app.main:app','--app-dir','core-api','--host','127.0.0.1','--port','8000') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $localDir 'server.stdout.log') -RedirectStandardError (Join-Path $localDir 'server.stderr.log') -PassThru
[IO.File]::WriteAllText((Join-Path $localDir 'server.pid'), [string]$process.Id)
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if ($process.HasExited) { throw 'Server exited. Read core-api/.local/server.stderr.log.' }
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Host 'Matchmaker is running at http://127.0.0.1:8000 (background process).'
            return
        }
    } catch { Start-Sleep -Milliseconds 300 }
}
throw 'Startup health check timed out. Inspect server.stderr.log before starting another process.'
