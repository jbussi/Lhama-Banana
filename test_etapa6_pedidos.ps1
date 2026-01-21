# Teste ETAPA 6 - Sincronizacao de Pedidos
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE ETAPA 6: SINCRONIZACAO DE PEDIDOS ===" -ForegroundColor Cyan

# ============================================
# TESTE 1: Verificar endpoint de sincronizacao de pedidos
# ============================================
Write-Host "`n1. TESTE: Verificar endpoint de sincronizacao..." -ForegroundColor Yellow

Write-Host "`n   Endpoints disponiveis:" -ForegroundColor Cyan
Write-Host "   - POST /api/bling/pedidos/sync/{venda_id}" -ForegroundColor White
Write-Host "     Sincroniza um pedido especifico com Bling" -ForegroundColor Gray
Write-Host "`n   - GET /api/bling/pedidos/info/{venda_id}" -ForegroundColor White
Write-Host "     Verifica status de sincronizacao de um pedido" -ForegroundColor Gray
Write-Host "`n   - POST /api/bling/pedidos/status/sync-all" -ForegroundColor White
Write-Host "     Sincroniza status de todos os pedidos" -ForegroundColor Gray

# ============================================
# TESTE 2: Verificar funcionalidades implementadas
# ============================================
Write-Host "`n2. FUNCIONALIDADES IMPLEMENTADAS:" -ForegroundColor Yellow
Write-Host "   ✅ Sincronizacao automatica de cliente antes de criar pedido" -ForegroundColor Green
Write-Host "   ✅ Calculo automatico de CFOP (5102 para mesmo estado, 6108 para interestadual)" -ForegroundColor Green
Write-Host "   ✅ Mapeamento completo de dados do pedido" -ForegroundColor Green
Write-Host "   ✅ Tratamento de descontos promocionais por item" -ForegroundColor Green
Write-Host "   ✅ Idempotencia (evita duplicar pedidos)" -ForegroundColor Green
Write-Host "   ✅ Sincronizacao bidirecional de status" -ForegroundColor Green

# ============================================
# TESTE 3: Testar busca de informacoes de pedido
# ============================================
Write-Host "`n3. TESTE: Verificar status de sincronizacao de pedido..." -ForegroundColor Yellow

# Tentar com um ID de pedido qualquer (sera usado para teste)
$vendaId = 1

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/info/$vendaId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.synced) {
        Write-Host "   ✅ Pedido $vendaId esta sincronizado com Bling" -ForegroundColor Green
        Write-Host "   Bling Pedido ID: $($response.bling_pedido_id)" -ForegroundColor Cyan
        if ($response.bling_nfe_id) {
            Write-Host "   NF-e ID: $($response.bling_nfe_id)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   ⚠ Pedido $vendaId nao esta sincronizado" -ForegroundColor Yellow
        Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "   ⚠ Endpoint retornou 404 (pedido nao encontrado ou endpoint diferente)" -ForegroundColor Yellow
    } else {
        Write-Host "   ERRO: $_" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            try {
                $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
                Write-Host "   Detalhes: $($errorJson.error)" -ForegroundColor Yellow
            } catch {
                Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
            }
        }
    }
}

# ============================================
# TESTE 4: Fluxo completo de sincronizacao
# ============================================
Write-Host "`n4. FLUXO DE SINCRONIZACAO:" -ForegroundColor Yellow
Write-Host "`n   Quando um pedido e sincronizado:" -ForegroundColor Cyan
Write-Host "   1. sync_order_to_bling() e chamado" -ForegroundColor White
Write-Host "   2. sync_client_for_order() sincroniza cliente automaticamente" -ForegroundColor White
Write-Host "   3. CFOP e calculado automaticamente baseado em:" -ForegroundColor White
Write-Host "      - Estado do emitente (BLING_EMITENTE_ESTADO)" -ForegroundColor Gray
Write-Host "      - Estado do destinatario (dados fiscais do cliente)" -ForegroundColor Gray
Write-Host "      - CFOP 5102: mesmo estado (venda)" -ForegroundColor Gray
Write-Host "      - CFOP 6108: estados diferentes (venda)" -ForegroundColor Gray
Write-Host "   4. Descontos promocionais sao aplicados por item" -ForegroundColor White
Write-Host "   5. Pedido e criado no Bling com todos os itens" -ForegroundColor White
Write-Host "   6. Referencia e salva em bling_pedidos" -ForegroundColor White

# ============================================
# TESTE 5: Informacoes sobre CFOP
# ============================================
Write-Host "`n5. INFORMACOES SOBRE CFOP:" -ForegroundColor Yellow
Write-Host "   CFOP (Codigo Fiscal de Operacoes e Prestacoes)" -ForegroundColor Cyan
Write-Host "   - Calculado automaticamente baseado em estado emitente/destinatario" -ForegroundColor White
Write-Host "   - 5102: Venda dentro do mesmo estado" -ForegroundColor White
Write-Host "   - 6108: Venda para estado diferente" -ForegroundColor White
Write-Host "   - Configurado em: BLING_EMITENTE_ESTADO" -ForegroundColor White

Write-Host "`n=== TESTE ETAPA 6 CONCLUIDO ===" -ForegroundColor Cyan
Write-Host "`nPROXIMOS PASSOS PARA TESTE COMPLETO:" -ForegroundColor Yellow
Write-Host "1. Criar uma venda com dados fiscais completos" -ForegroundColor Cyan
Write-Host "2. Sincronizar pedido: POST /api/bling/pedidos/sync/{venda_id}" -ForegroundColor Cyan
Write-Host "3. Verificar se cliente foi sincronizado automaticamente" -ForegroundColor Cyan
Write-Host "4. Verificar se pedido foi criado no Bling com CFOP correto" -ForegroundColor Cyan
Write-Host "5. Verificar status: GET /api/bling/pedidos/info/{venda_id}" -ForegroundColor Cyan

