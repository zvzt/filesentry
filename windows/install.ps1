$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:LOCALAPPDATA "FileSentry"
$BinDir = Join-Path $env:USERPROFILE ".local\bin"
$ScriptPath = Join-Path $InstallDir "sentry.py"
$Launcher = Join-Path $BinDir "sentry.cmd"
$Url = "https://zxt.lol/sentry/windows/sentry.py"

function Find-Python {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & py -3 --version *> $null
            if ($LASTEXITCODE -eq 0) { return "py -3" }
        } catch {}
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        try {
            & python --version *> $null
            if ($LASTEXITCODE -eq 0) { return "python" }
        } catch {}
    }

    return $null
}

$Python = Find-Python

if (-not $Python) {
    Write-Host "FileSentry requires Python 3."
    Write-Host "Install it with:"
    Write-Host "  winget install Python.Python.3.13"
    exit 1
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

$TempFile = Join-Path $env:TEMP ("filesentry-" + [guid]::NewGuid().ToString() + ".py")

try {
    Write-Host "Downloading FileSentry..."
    Invoke-WebRequest -UseBasicParsing -Uri $Url -OutFile $TempFile

    if ($Python -eq "py -3") {
        & py -3 -m py_compile $TempFile
    } else {
        & python -m py_compile $TempFile
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Downloaded FileSentry failed Python syntax validation."
    }

    Move-Item -Force $TempFile $ScriptPath
} finally {
    if (Test-Path $TempFile) {
        Remove-Item -Force $TempFile
    }
}

$NL = [Environment]::NewLine
if ($Python -eq "py -3") {
    $LauncherText = '@echo off' + $NL + 'py -3 "' + $ScriptPath + '" %*' + $NL
} else {
    $LauncherText = '@echo off' + $NL + 'python "' + $ScriptPath + '" %*' + $NL
}

Set-Content -Path $Launcher -Value $LauncherText -Encoding ASCII

$UserPath = [Environment]::GetEnvironmentVariable("Path","User")
$Parts = @()
if ($UserPath) {
    $Parts = $UserPath.Split(";") | Where-Object { $_ }
}

if ($Parts -notcontains $BinDir) {
    $NewPath = (($Parts + $BinDir) -join ";")
    [Environment]::SetEnvironmentVariable("Path",$NewPath,"User")
}

if (($env:Path.Split(";")) -notcontains $BinDir) {
    $env:Path = "$BinDir;$env:Path"
}

Write-Host ""
Write-Host "FileSentry installed."
Write-Host "Run:"
Write-Host "  sentry"
Write-Host ""
Write-Host "If 'sentry' is not found in an older terminal window, close it and open a new PowerShell/Terminal window."
