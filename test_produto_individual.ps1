# Script para testar busca de produto individual do Bling
# ============================================================

$baseUrl = "http://localhost:5000/api/bling"
$produtoId = 16588734930  # ID do produto de teste

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TESTE - BUSCAR PRODUTO INDIVIDUAL DO BLING" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Produto ID: $produtoId" -ForegroundColor Yellow

# Buscar produto individual via endpoint de detalhes (se existir)
# Por enquanto, vamos verificar os logs do servidor ou criar um endpoint de debug específico

Write-Host "`nNota: Precisamos verificar se a API do Bling retorna campos customizados" -ForegroundColor Yellow
Write-Host "no endpoint GET /produtos/{id}" -ForegroundColor Yellow

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "VERIFICANDO PRODUTO NO BANCO LOCAL..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Verificar produto sincronizado no banco
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/admin/produtos" -Method GET -ContentType "application/json" -ErrorAction SilentlyContinue
    
    if ($response) {
        Write-Host "[OK] Produtos encontrados no banco local" -ForegroundColor Green
    }
} catch {
    Write-Host "[INFO] Endpoint de produtos admin pode não estar disponivel" -ForegroundColor Gray
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "TESTE CONCLUIDO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`nOBSERVACAO:" -ForegroundColor Yellow
Write-Host "Se os campos customizados nao aparecem, pode ser que:" -ForegroundColor Gray
Write-Host "  1. A API do Bling nao retorna campos customizados na listagem" -ForegroundColor Gray
Write-Host "  2. Os campos customizados precisam ser buscados individualmente" -ForegroundColor Gray
Write-Host "  3. O formato dos campos customizados pode ser diferente" -ForegroundColor Gray
Write-Host "`nSOLUCAO:" -ForegroundColor Yellow
Write-Host "Verifique no painel do Bling se os campos customizados estao preenchidos" -ForegroundColor Gray
Write-Host "e depois verifique os logs do servidor durante a sincronizacao." -ForegroundColor Gray
