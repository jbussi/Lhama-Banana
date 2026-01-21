# Script para ver estrutura completa do produto do Bling
# ============================================================

$baseUrl = "http://localhost:5000/api/bling"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "DEBUG - ESTRUTURA COMPLETA DO PRODUTO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/produtos/debug?limit=1" -Method GET -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "`n[OK] Produto encontrado" -ForegroundColor Green
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "ESTRUTURA COMPLETA DO PRODUTO (JSON):" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host ($response.sample_product | ConvertTo-Json -Depth 10) -ForegroundColor Gray
        
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "CHAVES DO PRODUTO:" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Cyan
        $response.product_keys | ForEach-Object {
            Write-Host "  - $_" -ForegroundColor White
        }
        
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "CAMPOS CUSTOMIZADOS BRUTOS:" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Cyan
        if ($response.custom_fields_raw -and $response.custom_fields_raw -ne 'Nenhum campo customizado encontrado') {
            Write-Host ($response.custom_fields_raw | ConvertTo-Json -Depth 5) -ForegroundColor Gray
        } else {
            Write-Host "  Nenhum campo customizado encontrado" -ForegroundColor Yellow
        }
        
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "CAMPOS CUSTOMIZADOS EXTRAIDOS:" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Cyan
        if ($response.custom_fields_extracted -and $response.custom_fields_extracted.Count -gt 0) {
            $response.custom_fields_extracted.PSObject.Properties | ForEach-Object {
                Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor Green
            }
        } else {
            Write-Host "  Nenhum campo extraido" -ForegroundColor Yellow
        }
        
        # Verificar campos que possam conter dados customizados
        Write-Host "`n============================================================" -ForegroundColor Cyan
        Write-Host "PROCURANDO CAMPOS RELACIONADOS:" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Cyan
        
        $produto = $response.sample_product
        
        # Verificar todas as chaves que possam conter campos customizados
        $produto.PSObject.Properties | ForEach-Object {
            $key = $_.Name
            $value = $_.Value
            
            if ($key -match 'campo|custom|field|atributo|attribute' -or $key -match 'categoria|tecido|estampa|tamanho' -or $key -match 'tipo|material|design|size') {
                Write-Host "  [$key]:" -ForegroundColor Cyan
                if ($value -is [Array]) {
                    Write-Host ($value | ConvertTo-Json -Depth 3) -ForegroundColor Gray
                } elseif ($value -is [PSCustomObject]) {
                    Write-Host ($value | ConvertTo-Json -Depth 3) -ForegroundColor Gray
                } else {
                    Write-Host "    $value" -ForegroundColor Gray
                }
            }
        }
        
    } else {
        Write-Host "[ERRO] $($response.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERRO] Erro ao buscar produto: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
