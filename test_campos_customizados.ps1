# Script para testar sincronização com campos customizados do Bling
# ===================================================================

$baseUrl = "http://localhost:5000/api/bling"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TESTE - CAMPOS CUSTOMIZADOS DO BLING" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Debug: Ver estrutura de produto e campos customizados
Write-Host "`n1. Verificando estrutura de produto e campos customizados..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/produtos/debug?limit=1" -Method GET -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "   [OK] Produto encontrado" -ForegroundColor Green
        
        if ($response.custom_fields_raw -and $response.custom_fields_raw -ne 'Nenhum campo customizado encontrado') {
            Write-Host "`n   Campos customizados brutos (do Bling):" -ForegroundColor Cyan
            $response.custom_fields_raw | ForEach-Object {
                $nome = $_.nome -or $_.name
                $valor = $_.valor -or $_.value
                Write-Host "     - $nome : $valor" -ForegroundColor Gray
            }
        } else {
            Write-Host "   [AVISO] Nenhum campo customizado encontrado no produto" -ForegroundColor Yellow
        }
        
        if ($response.custom_fields_extracted) {
            Write-Host "`n   Campos customizados extraídos e mapeados:" -ForegroundColor Cyan
            $response.custom_fields_extracted.PSObject.Properties | ForEach-Object {
                Write-Host "     - $($_.Name) : $($_.Value)" -ForegroundColor Green
            }
        }
        
        Write-Host "`n   Chaves do produto:" -ForegroundColor Cyan
        $response.product_keys | ForEach-Object {
            Write-Host "     - $_" -ForegroundColor Gray
        }
    } else {
        Write-Host "   [AVISO] $($response.message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [ERRO] Erro ao buscar produto: $_" -ForegroundColor Red
}

# 2. Importar produtos (vai usar campos customizados)
Write-Host "`n2. Importando produtos do Bling (usando campos customizados)..." -ForegroundColor Yellow

try {
    $body = @{
        limit = 5
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/produtos/import" -Method POST -Body $body -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "   [OK] Importacao concluida!" -ForegroundColor Green
        Write-Host "   Total processado: $($response.total)" -ForegroundColor Cyan
        Write-Host "   Sucessos: $($response.success_count)" -ForegroundColor Green
        Write-Host "   Erros: $($response.errors)" -ForegroundColor $(if ($response.errors -gt 0) { "Red" } else { "Green" })
        
        if ($response.results.Count -gt 0) {
            Write-Host "`n   Detalhes dos produtos sincronizados:" -ForegroundColor Cyan
            foreach ($result in $response.results) {
                if ($result.success) {
                    Write-Host "     [OK] Produto ID $($result.produto_id) (Bling ID: $($result.bling_id))" -ForegroundColor Green
                    
                    if ($result.campos_customizados_usados) {
                        Write-Host "       Campos customizados usados:" -ForegroundColor Yellow
                        $result.campos_customizados_usados.PSObject.Properties | ForEach-Object {
                            Write-Host "         - $($_.Name): $($_.Value)" -ForegroundColor Gray
                        }
                    }
                    
                    Write-Host "       Categoria ID: $($result.categoria_id)" -ForegroundColor Gray
                    Write-Host "       Tecido ID: $($result.tecido_id)" -ForegroundColor Gray
                    Write-Host "       Estampa ID: $($result.estampa_id)" -ForegroundColor Gray
                    Write-Host "       Tamanho ID: $($result.tamanho_id)" -ForegroundColor Gray
                } else {
                    Write-Host "     [ERRO] Bling ID $($result.bling_id): $($result.error)" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "   [ERRO] Falha na importacao: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERRO] Erro ao importar produtos: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

# 3. Resumo
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "TESTE CONCLUIDO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nProximos passos:" -ForegroundColor Yellow
Write-Host "  - Verificar produtos sincronizados no banco" -ForegroundColor Gray
Write-Host "  - Verificar categorias, tecidos, estampas e tamanhos criados" -ForegroundColor Gray
Write-Host "  - Testar exibicao na loja" -ForegroundColor Gray
