# Script PowerShell para testar sincronização de produto
# Execute após iniciar o Flask

Write-Host "🧪 Testando Sincronização de Produto com Bling" -ForegroundColor Cyan
Write-Host "=" * 60

$produtoId = 6
$baseUrl = "http://localhost:5000"

# Testar sincronização
Write-Host "`n📤 Sincronizando produto ID: $produtoId" -ForegroundColor Yellow
try {
    $uri = "$baseUrl/api/bling/produtos/sync/$produtoId"
    $headers = @{
        "Content-Type" = "application/json"
    }
    if ($useNgrok) {
        $headers["ngrok-skip-browser-warning"] = "true"
    }
    $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -ErrorAction Stop
    
    Write-Host "✅ Resposta:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
    if ($response.success) {
        Write-Host "`n🎉 Sincronização bem-sucedida!" -ForegroundColor Green
        Write-Host "   Bling ID: $($response.bling_id)" -ForegroundColor Cyan
        Write-Host "   Ação: $($response.action)" -ForegroundColor Cyan
    } else {
        Write-Host "`n❌ Erro na sincronização:" -ForegroundColor Red
        Write-Host "   $($response.error)" -ForegroundColor Red
        if ($response.details) {
            foreach ($detail in $response.details) {
                Write-Host "   - $detail" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "`n❌ Erro ao fazer requisição:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`n💡 Certifique-se de que o Flask está rodando:" -ForegroundColor Yellow
    Write-Host "   python app.py" -ForegroundColor Cyan
    Write-Host "   ou" -ForegroundColor Cyan
    Write-Host "   python -m flask run" -ForegroundColor Cyan
    exit 1
}

# Verificar status
Write-Host "`n📋 Verificando status..." -ForegroundColor Yellow
try {
    $uri = "$baseUrl/api/bling/produtos/status/$produtoId"
    $headers = @{}
    if ($useNgrok) {
        $headers["ngrok-skip-browser-warning"] = "true"
    }
    $status = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
    
    if ($status.synced) {
        Write-Host "✅ Produto sincronizado:" -ForegroundColor Green
        Write-Host "   Bling ID: $($status.bling_id)" -ForegroundColor Cyan
        Write-Host "   Bling Código: $($status.bling_codigo)" -ForegroundColor Cyan
        Write-Host "   Status: $($status.status)" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  Produto não sincronizado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Não foi possível verificar status: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "`n" + ("=" * 60)
Write-Host "✅ Teste concluído!" -ForegroundColor Green

