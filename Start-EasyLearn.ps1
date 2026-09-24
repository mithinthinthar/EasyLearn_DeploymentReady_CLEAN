$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$PortalUrl = "http://localhost:4000"

function Show-Heading {
    param([string]$Text)

    Write-Host ""
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ("=" * $Text.Length) -ForegroundColor DarkCyan
}

function Test-LocalPort {
    param([int]$Port)

    $connection = Get-NetTCPConnection `
        -State Listen `
        -LocalPort $Port `
        -ErrorAction SilentlyContinue

    return $null -ne $connection
}

function Start-EasyLearnWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )

    $safeTitle = $Title.Replace("'", "''")
    $safeDirectory = $WorkingDirectory.Replace("'", "''")

    $windowScript = @"
`$Host.UI.RawUI.WindowTitle = '$safeTitle'
Set-Location -LiteralPath '$safeDirectory'
Write-Host 'Starting $safeTitle...' -ForegroundColor Cyan
$Command
Write-Host ''
Write-Host '$safeTitle stopped. Read any error above before closing this window.' -ForegroundColor Yellow
Read-Host 'Press Enter to close'
"@

    $bytes = [System.Text.Encoding]::Unicode.GetBytes($windowScript)
    $encodedCommand = [Convert]::ToBase64String($bytes)

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile",
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-EncodedCommand", $encodedCommand
    ) | Out-Null
}

Show-Heading "EasyLearn startup check"

$requiredPaths = @(
    "shared\auth\.venv\Scripts\python.exe",
    "shared\auth\auth_server.py",
    "shared\auth\.env",

    "subjects\history\backend\.venv\Scripts\python.exe",
    "subjects\history\backend\history_app_local.py",
    "subjects\history\frontend\package.json",

    "subjects\mathematics\backend\.venv\Scripts\python.exe",
    "subjects\mathematics\backend\app.py",
    "subjects\mathematics\backend\math_portal_app.py",
    "subjects\mathematics\frontend\package.json",

    "subjects\bahasa_melayu\backend\.venv\Scripts\python.exe",
    "subjects\bahasa_melayu\backend\main.py",
    "subjects\bahasa_melayu\frontend\package.json",

    "portal\index.html",
    "portal\app.js",
    "portal\firebase-config.js"
)

$missingPaths = @()

foreach ($relativePath in $requiredPaths) {
    $fullPath = Join-Path $Root $relativePath

    if (-not (Test-Path -LiteralPath $fullPath)) {
        $missingPaths += $relativePath
    }
}

if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    $missingPaths += "Node.js/npm is not available in PATH"
}

if ($missingPaths.Count -gt 0) {
    Write-Host "EasyLearn cannot start because these items are missing:" `
        -ForegroundColor Red

    foreach ($item in $missingPaths) {
        Write-Host "  - $item" -ForegroundColor Red
    }

    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$mysqlService = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue

if ($null -ne $mysqlService -and $mysqlService.Status -ne "Running") {
    Write-Host "Starting MySQL80..." -ForegroundColor Yellow

    try {
        Start-Service -Name "MySQL80"
    }
    catch {
        Write-Host `
            "MySQL80 could not be started automatically. Mathematics questions and content may not load." `
            -ForegroundColor Red
    }
}

$services = @(
    [PSCustomObject]@{
        Title = "EasyLearn - Shared Authentication"
        Port = 4500
        Directory = Join-Path $Root "shared\auth"
        Command = "& '.\.venv\Scripts\python.exe' -m uvicorn 'auth_server:app' --host 127.0.0.1 --port 4500"
    },

    [PSCustomObject]@{
        Title = "EasyLearn - History API"
        Port = 5000
        Directory = Join-Path $Root "subjects\history\backend"
        Command = "& '.\.venv\Scripts\python.exe' '.\history_app_local.py'"
    },

    [PSCustomObject]@{
        Title = "EasyLearn - Mathematics API"
        Port = 5001
        Directory = Join-Path $Root "subjects\mathematics\backend"
        Command = "& '.\.venv\Scripts\python.exe' -m flask --app math_portal_app run --host 127.0.0.1 --port 5001"
    },

    [PSCustomObject]@{
        Title = "EasyLearn - Bahasa Melayu API"
        Port = 8000
        Directory = Join-Path $Root "subjects\bahasa_melayu\backend"
        Command = "& '.\.venv\Scripts\python.exe' -m uvicorn 'main:app' --host 127.0.0.1 --port 8000"
    },

    [PSCustomObject]@{
        Title = "EasyLearn - History Website"
        Port = 3000
        Directory = Join-Path $Root "subjects\history\frontend"
        Command = "`$env:HOST = '127.0.0.1'; `$env:PORT = '3000'; `$env:BROWSER = 'none'; npm.cmd start"
    },

    [PSCustomObject]@{
        Title = "EasyLearn - Mathematics Website"
        Port = 3001
        Directory = Join-Path $Root "subjects\mathematics\frontend"
        Command = "`$env:HOST = '127.0.0.1'; `$env:PORT = '3001'; `$env:BROWSER = 'none'; npm.cmd start"
    },

    [PSCustomObject]@{
        Title = "EasyLearn - Bahasa Melayu Website"
        Port = 5173
        Directory = Join-Path $Root "subjects\bahasa_melayu\frontend"
        Command = "npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort"
    },

    [PSCustomObject]@{
        Title = "EasyLearn - Main Portal"
        Port = 4000
        Directory = $Root
        Command = "& '.\shared\auth\.venv\Scripts\python.exe' -m http.server 4000 --bind 127.0.0.1 --directory '.\portal'"
    }
)

foreach ($service in $services) {
    if (Test-LocalPort -Port $service.Port) {
        Write-Host (
            "[Already running] {0} on port {1}" `
                -f $service.Title, $service.Port
        ) -ForegroundColor DarkYellow

        continue
    }

    Write-Host (
        "[Starting] {0} on port {1}" `
            -f $service.Title, $service.Port
    ) -ForegroundColor Green

    Start-EasyLearnWindow `
        -Title $service.Title `
        -WorkingDirectory $service.Directory `
        -Command $service.Command

    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host `
    "Keep the EasyLearn service windows open while using the application." `
    -ForegroundColor Yellow

Write-Host `
    "History and Mathematics may take 10-40 seconds to load their models." `
    -ForegroundColor White

Start-Sleep -Seconds 4
Start-Process $PortalUrl

Write-Host ""
Write-Host "EasyLearn launch completed: $PortalUrl" -ForegroundColor Green
Write-Host "You may close this startup-check window." -ForegroundColor White

Start-Sleep -Seconds 4
