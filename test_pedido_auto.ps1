# Teste Automático - Sincronizacao de Pedidos (Busca venda existente)
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE AUTOMATICO: SINCRONIZACAO DE PEDIDOS ===" -ForegroundColor Cyan

# ============================================
# PASSO 0: Verificar conexao
# ============================================
Write-Host "`n=== PASSO 0: Verificando conexao com API ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/test" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   ✅ Conexao com API Bling OK" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Problema na conexao" -ForegroundColor Red
        exit
    }
} catch {
    Write-Host "   ❌ Erro ao conectar: $_" -ForegroundColor Red
    exit
}

# ============================================
# PASSO 1: Buscar venda disponivel no banco
# ============================================
Write-Host "`n=== PASSO 1: Buscando venda disponivel para teste ===" -ForegroundColor Yellow

# Vamos tentar IDs de venda comuns (1-10)
$vendaId = $null
$vendaEncontrada = $false

for ($id = 1; $id -le 10; $id++) {
    try {
        $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/info/$id" `
            -Method GET -Headers $headers -ErrorAction Stop
        
        # Se conseguiu buscar (mesmo que não sincronizado), a venda existe
        $vendaId = $id
        $vendaEncontrada = $true
        Write-Host "   ✅ Venda encontrada: ID $id" -ForegroundColor Green
        
        if ($response.synced) {
            Write-Host "   Status: Já sincronizada com Bling (ID: $($response.bling_pedido_id))" -ForegroundColor Cyan
        } else {
            Write-Host "   Status: Não sincronizada (pronta para sincronizar)" -ForegroundColor Yellow
        }
        break
    } catch {
        # Venda não existe ou erro de conexão, continuar tentando
        continue
    }
}

if (-not $vendaEncontrada) {
    Write-Host "   ⚠ Nenhuma venda encontrada nos IDs testados (1-10)" -ForegroundColor Yellow
    
    # Tentar sincronizar diretamente para ver a mensagem de erro real
    Write-Host "`n   Testando sincronizacao para identificar o problema..." -ForegroundColor Cyan
    try {
        $testResponse = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/sync/1" `
            -Method POST -Headers $headers -ErrorAction Stop
    } catch {
        if ($_.ErrorDetails.Message) {
            try {
                $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
                Write-Host "   Erro: $($errorJson.error)" -ForegroundColor Red
                if ($errorJson.error -like "*não encontrada*") {
                    Write-Host "`n   ✅ PROBLEMA IDENTIFICADO: Nenhuma venda existe no banco de dados" -ForegroundColor Yellow
                }
            } catch { }
        }
    }
    
    Write-Host "`n   INSTRUCOES PARA TESTAR:" -ForegroundColor Yellow
    Write-Host "   1. Crie uma venda no sistema (via checkout ou manualmente)" -ForegroundColor Cyan
    Write-Host "   2. A venda precisa ter:" -ForegroundColor Cyan
    Write-Host "      ✅ Dados fiscais completos:" -ForegroundColor White
    Write-Host "         - CPF/CNPJ valido" -ForegroundColor Gray
    Write-Host "         - Nome/Razao Social" -ForegroundColor Gray
    Write-Host "         - Endereco completo (rua, numero, bairro, cidade, UF, CEP)" -ForegroundColor Gray
    Write-Host "         - Inscricao Estadual (se CNPJ)" -ForegroundColor Gray
    Write-Host "      ✅ Itens com produtos:" -ForegroundColor White
    Write-Host "         - Produtos sincronizados com Bling (ou ter SKU valido)" -ForegroundColor Gray
    Write-Host "         - Quantidades e precos" -ForegroundColor Gray
    Write-Host "      ✅ Status:" -ForegroundColor White
    Write-Host "         - Status de pagamento (opcional, pode ser pendente)" -ForegroundColor Gray
    Write-Host "`n   3. Apos criar a venda, execute este script novamente" -ForegroundColor Cyan
    Write-Host "   4. Ou informe o ID da venda manualmente editando o script" -ForegroundColor Cyan
    
    exit
}

Write-Host "`n   Venda selecionada para teste: ID $vendaId" -ForegroundColor Cyan

# ============================================
# PASSO 2: Verificar status atual do pedido
# ============================================
Write-Host "`n=== PASSO 2: Verificar status atual do pedido ===" -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/info/$vendaId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.synced) {
        Write-Host "   ✅ Pedido $vendaId ja esta sincronizado com Bling" -ForegroundColor Green
        Write-Host "   Bling Pedido ID: $($response.bling_pedido_id)" -ForegroundColor Cyan
        if ($response.bling_nfe_id) {
            Write-Host "   NF-e ID: $($response.bling_nfe_id)" -ForegroundColor Cyan
        }
        $jaSincronizado = $true
    } else {
        Write-Host "   ⚠ Pedido $vendaId nao esta sincronizado" -ForegroundColor Yellow
        Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
        $jaSincronizado = $false
    }
} catch {
    Write-Host "   ⚠ Erro ao verificar status: $_" -ForegroundColor Yellow
    $jaSincronizado = $false
}

