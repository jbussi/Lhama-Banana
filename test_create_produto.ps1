# Teste CREATE de Produto no Bling
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE CREATE: CRIACAO DE PRODUTO NO BLING ===" -ForegroundColor Cyan

# 1. Buscar produtos nao sincronizados (sem referencia no Bling)
Write-Host "`n1. Buscando produtos nao sincronizados..." -ForegroundColor Yellow

# Tentar IDs recentes primeiro (produtos mais recentes geralmente tem IDs maiores)
$produtoId = $null
$idsParaTestar = @(7..50) + @(51..100)

foreach ($id in $idsParaTestar) {
    try {
        # Verificar se produto existe e esta sincronizado
        $status = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$id" `
            -Method GET -Headers $headers -ErrorAction Stop
        
        # Se nao esta sincronizado, e o produto existe (nao deu erro 404)
        if (-not $status.synced) {
            Write-Host "   Produto ID $id encontrado e NAO sincronizado" -ForegroundColor Cyan
            $produtoId = $id
            break
        }
    } catch {
        # Se erro 404, produto nao existe, continuar
        continue
    }
}

if (-not $produtoId) {
    Write-Host "   Nenhum produto nao sincronizado encontrado nos IDs testados" -ForegroundColor Yellow
    Write-Host "   Tentando produto ID 21 (assumindo que e novo)..." -ForegroundColor Yellow
    $produtoId = 21
}

Write-Host "`n   Produto selecionado para teste: ID $produtoId" -ForegroundColor Green

# 2. Verificar status antes da sincronizacao
Write-Host "`n2. Verificando status ANTES da sincronizacao..." -ForegroundColor Yellow
try {
    $statusAntes = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$produtoId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($statusAntes.synced) {
        Write-Host "   AVISO: Produto ja esta sincronizado!" -ForegroundColor Yellow
        Write-Host "   Bling ID: $($statusAntes.bling_id)" -ForegroundColor Cyan
        Write-Host "   Para testar CREATE, use um produto novo sem NCM ainda sincronizado" -ForegroundColor Yellow
    } else {
        Write-Host "   OK! Produto nao esta sincronizado (ideal para testar CREATE)" -ForegroundColor Green
    }
} catch {
    Write-Host "   Produto nao encontrado ou erro ao verificar: $_" -ForegroundColor Red
}

# 3. Sincronizar produto (deve criar no Bling)
Write-Host "`n3. Sincronizando produto ID $produtoId (CREATE)..." -ForegroundColor Yellow
try {
    $start = Get-Date
    $result = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/sync/$produtoId" `
        -Method POST -Headers $headers -ErrorAction Stop
    $elapsed = ((Get-Date) - $start).TotalSeconds
    
    if ($result.success) {
        if ($result.action -eq 'created') {
            Write-Host "   SUCESSO! Produto CRIADO no Bling!" -ForegroundColor Green
            Write-Host "   Acao: $($result.action) ✅" -ForegroundColor Green
            Write-Host "   Bling ID: $($result.bling_product_id)" -ForegroundColor Cyan
            Write-Host "   Bling Codigo: $($result.bling_codigo)" -ForegroundColor Cyan
            Write-Host "   Tempo: $([math]::Round($elapsed, 2)) segundos" -ForegroundColor Cyan
        } elseif ($result.action -eq 'updated') {
            Write-Host "   AVISO: Produto foi ATUALIZADO (ja existia no Bling)" -ForegroundColor Yellow
            Write-Host "   Acao: $($result.action)" -ForegroundColor Yellow
            Write-Host "   Bling ID: $($result.bling_product_id)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   ERRO ao sincronizar" -ForegroundColor Red
        Write-Host "   Erro: $($result.error)" -ForegroundColor Red
        if ($result.details) {
            Write-Host "   Detalhes:" -ForegroundColor Yellow
            $result.details | ForEach-Object {
                Write-Host "     - $_" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "   ERRO: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Tipo: $($errorJson.error)" -ForegroundColor Yellow
            Write-Host "   Mensagem: $($errorJson.message)" -ForegroundColor Yellow
            if ($errorJson.details) {
                $errorJson.details | ForEach-Object {
                    Write-Host "     - $_" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
}

# 4. Verificar status DEPOIS da sincronizacao
Write-Host "`n4. Verificando status DEPOIS da sincronizacao..." -ForegroundColor Yellow
try {
    $statusDepois = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$produtoId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($statusDepois.synced) {
        Write-Host "   OK! Produto agora esta sincronizado" -ForegroundColor Green
        Write-Host "   Bling ID: $($statusDepois.bling_id)" -ForegroundColor Cyan
        Write-Host "   Bling Codigo: $($statusDepois.bling_codigo)" -ForegroundColor Cyan
        Write-Host "   Status: $($statusDepois.status)" -ForegroundColor Cyan
        Write-Host "   Ultima sincronizacao: $($statusDepois.ultima_sincronizacao)" -ForegroundColor Cyan
    } else {
        Write-Host "   ERRO: Produto ainda nao esta sincronizado" -ForegroundColor Red
    }
} catch {
    Write-Host "   ERRO ao verificar status: $_" -ForegroundColor Red
}

Write-Host "`n=== TESTE CREATE CONCLUIDO ===" -ForegroundColor Cyan
Write-Host "`nPROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Verifique o produto no painel do Bling" -ForegroundColor Cyan
Write-Host "2. Confirme que o produto foi CRIADO (nao atualizado)" -ForegroundColor Cyan
Write-Host "3. Verifique NCM, preco, estoque e outros campos" -ForegroundColor Cyan
Write-Host "4. Verifique logs: SELECT * FROM bling_sync_logs WHERE entity_type = 'produto' AND action = 'create'" -ForegroundColor Cyan

