param([int]$Port = 5173)

$ErrorActionPreference = 'Stop'
$webDir = Join-Path $PSScriptRoot 'web'
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) { $npm = Get-Command npm -ErrorAction SilentlyContinue }
$node = Get-Command node.exe -ErrorAction SilentlyContinue
if (-not $node) { $node = Get-Command node -ErrorAction SilentlyContinue }

# Codex Desktop supplies a Node runtime for this local workspace.  It is only
# a fallback: the normal and portable path remains a user's Node.js 20+ install.
$codexNode = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
if (-not $node -and (Test-Path -LiteralPath $codexNode)) {
    $nodePath = $codexNode
} elseif ($node) {
    $nodePath = $node.Source
} else {
    throw 'Node.js 20+ is required. Install the Node.js LTS release, then run this command again.'
}

Push-Location $webDir
try {
    if (-not (Test-Path -LiteralPath '.env')) {
        Copy-Item '.env.example' '.env'
    }
    if (-not (Test-Path -LiteralPath 'node_modules')) {
        if (-not $npm) { throw 'Dependencies are missing and npm is not available. Install Node.js 20+ and retry.' }
        & $npm.Source install
        if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' }
    }
    if ($npm) {
        & $npm.Source run dev -- --host 127.0.0.1 --port $Port
    } else {
        & $nodePath (Join-Path $webDir 'node_modules\vite\bin\vite.js') --host 127.0.0.1 --port $Port
    }
} finally {
    Pop-Location
}
