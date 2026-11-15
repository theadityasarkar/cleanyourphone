# Downloads Google Android SDK Platform-Tools (ADB & Fastboot) for Windows
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$destDir = Join-Path $repo 'tools\platform-tools'
$zipFile = Join-Path $repo 'tools\platform-tools.zip'
$url = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'

if (Test-Path (Join-Path $destDir 'adb.exe')) {
    Write-Host "[OK] ADB is already installed at: $destDir\adb.exe"
    exit 0
}

Write-Host "Downloading Android SDK Platform-Tools from Google..."
Invoke-WebRequest -Uri $url -OutFile $zipFile -UseBasicParsing

Write-Host "Extracting to tools\..."
Expand-Archive -Path $zipFile -DestinationPath (Join-Path $repo 'tools') -Force
Remove-Item -Path $zipFile -Force

if (Test-Path (Join-Path $destDir 'adb.exe')) {
    Write-Host "[SUCCESS] adb.exe is ready at $destDir\adb.exe"
} else {
    Write-Error "Failed to install adb.exe"
}
