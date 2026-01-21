# Script para testar sincronização completa de categorias e valores do Bling
# =========================================================================

$baseUrl = "http://localhost:5000/api/bling"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "SINCRONIZACAO COMPLETA - CATEGORIAS E VALORES DO BLING" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`nEste processo vai:" -ForegroundColor Yellow
Write-Host "  1. Remover categorias, tecidos, estampas e tamanhos existentes" -ForegroundColor Gray
Write-Host "  2. Buscar produtos do Bling e extrair valores únicos" -ForegroundColor Gray
Write-Host "  3. Criar categorias, tecidos, estampas e tamanhos no banco" -ForegroundColor Gray
Write-Host "  4. Sincronizar produtos novamente" -ForegroundColor Gray

$confirma = Read-Host "`nDeseja continuar? (S/N)"
if ($confirma -ne "S" -and $confirma -ne "s") {
    Write-Host "Operacao cancelada." -ForegroundColor Yellow
    exit
}

# 1. Primeiro, ver valores únicos que serão extraídos
Write-Host "`n1. Extraindo valores únicos do Bling..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/valores-unicos?limit=500" -Method GET -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "   [OK] Valores extraidos!" -ForegroundColor Green
        Write-Host "   Total de produtos processados: $($response.total_produtos_processados)" -ForegroundColor Cyan
        
        Write-Host "`n   Categorias encontradas: $($response.valores.categorias.Count)" -ForegroundColor Cyan
        if ($response.valores.categorias.Count -gt 0) {
            Write-Host "   - $($response.valores.categorias -join ', ')" -ForegroundColor Gray
        }
        
        Write-Host "`n   Tecidos encontrados: $($response.valores.tecidos.Count)" -ForegroundColor Cyan
        if ($response.valores.tecidos.Count -gt 0) {
            Write-Host "   - $($response.valores.tecidos -join ', ')" -ForegroundColor Gray
        }
        
        Write-Host "`n   Estampas encontradas: $($response.valores.estampas.Count)" -ForegroundColor Cyan
        if ($response.valores.estampas.Count -gt 0) {
            Write-Host "   - $($response.valores.estampas -join ', ')" -ForegroundColor Gray
        }
        
        Write-Host "`n   Tamanhos encontrados: $($response.valores.tamanhos.Count)" -ForegroundColor Cyan
        if ($response.valores.tamanhos.Count -gt 0) {
            Write-Host "   - $($response.valores.tamanhos -join ', ')" -ForegroundColor Gray
        }
    } else {
        Write-Host "   [ERRO] Falha ao extrair valores: $($response.error)" -ForegroundColor Red
        exit
    }
} catch {
    Write-Host "   [ERRO] Erro ao extrair valores: $_" -ForegroundColor Red
    exit
}

# 2. Executar sincronização completa
Write-Host "`n2. Executando sincronizacao completa..." -ForegroundColor Yellow
try {
    $body = @{
        limit_products = 500
        clear_first = $true
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/sync-completo" -Method POST -Body $body -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "   [OK] Sincronizacao concluida!" -ForegroundColor Green
        
        Write-Host "`n   RESUMO:" -ForegroundColor Cyan
        Write-Host "   - Categorias criadas: $($response.resumo.categorias)" -ForegroundColor Green
        Write-Host "   - Tecidos criados: $($response.resumo.tecidos)" -ForegroundColor Green
        Write-Host "   - Estampas criadas: $($response.resumo.estampas)" -ForegroundColor Green
        Write-Host "   - Tamanhos criados: $($response.resumo.tamanhos)" -ForegroundColor Green
        Write-Host "   - Produtos sincronizados: $($response.resumo.produtos)" -ForegroundColor Green
        
    } else {
        Write-Host "   [ERRO] Falha na sincronizacao: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERRO] Erro ao sincronizar: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "SINCRONIZACAO CONCLUIDA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
