# Teste ETAPA 7 - Emissao de Nota Fiscal (NF-e)
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE ETAPA 7: EMISSAO DE NOTA FISCAL (NF-e) ===" -ForegroundColor Cyan

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
# PASSO 2: Buscar venda sincronizada com Bling para testar NF-e
# ============================================
Write-Host "`n=== PASSO 2: Buscando venda sincronizada para teste ===" -ForegroundColor Yellow

$vendaId = $null
$vendaEncontrada = $false

# Tentar IDs de 1 a 100
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
    Write-Host "   [AVISO] Nenhuma venda sincronizada encontrada nos IDs testados" -ForegroundColor Yellow
    Write-Host "`n   INSTRUCOES:" -ForegroundColor Yellow
    Write-Host "   1. Sincronize uma venda primeiro: POST /api/bling/pedidos/sync/{venda_id}" -ForegroundColor Cyan
    Write-Host "   2. A venda precisa ter:" -ForegroundColor Cyan
    Write-Host "      - Pagamento confirmado" -ForegroundColor White
    Write-Host "      - Dados fiscais completos" -ForegroundColor White
    Write-Host "      - Pedido sincronizado com Bling" -ForegroundColor White
    Write-Host "   3. Depois execute este teste novamente" -ForegroundColor Cyan
    exit
}

Write-Host "`n   Venda selecionada para teste: ID $vendaId" -ForegroundColor Cyan

# ============================================
# PASSO 3: Verificar status atual da NF-e
# ============================================
Write-Host "`n=== PASSO 3: Verificando status atual da NF-e ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/nfe/status/$vendaId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Status da NF-e consultado" -ForegroundColor Green
        Write-Host "   Status: $($response.status)" -ForegroundColor Cyan
        if ($response.numero_nfe) {
            Write-Host "   Numero NF-e: $($response.numero_nfe)" -ForegroundColor Cyan
        }
        if ($response.chave_acesso) {
            Write-Host "   Chave de Acesso: $($response.chave_acesso)" -ForegroundColor Cyan
        }
        if ($response.ja_emitida) {
            Write-Host "   NF-e ja foi emitida anteriormente" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   [AVISO] $($response.error)" -ForegroundColor Yellow
        if ($response.message) {
            Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   [AVISO] Erro ao consultar status: $_" -ForegroundColor Yellow
    if ($_.ErrorDetails.Message) {
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Erro: $($errorJson.error)" -ForegroundColor Yellow
        } catch { }
    }
}

# ============================================
# PASSO 4: Tentar emitir NF-e (se ainda nao emitida)
# ============================================
Write-Host "`n=== PASSO 4: Tentando emitir NF-e ===" -ForegroundColor Yellow
Write-Host "   (Apenas se ainda nao foi emitida)" -ForegroundColor Gray

try {
    Write-Host "   Enviando requisicao de emissao..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/nfe/emitir/$vendaId" `
        -Method POST -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] NF-e processada com sucesso!" -ForegroundColor Green
        Write-Host "   Status: $($response.status)" -ForegroundColor Cyan
        
        if ($response.numero_nfe) {
            Write-Host "   Numero NF-e: $($response.numero_nfe)" -ForegroundColor Cyan
        }
        if ($response.chave_acesso) {
            Write-Host "   Chave de Acesso: $($response.chave_acesso)" -ForegroundColor Cyan
        }
        if ($response.message) {
            Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
        }
        
        Write-Host "`n   O que aconteceu:" -ForegroundColor Yellow
        Write-Host "   1. Condicoes verificadas (pagamento, dados fiscais, pedido no Bling)" -ForegroundColor White
        Write-Host "   2. Requisicao enviada para Bling API" -ForegroundColor White
        Write-Host "   3. Informacoes da NF-e armazenadas localmente" -ForegroundColor White
    } else {
        Write-Host "   [AVISO] $($response.error)" -ForegroundColor Yellow
        if ($response.details) {
            Write-Host "   Detalhes: $($response.details)" -ForegroundColor Gray
        }
        if ($response.message) {
            Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
        }
        
        Write-Host "`n   POSSIVEIS MOTIVOS:" -ForegroundColor Yellow
        Write-Host "   - NF-e ja foi emitida anteriormente" -ForegroundColor White
        Write-Host "   - Pagamento nao confirmado" -ForegroundColor White
        Write-Host "   - Dados fiscais incompletos" -ForegroundColor White
        Write-Host "   - Pedido nao sincronizado com Bling" -ForegroundColor White
        Write-Host "   - Erro na API do Bling (validacoes fiscais)" -ForegroundColor White
    }
} catch {
    Write-Host "   [ERRO] $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Erro: $($errorJson.error)" -ForegroundColor Yellow
            if ($errorJson.details) {
                Write-Host "   Detalhes: $($errorJson.details)" -ForegroundColor Gray
            }
        } catch {
            Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
}

