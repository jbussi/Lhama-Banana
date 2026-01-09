# Script de Teste Completo - Integração Bling
# ===========================================

# Configurar URL
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "🧪 Testando Integração Bling" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

# 1. Verificar tokens
Write-Host "`n1. Verificando tokens..." -ForegroundColor Yellow
try {
    $uri = "$ngrokUrl/api/bling/tokens"
    $tokens = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "   Autorizado: $($tokens.authorized)" -ForegroundColor $(if($tokens.authorized){"Green"}else{"Red"})
    if ($tokens.authorized) {
        Write-Host "   Token expira em: $($tokens.expires_at)" -ForegroundColor Cyan
    } else {
        Write-Host "   ⚠️  Bling não autorizado. Acesse: $ngrokUrl/api/bling/authorize" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erro ao verificar tokens: $_" -ForegroundColor Red
}

# 2. Testar conexão
Write-Host "`n2. Testando conexão com API Bling..." -ForegroundColor Yellow
try {
    $uri = "$ngrokUrl/api/bling/test"
    $test = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "   Status: $($test.message)" -ForegroundColor $(if($test.success){"Green"}else{"Red"})
    if ($test.success) {
        Write-Host "   Status Code: $($test.status_code)" -ForegroundColor Cyan
        Write-Host "   Produtos encontrados: $($test.products_count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ❌ Erro ao testar conexão: $_" -ForegroundColor Red
}

# 3. Verificar status da integração
Write-Host "`n3. Verificando status da integração..." -ForegroundColor Yellow
try {
    $uri = "$ngrokUrl/api/bling/status"
    $status = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "   Client ID configurado: $($status.client_id_configured)" -ForegroundColor $(if($status.client_id_configured){"Green"}else{"Red"})
    Write-Host "   Client Secret configurado: $($status.client_secret_configured)" -ForegroundColor $(if($status.client_secret_configured){"Green"}else{"Red"})
} catch {
    Write-Host "   ❌ Erro ao verificar status: $_" -ForegroundColor Red
}

# 4. Sincronizar produto (se autorizado)
Write-Host "`n4. Testando sincronização de produto..." -ForegroundColor Yellow
try {
    $uri = "$ngrokUrl/api/bling/produtos/sync/6"
    $result = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -ContentType "application/json" -ErrorAction Stop
    if ($result.success) {
        Write-Host "   ✅ Produto sincronizado com sucesso!" -ForegroundColor Green
        Write-Host "   Ação: $($result.action)" -ForegroundColor Cyan
        Write-Host "   Bling ID: $($result.bling_id)" -ForegroundColor Cyan
    } else {
        Write-Host "   ⚠️  Falha: $($result.error)" -ForegroundColor Yellow
        if ($result.details) {
            foreach ($detail in $result.details) {
                Write-Host "      - $detail" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "   ❌ Erro: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Verificar status do produto
Write-Host "`n5. Verificando status do produto 6..." -ForegroundColor Yellow
try {
    $uri = "$ngrokUrl/api/bling/produtos/status/6"
    $status = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
    if ($status.synced) {
        Write-Host "   ✅ Produto sincronizado" -ForegroundColor Green
        Write-Host "   Bling ID: $($status.bling_id)" -ForegroundColor Cyan
        Write-Host "   Bling Código: $($status.bling_codigo)" -ForegroundColor Cyan
        Write-Host "   Status: $($status.status)" -ForegroundColor Cyan
    } else {
        Write-Host "   ⚠️  Produto não sincronizado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Erro: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ Testes concluídos!" -ForegroundColor Green
Write-Host "`n💡 Próximos passos:" -ForegroundColor Cyan
Write-Host "   - Testar sincronização de estoque" -ForegroundColor White
Write-Host "   - Testar sincronização de pedidos" -ForegroundColor White
Write-Host "   - Verificar logs no banco: SELECT * FROM bling_sync_logs ORDER BY created_at DESC LIMIT 10" -ForegroundColor White

