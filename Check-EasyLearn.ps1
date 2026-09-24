$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$checks = @(
    [PSCustomObject]@{ Name = "History website"; Url = "http://127.0.0.1:3000" },
    [PSCustomObject]@{ Name = "History API"; Url = "http://127.0.0.1:5000/health" },
    [PSCustomObject]@{ Name = "Math website"; Url = "http://127.0.0.1:3001" },
    [PSCustomObject]@{ Name = "Math API"; Url = "http://127.0.0.1:5001/health" },
    [PSCustomObject]@{ Name = "Bahasa Melayu website"; Url = "http://127.0.0.1:5173" },
    [PSCustomObject]@{ Name = "Bahasa Melayu API"; Url = "http://127.0.0.1:8000/health" },
    [PSCustomObject]@{ Name = "EasyLearn main menu"; Url = "http://127.0.0.1:4000" }
)

Write-Host ""
Write-Host "EasyLearn connection check" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor DarkCyan

$failed = 0
foreach ($check in $checks) {
    try {
        $response = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 4
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            Write-Host ("[OK]      {0,-24} {1}" -f $check.Name, $check.Url) -ForegroundColor Green
        } else {
            Write-Host ("[WARNING] {0,-24} HTTP {1}" -f $check.Name, $response.StatusCode) -ForegroundColor Yellow
            $failed++
        }
    } catch {
        Write-Host ("[OFFLINE] {0,-24} {1}" -f $check.Name, $check.Url) -ForegroundColor Red
        $failed++
    }
}

$mysqlService = Get-Service -Name "MySQL80" -ErrorAction SilentlyContinue
if ($null -eq $mysqlService) {
    Write-Host "[WARNING] MySQL80 service was not found." -ForegroundColor Yellow
    $failed++
} elseif ($mysqlService.Status -eq "Running") {
    Write-Host "[OK]      MySQL80 service          Running" -ForegroundColor Green
} else {
    Write-Host ("[OFFLINE] MySQL80 service          {0}" -f $mysqlService.Status) -ForegroundColor Red
    $failed++
}

Write-Host ""
if ($failed -eq 0) {
    Write-Host "All EasyLearn services are reachable." -ForegroundColor Green
} else {
    Write-Host "$failed check(s) need attention. Look at the matching service window for the detailed error." -ForegroundColor Yellow
}

Read-Host "Press Enter to close"