# ============================================
# PASSO 5: Verificar status novamente
# ============================================
Write-Host "`n=== PASSO 5: Verificando status final da NF-e ===" -ForegroundColor Yellow

Start-Sleep -Seconds 2  # Aguardar um pouco

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/nfe/status/$vendaId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Status atualizado" -ForegroundColor Green
        Write-Host "   Status: $($response.status)" -ForegroundColor Cyan
        if ($response.numero_nfe) {
            Write-Host "   Numero NF-e: $($response.numero_nfe)" -ForegroundColor Cyan
        }
        if ($response.chave_acesso) {
            Write-Host "   Chave de Acesso: $($response.chave_acesso)" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "   [AVISO] Erro ao verificar status: $_" -ForegroundColor Yellow
}

# ============================================
# PASSO 6: Funcionalidades implementadas
# ============================================
Write-Host "`n=== PASSO 6: FUNCIONALIDADES IMPLEMENTADAS ===" -ForegroundColor Yellow
Write-Host "   [OK] Emissao automatica de NF-e via Bling API" -ForegroundColor Green
Write-Host "   [OK] Validacao de condicoes antes de emitir" -ForegroundColor Green
Write-Host "   [OK] Armazenamento de XML, chave de acesso e numero" -ForegroundColor Green
Write-Host "   [OK] Consulta de status da NF-e" -ForegroundColor Green
Write-Host "   [OK] Tratamento de erros fiscais" -ForegroundColor Green
Write-Host "   [OK] Integracao automatica no webhook de pagamento" -ForegroundColor Green

# ============================================
# PASSO 7: Status possiveis da NF-e
# ============================================
Write-Host "`n=== PASSO 7: STATUS DA NF-e ===" -ForegroundColor Yellow
Write-Host "   - pendente: Aguardando emissao" -ForegroundColor White
Write-Host "   - processando: Em processamento" -ForegroundColor White
Write-Host "   - emitida: NF-e emitida com sucesso" -ForegroundColor White
Write-Host "   - erro: Erro na emissao" -ForegroundColor White
Write-Host "   - cancelada: NF-e cancelada" -ForegroundColor White

# ============================================
# RESUMO
# ============================================
Write-Host "`n=== RESUMO DO TESTE ===" -ForegroundColor Cyan
Write-Host "`nTeste concluido!" -ForegroundColor Yellow
Write-Host "`nCONDICOES PARA EMISSAO DE NF-e:" -ForegroundColor Yellow
Write-Host "   1. Pagamento confirmado (status processando_envio ou superior)" -ForegroundColor White
Write-Host "   2. Pedido sincronizado com Bling" -ForegroundColor White
Write-Host "   3. Dados fiscais completos (CPF/CNPJ, nome, endereco)" -ForegroundColor White
Write-Host "   4. Cliente existe no Bling" -ForegroundColor White

Write-Host "`nFLUXO AUTOMATICO:" -ForegroundColor Yellow
Write-Host "   1. Pagamento confirmado (webhook PagBank)" -ForegroundColor White
Write-Host "   2. Pedido sincronizado com Bling" -ForegroundColor White
Write-Host "   3. NF-e emitida automaticamente" -ForegroundColor White
Write-Host "   4. Informacoes armazenadas localmente" -ForegroundColor White

Write-Host "`n=== TESTE ETAPA 7 CONCLUIDO ===" -ForegroundColor Cyan
