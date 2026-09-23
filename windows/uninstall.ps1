$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:LOCALAPPDATA "FileSentry"
$BinDir = Join-Path $env:USERPROFILE ".local\bin"
$Launcher = Join-Path $BinDir "sentry.cmd"

if (Test-Path $Launcher) {
    Remove-Item -Force $Launcher
}

if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
}

Write-Host "FileSentry removed."
Write-Host "The ~/.local/bin PATH entry is left in place because other tools may use it."
