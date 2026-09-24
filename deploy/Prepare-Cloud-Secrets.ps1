param(
    [Parameter(Mandatory=$true)][string]$FirebaseServiceAccountJson,
    [Parameter(Mandatory=$true)][string]$AivenCaPem
)

if (-not (Test-Path $FirebaseServiceAccountJson)) { throw "Firebase JSON not found: $FirebaseServiceAccountJson" }
if (-not (Test-Path $AivenCaPem)) { throw "Aiven CA not found: $AivenCaPem" }

$firebase = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path $FirebaseServiceAccountJson)))
$aiven = [Convert]::ToBase64String([IO.File]::ReadAllBytes((Resolve-Path $AivenCaPem)))

Write-Host "`nFIREBASE_SERVICE_ACCOUNT_BASE64 (copy this into Cloud Run):`n"
Write-Output $firebase
Write-Host "`nDB_SSL_CA_BASE64 (Mathematics Cloud Run only):`n"
Write-Output $aiven
Write-Host "`nDo not save these values in GitHub or send them in chat."
