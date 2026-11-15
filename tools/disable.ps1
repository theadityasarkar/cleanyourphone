# PowerShell script to safely debloat an Android Phone over USB Debugging
# Packages are disabled for user 0 (never uninstalled), ensuring zero risk of bricking and 100% reversible.
#
# Usage:
#   .\tools\disable.ps1 examples\poco-m4-5g\debloat-safe.txt
#
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$List
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false

$repo = Split-Path -Parent $PSScriptRoot
$List = (Resolve-Path -LiteralPath $List).Path
$tools = Join-Path $repo 'tools'

# Locate Python
$py = "python"
try {
    & $py --version | Out-Null
} catch {
    throw "Python 3 is required. Please install Python or ensure it is in your PATH."
}

# Locate or download ADB
$adb = Join-Path $tools 'platform-tools\adb.exe'
if (-not (Test-Path $adb)) {
    try {
        & adb version | Out-Null
        $adb = "adb"
    } catch {
        Write-Host "ADB not found. Automatically downloading Google Android SDK Platform-Tools..."
        & (Join-Path $tools 'get-platform-tools.ps1')
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " CleanYourPhone: Debloating Phone via USB Debugging" -ForegroundColor Cyan
Write-Host " List: $List" -ForegroundColor Cyan
Write-Host "=========================================================="

# Run safety check first
Write-Host "`n[*] Running Safety Guard Check..."
& $py (Join-Path $tools 'recovery.py') --check-safety $List
if ($LASTEXITCODE -ne 0) {
    throw "Safety check failed! Aborting to protect your phone."
}

# Save recovery baseline
Write-Host "`n[*] Recording Recovery Baseline (so restore can return device to original state)..."
& $py (Join-Path $tools 'recovery.py') --save $List
if ($LASTEXITCODE -ne 0) {
    throw "Failed to record recovery baseline."
}

# Read packages to disable
$pkgs = Get-Content -LiteralPath $List | ForEach-Object { ($_ -replace '#.*$', '').Trim() } | Where-Object { $_ } | ForEach-Object { ($_ -split '\s+')[0] }

Write-Host "`n[*] Processing $($pkgs.Count) packages..."
$successCount = 0
$skippedCount = 0

foreach ($pkg in $pkgs) {
    Write-Host "  -> Disabling $pkg ... " -NoNewline
    $res = & $py (Join-Path $tools 'phone.py') "pm disable-user --user 0 $pkg" 2>&1
    $resStr = ($res -join ' ').Trim()

    if ($resStr -match 'new state: disabled') {
        Write-Host "[DISABLED]" -ForegroundColor Green
        $successCount++
    } elseif ($resStr -match 'not installed' -or $resStr -match 'unknown package') {
        Write-Host "[NOT INSTALLED]" -ForegroundColor Gray
        $skippedCount++
    } else {
        Write-Host "[$resStr]" -ForegroundColor Yellow
        $successCount++
    }
}

Write-Host "`n[*] Syncing disk cache on device..."
& $py (Join-Path $tools 'phone.py') "sync" | Out-Null

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Debloat complete!" -ForegroundColor Green
Write-Host " Processed: $($pkgs.Count) | Modified: $successCount | Not present on device: $skippedCount" -ForegroundColor Green
Write-Host " To restore at any time, run:" -ForegroundColor White
Write-Host "   .\tools\restore.ps1 $List" -ForegroundColor Yellow
Write-Host "=========================================================="
