[CmdletBinding()]
param(
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$starter = Join-Path $PSScriptRoot "Start-AI-Job-Radar.ps1"
$taskName = "AI Job Radar Local Dashboard"
$startupFolder = [Environment]::GetFolderPath("Startup")
$startupFile = Join-Path $startupFolder "AI Job Radar.cmd"

if (-not (Test-Path -LiteralPath $starter)) {
    throw "Startup script was not found: $starter"
}

# The task runs only for the signed-in Windows user. It launches local services
# on 127.0.0.1 and receives no platform credentials or remote access.
$taskCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$starter`" -NoBrowser"
$previousErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& schtasks.exe /Create /TN $taskName /TR $taskCommand /SC ONLOGON /RL LIMITED /F 2>$null | Out-Null
$taskExitCode = $LASTEXITCODE
$ErrorActionPreference = $previousErrorAction
if ($taskExitCode -eq 0) {
    $autoStartMode = "Windows Task Scheduler"
} else {
    # Some managed Windows installations prohibit scheduled tasks. The current
    # user's Startup folder has the same login behavior and needs no admin.
    $startupContent = "@echo off`r`npowershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$starter`" -NoBrowser`r`n"
    [System.IO.File]::WriteAllText($startupFile, $startupContent, [System.Text.Encoding]::ASCII)
    $autoStartMode = "Windows current-user Startup folder"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $starter -NoBrowser
if ($LASTEXITCODE -ne 0) {
    throw "The auto-start task was created, but the local dashboard could not be started."
}

Write-Host "Auto-start configured: $autoStartMode" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:5173/" -ForegroundColor Green

if (-not $NoBrowser) {
    Start-Process "http://localhost:5173/"
}
