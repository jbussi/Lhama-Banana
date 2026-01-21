# Teste Completo - Todas as Vendas Disponiveis
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE: TODAS AS VENDAS DISPONIVEIS ===" -ForegroundColor Cyan

# ============================================
# CONFIGURACAO
# ============================================
$maxVendaId = 50  # Testar IDs de 1 a 50
$vendasTestadas = @()
$vendasSucesso = @()
$vendasErro = @()
$vendasNaoExistem = @()

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
# PASSO 2: Testar todas as vendas
# ============================================
Write-Host "`n=== PASSO 2: Testando vendas (IDs 1 a $maxVendaId) ===" -ForegroundColor Yellow
Write-Host "   Isso pode levar alguns minutos..." -ForegroundColor Gray

$progress = 0
for ($vendaId = 1; $vendaId -le $maxVendaId; $vendaId++) {
    $progress++
    $percent = [math]::Round(($progress / $maxVendaId) * 100, 1)
    Write-Progress -Activity "Testando Vendas" -Status "Venda ID $vendaId de $maxVendaId ($percent%)" -PercentComplete $percent
    
    # Verificar se venda existe (tentando buscar info)
    try {
        $infoResponse = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/info/$vendaId" `
            -Method GET -Headers $headers -ErrorAction Stop
        
        # Se chegou aqui, a venda existe (mesmo que não sincronizada)
        $vendaInfo = @{
            Id = $vendaId
            Existe = $true
            Sincronizada = $infoResponse.synced
            BlingPedidoId = if ($infoResponse.synced) { $infoResponse.bling_pedido_id } else { $null }
        }
        
        # Tentar sincronizar
        try {
            $syncResponse = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/sync/$vendaId" `
                -Method POST -Headers $headers -ErrorAction Stop
            
            if ($syncResponse.success) {
                $vendaInfo.Sucesso = $true
                $vendaInfo.Acao = $syncResponse.action
                $vendaInfo.BlingPedidoId = $syncResponse.bling_pedido_id
                $vendaInfo.Mensagem = $syncResponse.message
                $vendasSucesso += $vendaInfo
                Write-Host "   [OK] Venda ${vendaId}: Sincronizada com sucesso!" -ForegroundColor Green
            } else {
                $vendaInfo.Sucesso = $false
                $vendaInfo.Erro = $syncResponse.error
                $vendaInfo.Detalhes = $syncResponse.details
                $vendasErro += $vendaInfo
                Write-Host "   [ERRO] Venda ${vendaId}: $($syncResponse.error)" -ForegroundColor Red
            }
        } catch {
            $vendaInfo.Sucesso = $false
            if ($_.ErrorDetails.Message) {
                try {
                    $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
                    $vendaInfo.Erro = $errorJson.error
                    $vendaInfo.Detalhes = $errorJson.message
                } catch {
                    $vendaInfo.Erro = $_.ErrorDetails.Message
                }
            } else {
                $vendaInfo.Erro = $_.Exception.Message
            }
            $vendasErro += $vendaInfo
            Write-Host "   [ERRO] Venda ${vendaId}: Erro na sincronizacao" -ForegroundColor Red
        }
        
        $vendasTestadas += $vendaInfo
        
    } catch {
        # Venda não existe ou erro de conexão
        $vendaInfo = @{
            Id = $vendaId
            Existe = $false
            Sucesso = $false
            Erro = "Venda nao encontrada"
        }
        $vendasNaoExistem += $vendaInfo
        # Não mostrar erro para vendas que não existem (normal)
    }
    
    # Pequeno delay para não sobrecarregar a API
    Start-Sleep -Milliseconds 200
}

Write-Progress -Activity "Testando Vendas" -Completed

# ============================================
# PASSO 3: Resumo dos resultados
# ============================================
Write-Host "`n=== RESUMO DOS RESULTADOS ===" -ForegroundColor Cyan

Write-Host "`nESTATISTICAS:" -ForegroundColor Yellow
Write-Host "   Total testado: $($vendasTestadas.Count)" -ForegroundColor White
Write-Host "   [OK] Sucesso: $($vendasSucesso.Count)" -ForegroundColor Green
Write-Host "   [ERRO] Erro: $($vendasErro.Count)" -ForegroundColor Red
Write-Host "   [AVISO] Nao existem: $($vendasNaoExistem.Count)" -ForegroundColor Yellow

# ============================================
# PASSO 4: Detalhes das vendas com sucesso
# ============================================
if ($vendasSucesso.Count -gt 0) {
    Write-Host "`n[OK] VENDAS SINCRONIZADAS COM SUCESSO:" -ForegroundColor Green
    foreach ($venda in $vendasSucesso) {
        Write-Host "   Venda ID $($venda.Id):" -ForegroundColor Cyan
        Write-Host "      - Acao: $($venda.Acao)" -ForegroundColor White
        Write-Host "      - Bling Pedido ID: $($venda.BlingPedidoId)" -ForegroundColor White
        Write-Host "      - Mensagem: $($venda.Mensagem)" -ForegroundColor Gray
    }
}