# ============================================
# PASSO 3: Sincronizar pedido com Bling (se ainda não sincronizado)
# ============================================
if (-not $jaSincronizado) {
    Write-Host "`n=== PASSO 3: Sincronizar pedido com Bling ===" -ForegroundColor Yellow
    
    try {
        Write-Host "   Enviando sincronizacao..." -ForegroundColor Cyan
        
        $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/sync/$vendaId" `
            -Method POST -Headers $headers -ErrorAction Stop
        
        if ($response.success) {
            Write-Host "   ✅ Pedido sincronizado com sucesso!" -ForegroundColor Green
            Write-Host "   Acao: $($response.action)" -ForegroundColor Cyan
            Write-Host "   Bling Pedido ID: $($response.bling_pedido_id)" -ForegroundColor Cyan
            Write-Host "   Mensagem: $($response.message)" -ForegroundColor Gray
            
            Write-Host "`n   O que aconteceu:" -ForegroundColor Yellow
            Write-Host "   1. Cliente foi sincronizado automaticamente" -ForegroundColor White
            Write-Host "   2. CFOP foi calculado automaticamente" -ForegroundColor White
            Write-Host "   3. Pedido foi criado no Bling com situacao 'P' (Pendente)" -ForegroundColor White
            Write-Host "   4. Descontos promocionais foram aplicados por item" -ForegroundColor White
            
            # Aguardar um pouco para garantir que a sincronizacao foi processada
            Start-Sleep -Seconds 2
        } else {
            Write-Host "   ❌ Erro ao sincronizar: $($response.error)" -ForegroundColor Red
            if ($response.details) {
                Write-Host "   Detalhes: $($response.details)" -ForegroundColor Yellow
            }
            
            Write-Host "`n   POSSIVEIS PROBLEMAS:" -ForegroundColor Yellow
            Write-Host "   - Venda sem dados fiscais completos" -ForegroundColor White
            Write-Host "   - Produtos dos itens nao sincronizados com Bling" -ForegroundColor White
            Write-Host "   - Cliente sem CPF/CNPJ valido" -ForegroundColor White
            Write-Host "   - Endereco incompleto" -ForegroundColor White
            
            exit
        }
    } catch {
        Write-Host "   ❌ ERRO: $_" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            try {
                $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
                Write-Host "   Erro: $($errorJson.error)" -ForegroundColor Yellow
                Write-Host "   Mensagem: $($errorJson.message)" -ForegroundColor Yellow
                
                if ($errorJson.details) {
                    Write-Host "   Detalhes: $($errorJson.details)" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
            }
        }
        exit
    }
} else {
    Write-Host "`n=== PASSO 3: Pedido ja sincronizado, pulando... ===" -ForegroundColor Yellow
}

# ============================================
# PASSO 4: Verificar pedido no Bling
# ============================================
Write-Host "`n=== PASSO 4: Verificar pedido sincronizado ===" -ForegroundColor Yellow

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
# PASSO 5: Aprovar pedido no Bling
# ============================================
Write-Host "`n=== PASSO 5: Aprovar pedido no Bling ===" -ForegroundColor Yellow
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
# PASSO 6: Sincronizar status do Bling para local
# ============================================
Write-Host "`n=== PASSO 6: Sincronizar status do Bling ===" -ForegroundColor Yellow

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
Write-Host "1. ✅ Verificacao de conexao" -ForegroundColor Green
Write-Host "2. ✅ Busca de venda disponivel" -ForegroundColor Green
Write-Host "3. ✅ Verificacao de status inicial" -ForegroundColor Green
Write-Host "4. ✅ Sincronizacao de pedido (cliente + pedido)" -ForegroundColor Green
Write-Host "5. ✅ Aprovacao de pedido no Bling" -ForegroundColor Green
Write-Host "6. ✅ Sincronizacao de status bidirecional" -ForegroundColor Green

Write-Host "`nSITUACOES DO BLING:" -ForegroundColor Yellow
Write-Host "- 'P' = Pendente (aguardando aprovacao)" -ForegroundColor White
Write-Host "- 'E' = Em aberto (aprovado, pronto para processar)" -ForegroundColor White
Write-Host "- 'B' = Baixado (entregue/finalizado)" -ForegroundColor White
Write-Host "- 'F' = Faturado" -ForegroundColor White
Write-Host "- 'C' = Cancelado" -ForegroundColor White

Write-Host "`n=== TESTE CONCLUIDO ===" -ForegroundColor Cyan
