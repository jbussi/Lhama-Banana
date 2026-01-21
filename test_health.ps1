# Teste simples de health check
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

$headers = @{
    "ngrok-skip-browser-warning" = "true"
    "Content-Type" = "application/json"
}

Write-Host "Testando conectividade com o servidor..." -ForegroundColor Yellow
Write-Host "URL: $ngrokUrl" -ForegroundColor Gray
Write-Host ""

# Testar endpoint raiz ou health
try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/health" -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "[OK] Servidor esta respondendo!" -ForegroundColor Green
    Write-Host "Resposta: $($response | ConvertTo-Json)" -ForegroundColor Gray
} catch {
    Write-Host "[ERRO] Servidor nao esta respondendo" -ForegroundColor Red
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Verifique:" -ForegroundColor Yellow
    Write-Host "  1. O Flask esta rodando?" -ForegroundColor Gray
    Write-Host "  2. O ngrok esta ativo?" -ForegroundColor Gray
    Write-Host "  3. A URL do ngrok esta correta?" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Testando endpoint de status do Bling..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/tokens" -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "[OK] Endpoint Bling esta funcionando!" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Endpoint Bling nao esta respondendo" -ForegroundColor Red
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Gray
}
