param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$PatchRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Applying EasyLearn Vercel patch to: $ProjectRoot" -ForegroundColor Cyan

Get-ChildItem -Path $PatchRoot -Recurse -File | Where-Object {
    $_.FullName -ne $MyInvocation.MyCommand.Path
} | ForEach-Object {
    $relative = $_.FullName.Substring($PatchRoot.Length).TrimStart('\\','/')
    $target = Join-Path $ProjectRoot $relative
    $targetDir = Split-Path -Parent $target
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
    }
    Copy-Item -Force $_.FullName $target
    Write-Host "Updated: $relative"
}

Write-Host "Vercel patch applied successfully." -ForegroundColor Green
