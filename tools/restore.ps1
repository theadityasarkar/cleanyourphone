# PowerShell script to restore disabled packages on an Android Phone
# Replays the baseline record or debloat list to restore phone to default state.
#
# Usage:
#   .\tools\restore.ps1 examples\poco-m4-5g\debloat-safe.txt
#
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$List
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false

$repo = Split-Path -Parent $PSScriptRoot
$List = (Resolve-Path -LiteralPath $List).Path
$tools = Join-Path $repo 'tools'
$py = "python"

Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host " CleanYourPhone: Restoring Packages via USB Debugging" -ForegroundColor Yellow
Write-Host " List: $List" -ForegroundColor Yellow
Write-Host "=========================================================="

Write-Host "`n[*] Generating restore commands from baseline record..."
$cmds = & $py (Join-Path $tools 'recovery.py') --commands $List

if (-not $cmds -or $cmds.Count -eq 0) {
    Write-Warning "No packages found to restore."
    exit 0
}

Write-Host "[*] Restoring $($cmds.Count) packages..."
$restoredCount = 0

foreach ($cmd in $cmds) {
    if ($cmd -match '^pm enable\s+(\S+)$') {
        $pkg = $Matches[1]
        Write-Host "  <- Restoring $pkg ... " -NoNewline
        $res = & $py (Join-Path $tools 'phone.py') $cmd 2>&1
        $resStr = ($res -join ' ').Trim()

        if ($resStr -match 'new state: enabled' -or $resStr -match 'new state: default') {
            Write-Host "[ENABLED]" -ForegroundColor Green
            $restoredCount++
        } else {
            Write-Host "[$resStr]" -ForegroundColor Yellow
            $restoredCount++
        }
    }
}

Write-Host "`n[*] Syncing disk cache on device..."
& $py (Join-Path $tools 'phone.py') "sync" | Out-Null

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Restore complete! $restoredCount packages re-enabled." -ForegroundColor Green
Write-Host "=========================================================="
