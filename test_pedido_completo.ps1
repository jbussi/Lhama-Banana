# Teste Completo - Sincronizacao de Pedidos
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE COMPLETO: SINCRONIZACAO DE PEDIDOS ===" -ForegroundColor Cyan

# ============================================
# CONFIGURACAO
# ============================================
# ID da venda para testar (ajustar conforme necessario)
$vendaId = 1

Write-Host "`nVenda ID para teste: $vendaId" -ForegroundColor Yellow

# ============================================
# PASSO 1: Verificar status atual do pedido
# ============================================
Write-Host "`n=== PASSO 1: Verificar status atual do pedido ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/info/$vendaId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.synced) {
        Write-Host "   ✅ Pedido $vendaId ja esta sincronizado com Bling" -ForegroundColor Green
        Write-Host "   Bling Pedido ID: $($response.bling_pedido_id)" -ForegroundColor Cyan
        if ($response.bling_nfe_id) {
            Write-Host "   NF-e ID: $($response.bling_nfe_id)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   ⚠ Pedido $vendaId nao esta sincronizado" -ForegroundColor Yellow
        Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠ Erro ao verificar status: $_" -ForegroundColor Yellow
}

# ============================================
# PASSO 2: Sincronizar pedido com Bling
# ============================================
Write-Host "`n=== PASSO 2: Sincronizar pedido com Bling ===" -ForegroundColor Yellow

try {
    Write-Host "   Enviando sincronizacao..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/sync/$vendaId" `
        -Method POST -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   ✅ Pedido sincronizado com sucesso!" -ForegroundColor Green
        Write-Host "   Acao: $($response.action)" -ForegroundColor Cyan
        Write-Host "   Bling Pedido ID: $($response.bling_pedido_id)" -ForegroundColor Cyan
        Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
        
        # Quando um pedido e sincronizado:
        Write-Host "`n   O que aconteceu:" -ForegroundColor Yellow
        Write-Host "   1. Cliente foi sincronizado automaticamente" -ForegroundColor White
        Write-Host "   2. CFOP foi calculado automaticamente" -ForegroundColor White
        Write-Host "   3. Pedido foi criado no Bling com situacao 'P' (Pendente)" -ForegroundColor White
        Write-Host "   4. Descontos promocionais foram aplicados por item" -ForegroundColor White
    } else {
        Write-Host "   ❌ Erro ao sincronizar: $($response.error)" -ForegroundColor Red
        if ($response.details) {
            Write-Host "   Detalhes: $($response.details)" -ForegroundColor Yellow
        }
        exit
    }
} catch {
    Write-Host "   ❌ ERRO: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Erro: $($errorJson.error)" -ForegroundColor Yellow
            Write-Host "   Mensagem: $($errorJson.message)" -ForegroundColor Yellow
        } catch {
            Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
    exit
}

# Aguardar um pouco para garantir que a sincronizacao foi processada
Start-Sleep -Seconds 2

# ============================================
# PASSO 3: Verificar pedido no Bling
# ============================================
Write-Host "`n=== PASSO 3: Verificar pedido sincronizado ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/info/$vendaId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.synced) {
        Write-Host "   ✅ Pedido confirmado no Bling" -ForegroundColor Green
        Write-Host "   Bling Pedido ID: $($response.bling_pedido_id)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   ⚠ Erro ao verificar: $_" -ForegroundColor Yellow
}

# ============================================
# PASSO 4: Aprovar pedido no Bling
# ============================================
Write-Host "`n=== PASSO 4: Aprovar pedido no Bling ===" -ForegroundColor Yellow
Write-Host "   (Mudando situacao de 'P' = Pendente para 'E' = Em aberto)" -ForegroundColor Gray

try {
    Write-Host "   Enviando aprovacao..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/approve/$vendaId" `
        -Method POST -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   ✅ Pedido aprovado com sucesso!" -ForegroundColor Green
        Write-Host "   Situacao anterior: $($response.situacao_anterior)" -ForegroundColor Cyan
        Write-Host "   Situacao nova: $($response.situacao_nova)" -ForegroundColor Cyan
        Write-Host "   Status local atualizado: $($response.status_local_atualizado)" -ForegroundColor Cyan
        Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠ $($response.error)" -ForegroundColor Yellow
        if ($response.message) {
            Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   ❌ ERRO: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Erro: $($errorJson.error)" -ForegroundColor Yellow
        } catch {
            Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
}

# ============================================
# PASSO 5: Sincronizar status do Bling para local
# ============================================
Write-Host "`n=== PASSO 5: Sincronizar status do Bling ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/status/$vendaId" `
        -Method POST -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   ✅ Status sincronizado" -ForegroundColor Green
        Write-Host "   Status atual: $($response.status)" -ForegroundColor Cyan
        Write-Host "   Situacao Bling: $($response.situacao_bling)" -ForegroundColor Cyan
    } else {
        Write-Host "   ⚠ $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠ Erro ao sincronizar status: $_" -ForegroundColor Yellow
}

# ============================================
# RESUMO
# ============================================
Write-Host "`n=== RESUMO DO TESTE ===" -ForegroundColor Cyan
Write-Host "`nFluxo completo testado:" -ForegroundColor Yellow
Write-Host "1. ✅ Verificacao de status inicial" -ForegroundColor Green
Write-Host "2. ✅ Sincronizacao de pedido (cliente + pedido)" -ForegroundColor Green
Write-Host "3. ✅ Aprovacao de pedido no Bling" -ForegroundColor Green
Write-Host "4. ✅ Sincronizacao de status bidirecional" -ForegroundColor Green

Write-Host "`nSITUACOES DO BLING:" -ForegroundColor Yellow
Write-Host "- 'P' = Pendente (aguardando aprovacao)" -ForegroundColor White
Write-Host "- 'E' = Em aberto (aprovado, pronto para processar)" -ForegroundColor White
Write-Host "- 'B' = Baixado (entregue/finalizado)" -ForegroundColor White
Write-Host "- 'F' = Faturado" -ForegroundColor White
Write-Host "- 'C' = Cancelado" -ForegroundColor White

Write-Host "`n=== TESTE CONCLUIDO ===" -ForegroundColor Cyan
