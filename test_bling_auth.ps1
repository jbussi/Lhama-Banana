# Teste de autenticacao Bling
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

$headers = @{
    "ngrok-skip-browser-warning" = "true"
    "Content-Type" = "application/json"
}

Write-Host "Verificando autenticacao Bling..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/tokens" -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "[OK] Bling esta autenticado!" -ForegroundColor Green
    Write-Host "Token expira em: $($response.expires_at)" -ForegroundColor Gray
} catch {
    Write-Host "[ERRO] Bling nao esta autenticado ou erro ao verificar" -ForegroundColor Red
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Para autenticar:" -ForegroundColor Yellow
    Write-Host "  1. Acesse: $ngrokUrl/api/bling/authorize" -ForegroundColor Gray
    Write-Host "  2. Autorize a aplicacao no Bling" -ForegroundColor Gray
    Write-Host "  3. O callback ira salvar os tokens" -ForegroundColor Gray
}
