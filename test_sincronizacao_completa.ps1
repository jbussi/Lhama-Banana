# Script de teste completo da sincronizacao Bling
# ================================================

# Tentar obter URL do ngrok
$ngrokUrl = $env:NGROK_URL
if (-not $ngrokUrl) {
    # Tentar ler do .env
    $envFile = Join-Path $PSScriptRoot ".env"
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile
        foreach ($line in $envContent) {
            if ($line -match "^NGROK_URL=(.+)$") {
                $ngrokUrl = $matches[1].Trim()
                break
            }
        }
    }
}

if (-not $ngrokUrl) {
    # Valor padrao para desenvolvimento
    $ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
    Write-Host "Usando URL padrao do ngrok: $ngrokUrl" -ForegroundColor Yellow
    Write-Host "(Para usar outra URL, defina a variavel de ambiente NGROK_URL)" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TESTE COMPLETO DE SINCRONIZACAO BLING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# IDs dos produtos criados
$produtosIds = @(10, 11, 12, 13, 14, 15)

Write-Host "1. VERIFICANDO STATUS INICIAL DOS PRODUTOS..." -ForegroundColor Yellow
Write-Host ""

$headers = @{
    "ngrok-skip-browser-warning" = "true"
    "Content-Type" = "application/json"
}

foreach ($produtoId in $produtosIds) {
    try {
        $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$produtoId" -Method GET -Headers $headers -ErrorAction Stop
        if ($response.synced) {
            Write-Host "  [OK] Produto ${produtoId}: Sincronizado (Bling ID: $($response.bling_id), Status: $($response.status))" -ForegroundColor Green
        } else {
            Write-Host "  [PENDENTE] Produto ${produtoId}: Nao sincronizado ainda" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERRO] Produto ${produtoId}: Nao foi possivel verificar status" -ForegroundColor Red
        Write-Host "         Erro: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "2. SINCRONIZANDO PRODUTOS COM BLING..." -ForegroundColor Yellow
Write-Host ""

$resultadosSincronizacao = @()

foreach ($produtoId in $produtosIds) {
    Write-Host "  Sincronizando produto $produtoId..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/sync/$produtoId" -Method POST -Headers $headers -ErrorAction Stop
        
        if ($response.success) {
            Write-Host "    [OK] Sincronizado com sucesso!" -ForegroundColor Green
            Write-Host "         Acao: $($response.action), Bling ID: $($response.bling_id)" -ForegroundColor Gray
            $resultadosSincronizacao += @{
                produto_id = $produtoId
                success = $true
                bling_id = $response.bling_id
                action = $response.action
            }
        } else {
            Write-Host "    [FALHOU] Erro: $($response.error)" -ForegroundColor Red
            $resultadosSincronizacao += @{
                produto_id = $produtoId
                success = $false
                error = $response.error
            }
        }
    } catch {
        Write-Host "    [ERRO] Falha na requisicao: $($_.Exception.Message)" -ForegroundColor Red
        $resultadosSincronizacao += @{
            produto_id = $produtoId
            success = $false
            error = $_.Exception.Message
        }
    }
    
    # Pequeno delay entre requisicoes
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "3. VERIFICANDO STATUS APOS SINCRONIZACAO..." -ForegroundColor Yellow
Write-Host ""

foreach ($produtoId in $produtosIds) {
    try {
        $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$produtoId" -Method GET -Headers $headers -ErrorAction Stop
        if ($response.synced) {
            Write-Host "  [OK] Produto ${produtoId}: Sincronizado" -ForegroundColor Green
            Write-Host "       Bling ID: $($response.bling_id)" -ForegroundColor Gray
            Write-Host "       Status: $($response.status)" -ForegroundColor Gray
            if ($response.ultima_sincronizacao) {
                Write-Host "       Ultima sincronizacao: $($response.ultima_sincronizacao)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  [PENDENTE] Produto ${produtoId}: Ainda nao sincronizado" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERRO] Produto ${produtoId}: Erro ao verificar status" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "4. TESTANDO SINCRONIZACAO DE ESTOQUE..." -ForegroundColor Yellow
Write-Host ""

# Testar sincronizacao de estoque para um produto especifico
$produtoTeste = $produtosIds[0]
Write-Host "  Testando sincronizacao de estoque do produto $produtoTeste..." -ForegroundColor Cyan

try {
    $body = @{
        direction = "both"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/estoque/sync/$produtoTeste" -Method POST -Headers $headers -Body $body -ErrorAction Stop
    
    if ($response.success) {
        Write-Host "    [OK] Estoque sincronizado com sucesso!" -ForegroundColor Green
        if ($response.estoque_local) {
            Write-Host "         Estoque Local: $($response.estoque_local)" -ForegroundColor Gray
        }
        if ($response.estoque_bling) {
            Write-Host "         Estoque Bling: $($response.estoque_bling)" -ForegroundColor Gray
        }
    } else {
        Write-Host "    [FALHOU] Erro: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "    [ERRO] Falha na sincronizacao de estoque: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "5. TESTANDO SINCRONIZACAO DE TODOS OS PRODUTOS..." -ForegroundColor Yellow
Write-Host ""

try {
    $body = @{
        limit = 10
        only_active = $true
    } | ConvertTo-Json
    
    Write-Host "  Enviando requisicao para sincronizar todos os produtos..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/sync-all" -Method POST -Headers $headers -Body $body -ErrorAction Stop
    
    Write-Host "    [OK] Sincronizacao em lote concluida!" -ForegroundColor Green
    Write-Host "         Total processado: $($response.total)" -ForegroundColor Gray
    Write-Host "         Sucessos: $($response.success_count)" -ForegroundColor Gray
    Write-Host "         Erros: $($response.error_count)" -ForegroundColor Gray
} catch {
    Write-Host "    [ERRO] Falha na sincronizacao em lote: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RESUMO DOS RESULTADOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$sucessos = ($resultadosSincronizacao | Where-Object { $_.success }).Count
$falhas = ($resultadosSincronizacao | Where-Object { -not $_.success }).Count

Write-Host "Produtos sincronizados com sucesso: $sucessos" -ForegroundColor Green
Write-Host "Produtos com falha: $falhas" -ForegroundColor $(if ($falhas -gt 0) { "Red" } else { "Gray" })

Write-Host ""
Write-Host "Detalhes:" -ForegroundColor Yellow

foreach ($resultado in $resultadosSincronizacao) {
    if ($resultado.success) {
        Write-Host "  [OK] Produto $($resultado.produto_id): $($resultado.action) -> Bling ID: $($resultado.bling_id)" -ForegroundColor Green
    } else {
        Write-Host "  [FALHOU] Produto $($resultado.produto_id): $($resultado.error)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Teste concluido!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
