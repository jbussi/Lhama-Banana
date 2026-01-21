# Script para testar sincronização de categorias e produtos do Bling
# ===================================================================

$baseUrl = "http://localhost:5000/api/bling"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TESTE DE SINCRONIZACAO - CATEGORIAS E PRODUTOS DO BLING" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Listar categorias do Bling (antes de sincronizar)
Write-Host "`n1. Listando categorias do Bling..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/categorias" -Method GET -ContentType "application/json"
    if ($response.success) {
        Write-Host "   [OK] Categorias encontradas no Bling: $($response.total)" -ForegroundColor Green
        if ($response.categories.Count -gt 0) {
            Write-Host "   Categorias:" -ForegroundColor Cyan
            foreach ($cat in $response.categories) {
                $nome = $cat.nome -or $cat.descricao -or "Sem nome"
                Write-Host "     - $nome" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "   [AVISO] Nao foi possivel listar categorias: $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [AVISO] Endpoint de categorias pode nao existir ou erro ao buscar: $_" -ForegroundColor Yellow
}

# 2. Sincronizar categorias do Bling
Write-Host "`n2. Sincronizando categorias do Bling para o banco local..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/categorias/sync" -Method POST -ContentType "application/json"
    if ($response.success) {
        Write-Host "   [OK] Sincronizacao concluida!" -ForegroundColor Green
        Write-Host "   Total de categorias: $($response.total)" -ForegroundColor Cyan
        Write-Host "   Categorias sincronizadas: $($response.success_count)" -ForegroundColor Cyan
        
        if ($response.results.Count -gt 0) {
            Write-Host "   Detalhes:" -ForegroundColor Cyan
            foreach ($result in $response.results) {
                if ($result.success) {
                    Write-Host "     [OK] $($result.bling_category) -> Categoria ID: $($result.local_categoria_id)" -ForegroundColor Green
                } else {
                    Write-Host "     [ERRO] $($result.bling_category): $($result.error)" -ForegroundColor Red
                }
            }
        }
    } else {
        Write-Host "   [ERRO] Falha na sincronizacao: $($response.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERRO] Erro ao sincronizar categorias: $_" -ForegroundColor Red
    Write-Host "   Continuando com importacao de produtos..." -ForegroundColor Yellow
}

# 3. Verificar categorias locais
Write-Host "`n3. Verificando categorias locais..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/admin/cadastros/categorias" -Method GET -ContentType "application/json"
    Write-Host "   [OK] Categorias locais encontradas: $($response.categorias.Count)" -ForegroundColor Green
    if ($response.categorias.Count -gt 0) {
        Write-Host "   Categorias locais:" -ForegroundColor Cyan
        foreach ($cat in $response.categorias) {
            Write-Host "     - $($cat.nome) (ID: $($cat.id))" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   [ERRO] Erro ao listar categorias locais: $_" -ForegroundColor Red
}

# 4. Importar produtos do Bling
Write-Host "`n4. Importando produtos do Bling..." -ForegroundColor Yellow
try {
    $body = @{
        limit = 10
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/produtos/import" -Method POST -Body $body -ContentType "application/json"
    
    if ($response.success) {
        Write-Host "   [OK] Importacao concluida!" -ForegroundColor Green
        Write-Host "   Total processado: $($response.total)" -ForegroundColor Cyan
        Write-Host "   Sucessos: $($response.success_count)" -ForegroundColor Green
        
        if ($response.results.Count -gt 0) {
            Write-Host "`n   Detalhes dos produtos:" -ForegroundColor Cyan
            foreach ($result in $response.results) {
                if ($result.success) {
                    Write-Host "     [OK] Produto ID $($result.produto_id) (Bling ID: $($result.bling_id))" -ForegroundColor Green
                    if ($result.categoria_id) {
                        Write-Host "       Categoria ID: $($result.categoria_id)" -ForegroundColor Gray
                    }
                    if ($result.estampa_id) {
                        Write-Host "       Estampa ID: $($result.estampa_id)" -ForegroundColor Gray
                    }
                    if ($result.tamanho_id) {
                        Write-Host "       Tamanho ID: $($result.tamanho_id)" -ForegroundColor Gray
                    }
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

# 5. Resumo final
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "TESTE CONCLUIDO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nProximos passos:" -ForegroundColor Yellow
Write-Host "  - Verificar produtos importados na loja" -ForegroundColor Gray
Write-Host "  - Verificar categorias sincronizadas" -ForegroundColor Gray
Write-Host "  - Testar exibicao na loja (GET /api/store/products)" -ForegroundColor Gray
