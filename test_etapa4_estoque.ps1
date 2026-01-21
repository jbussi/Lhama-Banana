# Teste ETAPA 4 - Sincronizacao de Estoque
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE ETAPA 4: SINCRONIZACAO DE ESTOQUE ===" -ForegroundColor Cyan

# Usar produto ID 6 (que ja esta sincronizado)
$produtoId = 6

Write-Host "`nProduto de teste: ID $produtoId" -ForegroundColor Cyan
Write-Host "(Este produto ja esta sincronizado com Bling)" -ForegroundColor Yellow

# ============================================
# TESTE 1: Sincronizar estoque DO BLING para LOCAL
# ============================================
Write-Host "`n1. TESTE: Sincronizar estoque DO BLING para LOCAL..." -ForegroundColor Yellow
try {
    $body = @{
        produto_id = $produtoId
    } | ConvertTo-Json
    
    $start = Get-Date
    $result = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/estoque/sync-from-bling" `
        -Method POST -Headers $headers `
        -Body $body -ContentType "application/json" -ErrorAction Stop
    $elapsed = ((Get-Date) - $start).TotalSeconds
    
    if ($result.success) {
        Write-Host "   OK! Estoque sincronizado do Bling para local" -ForegroundColor Green
        Write-Host "   Total processado: $($result.total)" -ForegroundColor Cyan
        Write-Host "   Sucesso: $($result.success_count)" -ForegroundColor Cyan
        Write-Host "   Erros: $($result.errors)" -ForegroundColor Cyan
        Write-Host "   Tempo: $([math]::Round($elapsed, 2)) segundos" -ForegroundColor Cyan
        
        if ($result.results -and $result.results.Count -gt 0) {
            Write-Host "   Resultados:" -ForegroundColor Cyan
            foreach ($r in $result.results) {
                if ($r.success) {
                    Write-Host "     Produto $($r.produto_id): Estoque atualizado para $($r.estoque_novo)" -ForegroundColor Green
                } else {
                    Write-Host "     Produto $($r.produto_id): ERRO - $($r.error)" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "   ERRO ao sincronizar estoque" -ForegroundColor Red
        Write-Host "   Erro: $($result.error)" -ForegroundColor Red
    }
} catch {
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

# ============================================
# TESTE 2: Sincronizar estoque DO LOCAL para BLING
# ============================================
Write-Host "`n2. TESTE: Sincronizar estoque DO LOCAL para BLING..." -ForegroundColor Yellow
try {
    $body = @{
        produto_id = $produtoId
    } | ConvertTo-Json
    
    $start = Get-Date
    $result = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/estoque/sync-to-bling" `
        -Method POST -Headers $headers `
        -Body $body -ContentType "application/json" -ErrorAction Stop
    $elapsed = ((Get-Date) - $start).TotalSeconds
    
    if ($result.success) {
        Write-Host "   OK! Estoque sincronizado do local para Bling" -ForegroundColor Green
        Write-Host "   Total processado: $($result.total)" -ForegroundColor Cyan
        Write-Host "   Sucesso: $($result.success_count)" -ForegroundColor Cyan
        Write-Host "   Erros: $($result.errors)" -ForegroundColor Cyan
        Write-Host "   Tempo: $([math]::Round($elapsed, 2)) segundos" -ForegroundColor Cyan
        
        if ($result.results -and $result.results.Count -gt 0) {
            Write-Host "   Resultados:" -ForegroundColor Cyan
            foreach ($r in $result.results) {
                if ($r.success) {
                    Write-Host "     Produto $($r.produto_id): Estoque atualizado para $($r.estoque_novo)" -ForegroundColor Green
                } else {
                    Write-Host "     Produto $($r.produto_id): ERRO - $($r.error)" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "   ERRO ao sincronizar estoque" -ForegroundColor Red
        Write-Host "   Erro: $($result.error)" -ForegroundColor Red
    }
} catch {
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

# ============================================
# TESTE 3: Sincronizacao bidirecional (produto especifico)
# ============================================
Write-Host "`n3. TESTE: Sincronizacao bidirecional (produto especifico)..." -ForegroundColor Yellow
try {
    $start = Get-Date
    $result = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/estoque/sync/$produtoId" `
        -Method POST -Headers $headers -ErrorAction Stop
    $elapsed = ((Get-Date) - $start).TotalSeconds
    
    if ($result.success) {
        Write-Host "   OK! Estoque sincronizado bidirecionalmente" -ForegroundColor Green
        Write-Host "   Estoque local: $($result.estoque_local)" -ForegroundColor Cyan
        Write-Host "   Estoque Bling: $($result.estoque_bling)" -ForegroundColor Cyan
        Write-Host "   Tempo: $([math]::Round($elapsed, 2)) segundos" -ForegroundColor Cyan
    } else {
        Write-Host "   ERRO ao sincronizar" -ForegroundColor Red
        Write-Host "   Erro: $($result.error)" -ForegroundColor Red
    }
} catch {
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

# ============================================
# TESTE 4: Verificar consistencia de estoque
# ============================================
Write-Host "`n4. TESTE: Verificar consistencia de estoque..." -ForegroundColor Yellow
try {
    $body = @{
        produto_id = $produtoId
    } | ConvertTo-Json
    
    $start = Get-Date
    $result = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/estoque/consistency" `
        -Method POST -Headers $headers `
        -Body $body -ContentType "application/json" -ErrorAction Stop
    $elapsed = ((Get-Date) - $start).TotalSeconds
    
    if ($result.success) {
        Write-Host "   OK! Consistencia verificada" -ForegroundColor Green
        Write-Host "   Total verificado: $($result.total)" -ForegroundColor Cyan
        Write-Host "   Consistente: $($result.consistent)" -ForegroundColor Cyan
        Write-Host "   Inconsistente: $($result.inconsistent)" -ForegroundColor Cyan
        Write-Host "   Corrigidos: $($result.corrigidos)" -ForegroundColor Cyan
        Write-Host "   Tempo: $([math]::Round($elapsed, 2)) segundos" -ForegroundColor Cyan
        
        if ($result.differences -and $result.differences.Count -gt 0) {
            Write-Host "   Diferencas encontradas:" -ForegroundColor Yellow
            foreach ($diff in $result.differences) {
                Write-Host "     Produto $($diff.produto_id): Local=$($diff.estoque_local), Bling=$($diff.estoque_bling)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "   ERRO ao verificar consistencia" -ForegroundColor Red
        Write-Host "   Erro: $($result.error)" -ForegroundColor Red
    }
} catch {
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

Write-Host "`n=== TESTE ETAPA 4 CONCLUIDO ===" -ForegroundColor Cyan
Write-Host "`nPROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Verifique o estoque no painel do Bling" -ForegroundColor Cyan
Write-Host "2. Compare estoque local vs Bling" -ForegroundColor Cyan
Write-Host "3. Teste fluxo completo: criar pedido -> verificar estoque" -ForegroundColor Cyan
Write-Host "4. Teste cancelamento: cancelar pedido -> verificar reversao de estoque" -ForegroundColor Cyan


