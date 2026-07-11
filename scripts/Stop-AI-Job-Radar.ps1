[CmdletBinding()]
param()

$ports = @(8000, 5173)
$processIds = foreach ($port in $ports) {
    Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
}

if (-not $processIds) {
    Write-Host "AI Job Radar is not running."
    exit 0
}

foreach ($processId in ($processIds | Select-Object -Unique)) {
    Stop-Process -Id $processId -Force -ErrorAction Stop
    Write-Host "Stopped process $processId."
}
