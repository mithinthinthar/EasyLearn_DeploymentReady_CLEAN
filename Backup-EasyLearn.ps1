$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectParent = Split-Path -Parent $ProjectRoot
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupParent = Join-Path $ProjectParent "EasyLearn_Backups"
$BackupRoot = Join-Path $BackupParent "EasyLearn_Backup_$Timestamp"
$ProjectBackup = Join-Path $BackupRoot "project"
$DatabaseBackup = Join-Path $BackupRoot "database"
$DatabaseFile = Join-Path $DatabaseBackup "mathsy_db.sql"
$ManifestFile = Join-Path $BackupRoot "BACKUP-MANIFEST.txt"

function Stop-Backup {
    param([string]$Message)

    Write-Host ""
    Write-Host "BACKUP STOPPED" -ForegroundColor Red
    Write-Host $Message -ForegroundColor Yellow
    Write-Host "Your working EasyLearn project was not changed." -ForegroundColor White
    Read-Host "Press Enter to close"
    exit 1
}

function Get-CommandVersion {
    param([string]$Command, [string[]]$Arguments)

    try {
        $result = & $Command @Arguments 2>&1 | Select-Object -First 1
        return [string]$result
    } catch {
        return "Not available"
    }
}

Write-Host ""
Write-Host "EasyLearn backup" -ForegroundColor Cyan
Write-Host "================" -ForegroundColor DarkCyan
Write-Host "Project: $ProjectRoot"
Write-Host "Backup:  $BackupRoot"
Write-Host ""

$requiredProjectItems = @(
    "subjects\history",
    "subjects\mathematics",
    "subjects\bahasa_melayu",
    "portal",
    "Start-EasyLearn.cmd"
)

$missingItems = @()
foreach ($relativePath in $requiredProjectItems) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $relativePath))) {
        $missingItems += $relativePath
    }
}

if ($missingItems.Count -gt 0) {
    $list = $missingItems -join ", "
    Stop-Backup "This script must be inside the EasyLearn_Combined root. Missing: $list"
}

$mysqlService = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
if ($null -eq $mysqlService) {
    Stop-Backup "The MySQL80 Windows service was not found."
}
if ($mysqlService.Status -ne "Running") {
    Stop-Backup "MySQL80 is not running. Start it and run this backup again."
}

$dumpCommand = Get-Command "mysqldump.exe" -ErrorAction SilentlyContinue
$dumpPath = if ($null -ne $dumpCommand) {
    $dumpCommand.Source
} else {
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
}

if (-not (Test-Path -LiteralPath $dumpPath)) {
    Stop-Backup "mysqldump.exe was not found. Confirm MySQL Server 8.0 is installed."
}

$dbUser = Read-Host "MySQL username [root]"
if ([string]::IsNullOrWhiteSpace($dbUser)) {
    $dbUser = "root"
}

try {
    New-Item -ItemType Directory -Path $ProjectBackup -Force | Out-Null
    New-Item -ItemType Directory -Path $DatabaseBackup -Force | Out-Null

    Write-Host ""
    Write-Host "Step 1 of 3: Exporting mathsy_db" -ForegroundColor Cyan
    Write-Host "MySQL will ask for the password for '$dbUser'. The password is not saved in the script." -ForegroundColor Yellow

    $dumpArguments = @(
        "--user=$dbUser",
        "--password",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--databases", "mathsy_db",
        "--result-file=$DatabaseFile"
    )

    & $dumpPath @dumpArguments
    if ($LASTEXITCODE -ne 0) {
        throw "mysqldump returned exit code $LASTEXITCODE. Check the MySQL password and try again."
    }
    if (-not (Test-Path -LiteralPath $DatabaseFile)) {
        throw "The database export file was not created."
    }
    if ((Get-Item -LiteralPath $DatabaseFile).Length -lt 100) {
        throw "The database export is unexpectedly small and may be incomplete."
    }

    Write-Host "Database export completed." -ForegroundColor Green
    Write-Host ""
    Write-Host "Step 2 of 3: Copying project source and local data" -ForegroundColor Cyan

    $excludedDirectories = @(
        "node_modules",
        ".venv",
        "venv",
        "build",
        "dist",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache"
    )

    $robocopyArguments = @(
        $ProjectRoot,
        $ProjectBackup,
        "/E",
        "/COPY:DAT",
        "/DCOPY:T",
        "/R:1",
        "/W:1",
        "/XJ",
        "/NFL",
        "/NDL",
        "/NP",
        "/XD"
    ) + $excludedDirectories + @(
        "/XF",
        "*.pyc",
        "*.pyo",
        "*.log"
    )

    & robocopy.exe @robocopyArguments
    $robocopyExitCode = $LASTEXITCODE
    if ($robocopyExitCode -ge 8) {
        throw "Project copy failed. Robocopy returned exit code $robocopyExitCode."
    }

    Write-Host "Project copy completed." -ForegroundColor Green
    Write-Host ""
    Write-Host "Step 3 of 3: Writing and checking the backup manifest" -ForegroundColor Cyan

    $nodeVersion = Get-CommandVersion -Command "node.exe" -Arguments @("--version")
    $npmVersion = Get-CommandVersion -Command "npm.cmd" -Arguments @("--version")
    $pythonVersion = Get-CommandVersion -Command "py.exe" -Arguments @("-3.12", "--version")
    $mysqlVersion = Get-CommandVersion -Command "mysql.exe" -Arguments @("--version")

    @(
        "EasyLearn backup manifest",
        "=========================",
        "Created: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "Original project: $ProjectRoot",
        "Project backup: $ProjectBackup",
        "Database backup: $DatabaseFile",
        "Database: mathsy_db",
        "MySQL service: $($mysqlService.Status)",
        "Node: $nodeVersion",
        "npm: $npmVersion",
        "Python 3.12: $pythonVersion",
        "MySQL client: $mysqlVersion",
        "",
        "Excluded replaceable folders:",
        "node_modules, .venv, venv, build, dist, .git, __pycache__",
        "",
        "Important: This backup may contain .env files or service credentials.",
        "Keep it private and do not upload it to a public repository."
    ) | Set-Content -LiteralPath $ManifestFile -Encoding UTF8

    $verificationItems = @(
        (Join-Path $ProjectBackup "subjects\history"),
        (Join-Path $ProjectBackup "subjects\mathematics"),
        (Join-Path $ProjectBackup "subjects\bahasa_melayu"),
        (Join-Path $ProjectBackup "portal\index.html"),
        $DatabaseFile,
        $ManifestFile
    )

    $verificationFailures = @($verificationItems | Where-Object { -not (Test-Path -LiteralPath $_) })
    if ($verificationFailures.Count -gt 0) {
        throw "Backup verification failed. One or more required files are missing."
    }

    Write-Host ""
    Write-Host "BACKUP COMPLETED AND VERIFIED" -ForegroundColor Green
    Write-Host "Saved to: $BackupRoot" -ForegroundColor White
    Write-Host ""
    Write-Host "Copy this backup folder to another drive or private cloud storage for real protection." -ForegroundColor Yellow

    Start-Process -FilePath "explorer.exe" -ArgumentList @($BackupRoot)
    Read-Host "Press Enter to close"
} catch {
    Stop-Backup $_.Exception.Message
}

