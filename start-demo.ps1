param([switch]$UseSqlite)

$ErrorActionPreference = 'Stop'
$backendArguments = @()
if ($UseSqlite) { $backendArguments += '-UseSqlite' }

& (Join-Path $PSScriptRoot 'start-background.ps1') @backendArguments
if ($LASTEXITCODE -ne 0) { throw 'The backend did not start.' }

$frontendStart = Join-Path $PSScriptRoot 'frontend\start.ps1'
if (-not (Test-Path -LiteralPath $frontendStart)) {
    throw 'The frontend folder is missing. Clone the complete Matchmaker repository.'
}

Write-Host 'Opening the web client at http://127.0.0.1:5173'
& $frontendStart
