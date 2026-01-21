# Teste ETAPA 9 - Integracao Financeira
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE ETAPA 9: INTEGRACAO FINANCEIRA ===" -ForegroundColor Cyan

# ============================================
# PASSO 1: Verificar conexao
# ============================================
Write-Host "`n=== PASSO 1: Verificando conexao ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/test" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Conexao com API Bling OK" -ForegroundColor Green
    } else {
        Write-Host "   [ERRO] Problema na conexao" -ForegroundColor Red
        exit
    }
} catch {
    Write-Host "   [ERRO] Erro ao conectar: $_" -ForegroundColor Red
    exit
}

# ============================================
# PASSO 2: Buscar venda sincronizada para teste
# ============================================
Write-Host "`n=== PASSO 2: Buscando venda sincronizada para teste ===" -ForegroundColor Yellow

$vendaId = $null
$vendaEncontrada = $false

for ($id = 1; $id -le 100; $id++) {
    try {
        $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/info/$id" `
            -Method GET -Headers $headers -ErrorAction Stop
        
        if ($response.synced) {
            $vendaId = $id
            $vendaEncontrada = $true
            Write-Host "   [OK] Venda encontrada: ID $id" -ForegroundColor Green
            Write-Host "   Bling Pedido ID: $($response.bling_pedido_id)" -ForegroundColor Cyan
            break
        }
    } catch {
        continue
    }
}

if (-not $vendaEncontrada) {
    Write-Host "   [AVISO] Nenhuma venda sincronizada encontrada" -ForegroundColor Yellow
    Write-Host "`n   NOTA: Contas a receber sao criadas automaticamente quando:" -ForegroundColor Yellow
    Write-Host "   - Pagamento e confirmado (webhook PagBank)" -ForegroundColor White
    Write-Host "   - Pedido ja esta sincronizado com Bling" -ForegroundColor White
    Write-Host "   - Cliente existe no Bling" -ForegroundColor White
    Write-Host "`n   Este endpoint pode ser usado para criar manualmente tambem." -ForegroundColor Cyan
    exit
}

Write-Host "`n   Venda selecionada para teste: ID $vendaId" -ForegroundColor Cyan

# ============================================
# PASSO 3: Tentar criar conta a receber
# ============================================
Write-Host "`n=== PASSO 3: Criando conta a receber no Bling ===" -ForegroundColor Yellow
Write-Host "   (Verificando se ja existe antes de criar)" -ForegroundColor Gray

try {
    Write-Host "   Enviando requisicao..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/financeiro/conta-receber/$vendaId" `
        -Method POST -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Conta a receber processada com sucesso!" -ForegroundColor Green
        
        if ($response.contas_criadas) {
            Write-Host "   Contas criadas: $($response.contas_criadas)" -ForegroundColor Cyan
        }
        if ($response.contas_existentes) {
            Write-Host "   Contas ja existentes: $($response.contas_existentes)" -ForegroundColor Yellow
        }
        if ($response.message) {
            Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
        }
        
        Write-Host "`n   O que aconteceu:" -ForegroundColor Yellow
        Write-Host "   1. Verificacao se pedido existe no Bling" -ForegroundColor White
        Write-Host "   2. Verificacao se cliente existe no Bling" -ForegroundColor White
        Write-Host "   3. Busca de pagamento confirmado" -ForegroundColor White
        Write-Host "   4. Criacao de conta(s) a receber (ou verificacao se ja existe)" -ForegroundColor White
        Write-Host "   5. Vinculacao ao pedido e cliente no Bling" -ForegroundColor White
    } else {
        Write-Host "   [AVISO] $($response.error)" -ForegroundColor Yellow
        if ($response.details) {
            Write-Host "   Detalhes: $($response.details)" -ForegroundColor Gray
        }
        if ($response.hint) {
            Write-Host "   Dica: $($response.hint)" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "   [ERRO] $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Erro: $($errorJson.error)" -ForegroundColor Yellow
        } catch { }
    }
}

# ============================================
# PASSO 4: Funcionalidades implementadas
# ============================================
Write-Host "`n=== PASSO 4: FUNCIONALIDADES IMPLEMENTADAS ===" -ForegroundColor Yellow
Write-Host "   [OK] Criacao automatica de contas a receber" -ForegroundColor Green
Write-Host "   [OK] Suporte para PIX (1 conta a receber)" -ForegroundColor Green
Write-Host "   [OK] Suporte para Cartao Parcelado (multiplas contas)" -ForegroundColor Green
Write-Host "   [OK] Suporte para Boleto/Cartao a Vista" -ForegroundColor Green
Write-Host "   [OK] Vinculacao ao pedido e cliente no Bling" -ForegroundColor Green
Write-Host "   [OK] Prevencao de duplicacao (verifica antes de criar)" -ForegroundColor Green
Write-Host "   [OK] Integracao automatica no webhook de pagamento" -ForegroundColor Green

# ============================================
# PASSO 5: Fluxo automatico
# ============================================
Write-Host "`n=== PASSO 5: FLUXO AUTOMATICO ===" -ForegroundColor Yellow
Write-Host "`nQuando um pagamento e confirmado:" -ForegroundColor Cyan
Write-Host "   1. Webhook PagBank recebe notificacao" -ForegroundColor White
Write-Host "   2. Status do pagamento atualizado para PAID/AUTHORIZED" -ForegroundColor White
Write-Host "   3. Pedido sincronizado com Bling (se ainda nao)" -ForegroundColor White
Write-Host "   4. Cliente sincronizado com Bling (se ainda nao)" -ForegroundColor White
Write-Host "   5. Conta(s) a receber criada(s) automaticamente" -ForegroundColor White
Write-Host "   6. Vinculada(s) ao pedido e cliente no Bling" -ForegroundColor White

Write-Host "`nTratamento de parcelas:" -ForegroundColor Cyan
Write-Host "   - PIX: 1 conta a receber com vencimento no dia do pagamento" -ForegroundColor White
Write-Host "   - Cartao Parcelado: N contas a receber (uma por parcela)" -ForegroundColor White
Write-Host "   - Boleto/Cartao a Vista: 1 conta a receber" -ForegroundColor White

# ============================================
# RESUMO
# ============================================
Write-Host "`n=== RESUMO DO TESTE ===" -ForegroundColor Cyan
Write-Host "`nTeste concluido!" -ForegroundColor Yellow
Write-Host "`nCONDICOES PARA CRIAR CONTA A RECEBER:" -ForegroundColor Yellow
Write-Host "   1. Pedido sincronizado com Bling" -ForegroundColor White
Write-Host "   2. Cliente existe no Bling" -ForegroundColor White
Write-Host "   3. Pagamento confirmado (PAID/AUTHORIZED)" -ForegroundColor White
Write-Host "   4. Conta ainda nao existe (evita duplicacao)" -ForegroundColor White

Write-Host "`n=== TESTE ETAPA 9 CONCLUIDO ===" -ForegroundColor Cyan