# ============================================
# PASSO 5: Detalhes das vendas com erro
# ============================================
if ($vendasErro.Count -gt 0) {
    Write-Host "`n[ERRO] VENDAS COM ERRO:" -ForegroundColor Red
    
    # Agrupar erros por tipo
    $errosPorTipo = @{}
    foreach ($venda in $vendasErro) {
        $tipoErro = $venda.Erro
        if (-not $errosPorTipo.ContainsKey($tipoErro)) {
            $errosPorTipo[$tipoErro] = @()
        }
        $errosPorTipo[$tipoErro] += $venda.Id
    }
    
    foreach ($tipoErro in $errosPorTipo.Keys) {
        $ids = $errosPorTipo[$tipoErro] -join ", "
        Write-Host "`n   Erro: $tipoErro" -ForegroundColor Yellow
        Write-Host "   Vendas afetadas: $ids" -ForegroundColor White
        
        # Mostrar detalhes de uma venda exemplo
        $vendaExemplo = $vendasErro | Where-Object { $_.Erro -eq $tipoErro } | Select-Object -First 1
        if ($vendaExemplo.Detalhes) {
            Write-Host "   Detalhes: $($vendaExemplo.Detalhes)" -ForegroundColor Gray
        }
    }
    
    # Lista completa
    Write-Host "`n   Lista completa de vendas com erro:" -ForegroundColor Yellow
    foreach ($venda in $vendasErro) {
        Write-Host "      - Venda $($venda.Id): $($venda.Erro)" -ForegroundColor White
    }
}

# ============================================
# PASSO 6: Testar aprovacao nas vendas sincronizadas
# ============================================
if ($vendasSucesso.Count -gt 0) {
    Write-Host "`n=== PASSO 6: Testando aprovacao das vendas sincronizadas ===" -ForegroundColor Yellow
    
    $aprovacoesSucesso = 0
    $aprovacoesErro = 0
    
    foreach ($venda in $vendasSucesso) {
        $vendaId = $venda.Id
        Write-Host "`n   Testando aprovacao da venda $vendaId..." -ForegroundColor Cyan
        
        try {
            $approveResponse = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/approve/$vendaId" `
                -Method POST -Headers $headers -ErrorAction Stop
            
            if ($approveResponse.success) {
                $aprovacoesSucesso++
                Write-Host "      [OK] Aprovada! Situacao: $($approveResponse.situacao_nova)" -ForegroundColor Green
            } else {
                $aprovacoesErro++
                Write-Host "      [AVISO] $($approveResponse.error)" -ForegroundColor Yellow
            }
        } catch {
            $aprovacoesErro++
                Write-Host "      [ERRO] Erro: $_" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 200
    }
    
    Write-Host "`n   Resumo de aprovacoes:" -ForegroundColor Yellow
    Write-Host "      [OK] Aprovadas: $aprovacoesSucesso" -ForegroundColor Green
    Write-Host "      [ERRO] Erros: $aprovacoesErro" -ForegroundColor Red
}

# ============================================
# PASSO 7: Resumo final
# ============================================
Write-Host "`n=== RESUMO FINAL ===" -ForegroundColor Cyan
Write-Host "`n[OK] FUNCIONANDO:" -ForegroundColor Green
Write-Host "   - Vendas sincronizadas: $($vendasSucesso.Count)" -ForegroundColor White
if ($vendasSucesso.Count -gt 0) {
    Write-Host "   - Aprovacoes bem-sucedidas: $aprovacoesSucesso" -ForegroundColor White
}

Write-Host "`n[ERRO] PROBLEMAS ENCONTRADOS:" -ForegroundColor Red
Write-Host "   - Vendas com erro: $($vendasErro.Count)" -ForegroundColor White
if ($vendasErro.Count -gt 0) {
    Write-Host "   - Principais erros:" -ForegroundColor White
    $errosPorTipo.Keys | ForEach-Object {
        $count = $errosPorTipo[$_].Count
        Write-Host "      - $_ ($count vendas)" -ForegroundColor Gray
    }
}

Write-Host "`nPROXIMOS PASSOS:" -ForegroundColor Yellow
if ($vendasSucesso.Count -gt 0) {
    Write-Host "   [OK] $($vendasSucesso.Count) venda(s) pronta(s) para processamento!" -ForegroundColor Green
    Write-Host "   - Verifique no Bling se os pedidos foram criados corretamente" -ForegroundColor Cyan
    Write-Host "   - Verifique se os clientes foram sincronizados" -ForegroundColor Cyan
    Write-Host "   - Verifique se os produtos estao corretos" -ForegroundColor Cyan
}

if ($vendasErro.Count -gt 0) {
    Write-Host "   - Corrija os problemas nas vendas com erro" -ForegroundColor Cyan
    Write-Host "   - Verifique dados fiscais, produtos e enderecos" -ForegroundColor Cyan
}

Write-Host "`n=== TESTE CONCLUIDO ===" -ForegroundColor Cyan
