param(
  [int]$Vus = 10,
  [string]$Duration = '1m',
  [string]$LoomaUrl = 'http://127.0.0.1:8010',
  [string]$AuthToken = 'token-stub'
)

$env:VUS = $Vus
$env:DURATION = $Duration
$env:LOOMA_URL = $LoomaUrl
$env:AUTH_TOKEN = $AuthToken

Write-Host "Running k6 with VUS=$VUS, Duration=$Duration, LOOMA_URL=$LoomaUrl, AUTH_TOKEN=$AuthToken"

k6 run --vus $Vus --duration $Duration scripts/k6_ask_test.js
