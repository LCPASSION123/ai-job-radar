[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
$logs = Join-Path $root ".logs"

function Test-ListeningPort([int]$Port) {
    return [bool](Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
}

function Wait-ForPort([int]$Port, [string]$Name) {
    for ($attempt = 0; $attempt -lt 50; $attempt++) {
        if (Test-ListeningPort $Port) { return }
        Start-Sleep -Milliseconds 200
    }
    throw "$Name did not start on port $Port. Read the logs in $logs."
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing $python. Create the virtual environment and install requirements first."
}
if (-not $npm) {
    throw "npm.cmd was not found. Install Node.js 20+ first."
}

New-Item -ItemType Directory -Force -Path $logs | Out-Null

if (-not (Test-ListeningPort 8000)) {
    Start-Process -FilePath $python -WorkingDirectory $root -WindowStyle Hidden `
        -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -RedirectStandardOutput (Join-Path $logs "backend.log") `
        -RedirectStandardError (Join-Path $logs "backend-error.log")
    Wait-ForPort 8000 "Backend"
}

if (-not (Test-ListeningPort 5173)) {
    Start-Process -FilePath $npm.Source -WorkingDirectory (Join-Path $root "frontend") -WindowStyle Hidden `
        -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1") `
        -RedirectStandardOutput (Join-Path $logs "frontend.log") `
        -RedirectStandardError (Join-Path $logs "frontend-error.log")
    Wait-ForPort 5173 "Frontend"
}

Write-Host "AI Job Radar is ready:" -ForegroundColor Green
Write-Host "  Dashboard: http://localhost:5173/"
Write-Host "  API docs : http://127.0.0.1:8000/docs"
Write-Host "  Logs     : $logs"

if (-not $NoBrowser) {
    Start-Process "http://localhost:5173/"
}
