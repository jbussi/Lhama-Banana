# Teste de debug - Estoque Local -> Bling
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== DEBUG: SINCRONIZACAO LOCAL -> BLING ===" -ForegroundColor Cyan

$produtoId = 6

Write-Host "`nTestando produto ID: $produtoId" -ForegroundColor Yellow

try {
    $body = @{
        produto_id = $produtoId
    } | ConvertTo-Json
    
    Write-Host "`nEnviando requisição..." -ForegroundColor Cyan
    $response = Invoke-WebRequest -Uri "$ngrokUrl/api/bling/estoque/sync-to-bling" `
        -Method POST -Headers $headers `
        -Body $body -ContentType "application/json" -ErrorAction Stop
    
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Cyan
    Write-Host "`nResposta completa:" -ForegroundColor Yellow
    $result = $response.Content | ConvertFrom-Json
    $result | ConvertTo-Json -Depth 10 | Write-Host
    
    Write-Host "`nAnalise:" -ForegroundColor Yellow
    Write-Host "  success (tipo): $($result.success.GetType().Name)" -ForegroundColor Cyan
    Write-Host "  success (valor): $($result.success)" -ForegroundColor Cyan
    Write-Host "  total: $($result.total)" -ForegroundColor Cyan
    Write-Host "  errors: $($result.errors)" -ForegroundColor Cyan
    
    if ($result.results) {
        Write-Host "`nResultados individuais:" -ForegroundColor Yellow
        foreach ($r in $result.results) {
            Write-Host "  Produto $($r.produto_id): success=$($r.success), estoque_enviado=$($r.estoque_enviado)" -ForegroundColor Cyan
        }
    }
    
} catch {
    Write-Host "`nERRO: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Detalhes:" -ForegroundColor Yellow
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            $errorJson | ConvertTo-Json -Depth 10 | Write-Host
        } catch {
            Write-Host $_.ErrorDetails.Message
        }
    }
    Write-Host "`nException completa:" -ForegroundColor Yellow
    $_.Exception | Format-List | Write-Host
}

