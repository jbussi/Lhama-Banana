# Script para testar busca de um produto específico do Bling
# ============================================================

$baseUrl = "http://localhost:5000/api/bling"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TESTE - BUSCAR PRODUTO DO BLING" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Primeiro, buscar produtos do Bling para ver o formato
Write-Host "`n1. Buscando produtos do Bling (limite 5)..." -ForegroundColor Yellow

try {
    # Buscar produtos diretamente via API do Bling
    # Primeiro precisamos pegar um produto para ver sua estrutura
    
    # Vamos testar a importação de apenas 1 produto para ver o formato
    $body = @{
        limit = 1
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$baseUrl/produtos/import" -Method POST -Body $body -ContentType "application/json" -ErrorAction SilentlyContinue
    
    if ($response) {
        Write-Host "   Resposta da importacao:" -ForegroundColor Cyan
        Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor Gray
    }
} catch {
    Write-Host "   [ERRO] Erro ao importar: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Detalhes: $responseBody" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "TESTE CONCLUIDO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
