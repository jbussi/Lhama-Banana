# Teste ETAPA 3 - Sincronizacao de Produtos
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE ETAPA 3: SINCRONIZACAO DE PRODUTOS ===" -ForegroundColor Cyan

# Tentar encontrar um produto valido testando varios IDs
Write-Host "`n0. Buscando produto valido (com NCM)..." -ForegroundColor Yellow
$produtoId = $null
$idsParaTestar = @(1..20)

foreach ($id in $idsParaTestar) {
    try {
        $result = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/sync/$id" `
            -Method POST -Headers $headers -ErrorAction Stop -TimeoutSec 5
        
        # Se nao retornou erro de validacao, encontramos um produto valido
        if ($result.success -or ($result.error -and $result.error -notlike "*NCM*")) {
            $produtoId = $id
            Write-Host "   Produto valido encontrado: ID $id" -ForegroundColor Green
            break
        }
    } catch {
        $errorMsg = $_.ErrorDetails.Message
        if ($errorMsg -and $errorMsg -notlike "*NCM*") {
            # Erro diferente de NCM, pode ser que o produto nao exista
            continue
        }
    }
}

if (-not $produtoId) {
    Write-Host "   Nenhum produto valido encontrado nos primeiros 20 IDs" -ForegroundColor Yellow
    Write-Host "   Tentando usar ID 1 mesmo..." -ForegroundColor Yellow
    $produtoId = 1
}

Write-Host "`n1. Verificando produto antes de sincronizar..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$produtoId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($status.synced) {
        Write-Host "   Produto ja sincronizado!" -ForegroundColor Cyan
        Write-Host "   Bling ID: $($status.bling_id)" -ForegroundColor Cyan
        Write-Host "   Bling Codigo: $($status.bling_codigo)" -ForegroundColor Cyan
        Write-Host "   Status: $($status.status)" -ForegroundColor Cyan
    } else {
        Write-Host "   Produto ainda nao sincronizado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   AVISO: Nao foi possivel verificar status: $_" -ForegroundColor Yellow
}

# 2. Sincronizar produto
Write-Host "`n2. Sincronizando produto ID $produtoId..." -ForegroundColor Yellow
try {
    $start = Get-Date
    $result = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/sync/$produtoId" `
        -Method POST -Headers $headers -ErrorAction Stop
    $elapsed = ((Get-Date) - $start).TotalSeconds
    
    if ($result.success) {
        Write-Host "   OK! Produto sincronizado" -ForegroundColor Green
        Write-Host "   Acao: $($result.action)" -ForegroundColor Cyan
        Write-Host "   Bling ID: $($result.bling_product_id)" -ForegroundColor Cyan
        Write-Host "   Bling Codigo: $($result.bling_codigo)" -ForegroundColor Cyan
        Write-Host "   Tempo: $([math]::Round($elapsed, 2)) segundos" -ForegroundColor Cyan
    } else {
        Write-Host "   ERRO ao sincronizar" -ForegroundColor Red
        Write-Host "   Erro: $($result.error)" -ForegroundColor Red
        if ($result.errors) {
            Write-Host "   Detalhes:" -ForegroundColor Yellow
            $result.errors | ForEach-Object {
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
            if ($errorJson.errors) {
                $errorJson.errors | ForEach-Object {
                    Write-Host "     - $_" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
}

# 3. Verificar status apos sincronizacao
Write-Host "`n3. Verificando status apos sincronizacao..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$produtoId" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($status.synced) {
        Write-Host "   OK! Produto sincronizado com sucesso" -ForegroundColor Green
        Write-Host "   Bling ID: $($status.bling_id)" -ForegroundColor Cyan
        Write-Host "   Bling Codigo: $($status.bling_codigo)" -ForegroundColor Cyan
        Write-Host "   Status: $($status.status)" -ForegroundColor Cyan
        Write-Host "   Ultima sincronizacao: $($status.ultima_sincronizacao)" -ForegroundColor Cyan
    } else {
        Write-Host "   AVISO: Produto ainda nao sincronizado" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ERRO: $_" -ForegroundColor Red
}

Write-Host "`n=== TESTE CONCLUIDO ===" -ForegroundColor Cyan
Write-Host "`nPROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host "1. Verifique o produto no painel do Bling" -ForegroundColor Cyan
Write-Host "2. Confirme que NCM, preco e estoque estao corretos" -ForegroundColor Cyan
Write-Host "3. Verifique logs no banco: SELECT * FROM bling_sync_logs WHERE entity_type = 'produto'" -ForegroundColor Cyan

