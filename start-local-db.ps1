param([int]$Port = 55432)
$ErrorActionPreference = 'Stop'
$pgBin = 'C:\Program Files\PostgreSQL\16\bin'
$localDir = Join-Path $PSScriptRoot 'core-api\.local'
$dataDir = Join-Path $localDir 'postgres'
$dbEnv = Join-Path $localDir 'postgres.env'
$configFile = Join-Path $PSScriptRoot 'core-api\.env'
if (-not (Test-Path -LiteralPath (Join-Path $pgBin 'initdb.exe'))) {
    throw 'PostgreSQL 16 binaries were not found. Use Docker Compose or adjust pgBin.'
}
New-Item -ItemType Directory -Path $localDir -Force | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $dataDir 'PG_VERSION'))) {
    if (Test-Path -LiteralPath $dataDir) { throw 'Data directory already exists but is not initialized. Inspect it manually.' }
    $passwordBytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($passwordBytes)
    $rng.Dispose()
    $dbPassword = -join ($passwordBytes | ForEach-Object { $_.ToString('x2') })
    $passwordFile = Join-Path $localDir 'initdb-password.tmp'
    [IO.File]::WriteAllText($passwordFile, $dbPassword, [Text.Encoding]::ASCII)
    try {
        & (Join-Path $pgBin 'initdb.exe') -D $dataDir -U matchmaker --encoding=UTF8 --locale=C --auth=scram-sha-256 --pwfile=$passwordFile
        if ($LASTEXITCODE -ne 0) { throw 'initdb failed; see output above.' }
        [IO.File]::WriteAllText($dbEnv, "DATABASE_URL=postgresql+psycopg://matchmaker:$dbPassword@127.0.0.1:$Port/postgres`n", [Text.Encoding]::ASCII)
    } finally {
        Remove-Item -LiteralPath $passwordFile -ErrorAction SilentlyContinue
    }
}
& (Join-Path $pgBin 'pg_ctl.exe') -D $dataDir status 2>$null
if ($LASTEXITCODE -ne 0) {
    & (Join-Path $pgBin 'pg_ctl.exe') -D $dataDir -l (Join-Path $localDir 'postgres.log') -o "-h 127.0.0.1 -p $Port" -w start
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL did not start. See core-api/.local/postgres.log.' }
}
if ((Test-Path -LiteralPath $configFile) -and -not (Select-String -LiteralPath $configFile -Pattern '^DATABASE_URL=' -Quiet)) {
    [IO.File]::AppendAllText($configFile, [IO.File]::ReadAllText($dbEnv), [Text.Encoding]::UTF8)
}
Write-Host "Dedicated Matchmaker PostgreSQL is ready on 127.0.0.1:$Port. Existing PostgreSQL services were not changed."
