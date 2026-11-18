param([switch]$UseSqlite, [switch]$WithChat)

$ErrorActionPreference = 'Stop'
$backendArguments = @()
if ($UseSqlite) { $backendArguments += '-UseSqlite' }

$backendReady = $false
try {
    $backendReady = (Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200
} catch {}

if ($backendReady) {
    Write-Host 'The backend is already running at http://127.0.0.1:8000'
} else {
    & (Join-Path $PSScriptRoot 'start-background.ps1') @backendArguments
    if ($LASTEXITCODE -ne 0) { throw 'The backend did not start.' }
}

if ($WithChat) {
    $chatDirectory = Join-Path $PSScriptRoot 'chat-service'
    if (-not (Test-Path -LiteralPath (Join-Path $chatDirectory 'node_modules'))) {
        Push-Location $chatDirectory
        try { npm install } finally { Pop-Location }
    }
    Start-Process -FilePath 'npm.cmd' -ArgumentList 'start' -WorkingDirectory $chatDirectory -WindowStyle Hidden
    Write-Host 'Chat service is starting at ws://127.0.0.1:8010/ws'
}

$frontendStart = Join-Path $PSScriptRoot 'frontend\start.ps1'
if (-not (Test-Path -LiteralPath $frontendStart)) {
    throw 'The frontend folder is missing. Clone the complete Matchmaker repository.'
}

$frontendReady = $false
try {
    $frontendReady = (Invoke-WebRequest -Uri 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200
} catch {}

if ($frontendReady) {
    Write-Host 'The frontend is already running at http://127.0.0.1:5173'
} else {
    Write-Host 'Opening the web client at http://127.0.0.1:5173'
    & $frontendStart
}
