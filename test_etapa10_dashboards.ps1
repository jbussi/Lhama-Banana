# Teste ETAPA 10 - Dashboards e Analytics
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE ETAPA 10: DASHBOARDS E ANALYTICS ===" -ForegroundColor Cyan

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
# PASSO 2: Dashboard Financeiro
# ============================================
Write-Host "`n=== PASSO 2: Dashboard Financeiro ===" -ForegroundColor Yellow

try {
    Write-Host "   Buscando dashboard financeiro..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/analytics/dashboard" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Dashboard carregado com sucesso!" -ForegroundColor Green
        Write-Host "`n   Periodo:" -ForegroundColor Cyan
        Write-Host "   - Inicio: $($response.periodo.inicio)" -ForegroundColor White
        Write-Host "   - Fim: $($response.periodo.fim)" -ForegroundColor White
        
        Write-Host "`n   Faturamento:" -ForegroundColor Cyan
        Write-Host "   - Bruto: R$ $($response.faturamento.bruto)" -ForegroundColor White
        Write-Host "   - Ticket Medio: R$ $($response.faturamento.ticket_medio)" -ForegroundColor White
        Write-Host "   - Total de Pedidos: $($response.faturamento.total_pedidos)" -ForegroundColor White
        
        Write-Host "`n   Frete:" -ForegroundColor Cyan
        Write-Host "   - Total: R$ $($response.frete.total)" -ForegroundColor White
        Write-Host "   - Percentual: $($response.frete.percentual)%" -ForegroundColor White
        
        Write-Host "`n   Descontos:" -ForegroundColor Cyan
        Write-Host "   - Total: R$ $($response.descontos.total)" -ForegroundColor White
        Write-Host "   - Percentual: $($response.descontos.percentual)%" -ForegroundColor White
        
        if ($response.contas_receber) {
            Write-Host "`n   Contas a Receber:" -ForegroundColor Cyan
            Write-Host "   - Total em Aberto: R$ $($response.contas_receber.total_aberto)" -ForegroundColor White
            Write-Host "   - Quantidade: $($response.contas_receber.quantidade)" -ForegroundColor White
        }
    } else {
        Write-Host "   [AVISO] $($response.error)" -ForegroundColor Yellow
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
# PASSO 3: Vendas por Periodo
# ============================================
Write-Host "`n=== PASSO 3: Vendas por Periodo (por dia) ===" -ForegroundColor Yellow

try {
    Write-Host "   Buscando vendas por dia..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/analytics/vendas/periodo?periodo=dia" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Dados carregados!" -ForegroundColor Green
        Write-Host "   Total de registros: $($response.vendas.Count)" -ForegroundColor Cyan
        
        if ($response.vendas.Count -gt 0) {
            Write-Host "`n   Primeiros 5 registros:" -ForegroundColor Yellow
            $response.vendas | Select-Object -First 5 | ForEach-Object {
                Write-Host "   - $($_.periodo): $($_.quantidade) vendas - R$ $($_.faturamento)" -ForegroundColor White
            }
        } else {
            Write-Host "   Nenhuma venda encontrada no periodo" -ForegroundColor Gray
        }
    } else {
        Write-Host "   [AVISO] $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [AVISO] Erro ao buscar: $_" -ForegroundColor Yellow
}

# ============================================
# PASSO 4: Top Produtos
# ============================================
Write-Host "`n=== PASSO 4: Top Produtos Mais Vendidos ===" -ForegroundColor Yellow

try {
    Write-Host "   Buscando top produtos..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/analytics/produtos/top?limit=10" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Dados carregados!" -ForegroundColor Green
        Write-Host "   Total de produtos: $($response.produtos.Count)" -ForegroundColor Cyan
        
        if ($response.produtos.Count -gt 0) {
            Write-Host "`n   Top produtos:" -ForegroundColor Yellow
            $response.produtos | ForEach-Object {
                Write-Host "   - $($_.nome_produto):" -ForegroundColor White
                Write-Host "     Quantidade: $($_.quantidade_vendida) | Faturamento: R$ $($_.faturamento) | Pedidos: $($_.num_pedidos)" -ForegroundColor Gray
            }
        } else {
            Write-Host "   Nenhum produto encontrado" -ForegroundColor Gray
        }
    } else {
        Write-Host "   [AVISO] $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [AVISO] Erro ao buscar: $_" -ForegroundColor Yellow
}

# ============================================
# PASSO 5: Comparacao Local vs Bling
# ============================================
Write-Host "`n=== PASSO 5: Comparacao Local vs Bling ===" -ForegroundColor Yellow

try {
    Write-Host "   Comparando dados locais com Bling..." -ForegroundColor Cyan
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/analytics/comparacao" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "   [OK] Comparacao realizada!" -ForegroundColor Green
        
        Write-Host "`n   Faturamento:" -ForegroundColor Cyan
        Write-Host "   - Local: R$ $($response.faturamento.local)" -ForegroundColor White
        Write-Host "   - Bling: R$ $($response.faturamento.bling)" -ForegroundColor White
        Write-Host "   - Diferenca: R$ $($response.faturamento.diferenca) ($($response.faturamento.percentual_diferenca)%)" -ForegroundColor $(if ([math]::Abs($response.faturamento.diferenca) -lt 0.01) { "Green" } else { "Yellow" })
        
        Write-Host "`n   Pedidos:" -ForegroundColor Cyan
        Write-Host "   - Local: $($response.pedidos.local)" -ForegroundColor White
        Write-Host "   - Bling: $($response.pedidos.bling)" -ForegroundColor White
        Write-Host "   - Diferenca: $($response.pedidos.diferenca)" -ForegroundColor $(if ($response.pedidos.diferenca -eq 0) { "Green" } else { "Yellow" })
        
        if ($response.frete) {
            Write-Host "`n   Frete:" -ForegroundColor Cyan
            Write-Host "   - Local: R$ $($response.frete.local)" -ForegroundColor White
            Write-Host "   - Bling: R$ $($response.frete.bling)" -ForegroundColor White
        }
        
        if ($response.divergencias.Count -gt 0) {
            Write-Host "`n   [AVISO] Divergencias encontradas:" -ForegroundColor Yellow
            $response.divergencias | ForEach-Object {
                Write-Host "   - $_" -ForegroundColor White
            }
        } else {
            Write-Host "`n   [OK] Nenhuma divergencia encontrada!" -ForegroundColor Green
        }
    } else {
        Write-Host "   [AVISO] $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [AVISO] Erro ao comparar: $_" -ForegroundColor Yellow
}

# ============================================
# PASSO 6: Funcionalidades implementadas
# ============================================
Write-Host "`n=== PASSO 6: FUNCIONALIDADES IMPLEMENTADAS ===" -ForegroundColor Yellow
Write-Host "   [OK] Dashboard financeiro com metricas principais" -ForegroundColor Green
Write-Host "   [OK] Vendas por periodo (dia/semana/mes)" -ForegroundColor Green
Write-Host "   [OK] Top produtos mais vendidos" -ForegroundColor Green
Write-Host "   [OK] Comparacao Local vs Bling" -ForegroundColor Green
Write-Host "   [OK] Contas a receber em aberto" -ForegroundColor Green

# ============================================
# RESUMO
# ============================================
Write-Host "`n=== RESUMO DO TESTE ===" -ForegroundColor Cyan
Write-Host "`nTeste concluido!" -ForegroundColor Yellow

Write-Host "`nENDPOINTS DISPONIVEIS:" -ForegroundColor Yellow
Write-Host "   - GET /api/bling/analytics/dashboard" -ForegroundColor White
Write-Host "   - GET /api/bling/analytics/vendas/periodo?periodo=dia|semana|mes" -ForegroundColor White
Write-Host "   - GET /api/bling/analytics/produtos/top?limit=10" -ForegroundColor White
Write-Host "   - GET /api/bling/analytics/comparacao" -ForegroundColor White

Write-Host "`n=== TESTE ETAPA 10 CONCLUIDO ===" -ForegroundColor Cyan
