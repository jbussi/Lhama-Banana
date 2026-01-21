# Script PowerShell para testar sincronização de situações do Bling
# Execute após iniciar o Flask

Write-Host "🧪 Testando Sincronização de Situações do Bling" -ForegroundColor Cyan
Write-Host "=" * 60

$baseUrl = "http://localhost:5000"
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

# Usar ngrok se disponível, senão localhost
$useNgrok = $false
try {
    $test = Invoke-WebRequest -Uri "$ngrokUrl/api/bling/tokens" -Method GET -Headers @{"ngrok-skip-browser-warning"="true"} -TimeoutSec 5 -ErrorAction Stop
    $useNgrok = $true
    $baseUrl = $ngrokUrl
    Write-Host "✅ Usando ngrok: $ngrokUrl" -ForegroundColor Green
} catch {
    Write-Host "⚠️ ngrok não disponível, usando localhost" -ForegroundColor Yellow
}

# 1. Sincronizar situações do Bling
Write-Host "`n📤 Sincronizando situações do Bling..." -ForegroundColor Yellow
try {
    $uri = "$baseUrl/api/bling/situacoes/sync"
    $headers = @{
        "Content-Type" = "application/json"
    }
    if ($useNgrok) {
        $headers["ngrok-skip-browser-warning"] = "true"
    }
    
    $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -ErrorAction Stop
    
    Write-Host "✅ Resposta:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
    if ($response.success) {
        Write-Host "`n🎉 Sincronização bem-sucedida!" -ForegroundColor Green
        Write-Host "   Total: $($response.total)" -ForegroundColor Cyan
        Write-Host "   Sincronizadas: $($response.sincronizadas)" -ForegroundColor Cyan
        Write-Host "   Atualizadas: $($response.atualizadas)" -ForegroundColor Cyan
    } else {
        Write-Host "`n❌ Erro na sincronização:" -ForegroundColor Red
        Write-Host "   $($response.error)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n❌ Erro ao fazer requisição:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "`n💡 Certifique-se de que:" -ForegroundColor Yellow
    Write-Host "   1. Flask está rodando" -ForegroundColor Cyan
    Write-Host "   2. Bling está autorizado (POST /api/bling/authorize)" -ForegroundColor Cyan
    Write-Host "   3. Você está autenticado como admin" -ForegroundColor Cyan
    exit 1
}

# 2. Listar situações sincronizadas
Write-Host "`n📋 Listando situações sincronizadas..." -ForegroundColor Yellow
try {
    $uri = "$baseUrl/api/bling/situacoes"
    $headers = @{}
    if ($useNgrok) {
        $headers["ngrok-skip-browser-warning"] = "true"
    }
    
    $response = Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
    
    Write-Host "✅ Situações encontradas: $($response.total)" -ForegroundColor Green
    Write-Host "`n📊 Situações do Bling:" -ForegroundColor Cyan
    Write-Host ("-" * 80)
    
    foreach ($situacao in $response.situacoes) {
        $status = if ($situacao.status_site) { "-> $($situacao.status_site)" } else { "(sem mapeamento)" }
        $linha = "ID: $($situacao.bling_situacao_id) | Nome: $($situacao.nome) | $status"
        Write-Host $linha -ForegroundColor White
        if ($situacao.cor) {
            Write-Host "   Cor: $($situacao.cor)" -ForegroundColor Gray
        }
    }
    
    Write-Host ("-" * 80)
    
    # Mostrar IDs importantes
    Write-Host "`n🎯 IDs importantes para mapeamento:" -ForegroundColor Yellow
    $situacoes_importantes = @(
        "Em aberto",
        "Em andamento",
        "Atendido",
        "Cancelado",
        "Venda Agenciada",
        "Em digitação",
        "Verificado",
        "Venda Atendimento Humano",
        "Logística"
    )
    
    foreach ($nome in $situacoes_importantes) {
        $sit = $response.situacoes | Where-Object { $_.nome -eq $nome }
        if ($sit) {
            Write-Host "   $nome : ID $($sit.bling_situacao_id)" -ForegroundColor Cyan
        }
    }
    
} catch {
    Write-Host "`n❌ Erro ao listar situações:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Teste concluído!" -ForegroundColor Green
Write-Host "`n💡 Próximos passos:" -ForegroundColor Yellow
Write-Host "   1. Mapear situações para status do site usando:" -ForegroundColor Cyan
Write-Host "      POST $baseUrl/api/bling/situacoes/<id>/map" -ForegroundColor White
Write-Host "      Body: {`"status_site`": `"em_processamento`"}" -ForegroundColor White
Write-Host "   2. Testar webhook quando pedido mudar de situação no Bling" -ForegroundColor Cyan
