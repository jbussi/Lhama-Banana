# Teste ETAPA 2 - Estrutura de Integracao
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$headers = @{"ngrok-skip-browser-warning"="true"}

Write-Host "`n=== TESTE ETAPA 2: ESTRUTURA DE INTEGRACAO ===" -ForegroundColor Cyan

# 1. Teste de Conexao Basica
Write-Host "`n1. Testando conexao com API Bling..." -ForegroundColor Yellow
try {
    $start = Get-Date
    $test = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/test" `
        -Method GET -Headers $headers -ErrorAction Stop
    $elapsed = ((Get-Date) - $start).TotalSeconds
    
    Write-Host "   OK! Conexao estabelecida" -ForegroundColor Green
    Write-Host "   Status: $($test.message)" -ForegroundColor Cyan
    Write-Host "   Status Code: $($test.status_code)" -ForegroundColor Cyan
    Write-Host "   Produtos encontrados: $($test.products_count)" -ForegroundColor Cyan
    Write-Host "   Tempo: $([math]::Round($elapsed, 2)) segundos" -ForegroundColor Cyan
} catch {
    Write-Host "   ERRO: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        try {
            $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "   Tipo: $($errorJson.error)" -ForegroundColor Yellow
            Write-Host "   Mensagem: $($errorJson.message)" -ForegroundColor Yellow
        } catch {
            Write-Host "   Detalhes: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
    }
}

# 2. Teste de Rate Limiting
Write-Host "`n2. Testando Rate Limiting (5 requisicoes)..." -ForegroundColor Yellow
$times = @()
1..5 | ForEach-Object {
    $num = $_
    $start = Get-Date
    try {
        Invoke-RestMethod -Uri "$ngrokUrl/api/bling/test" `
            -Method GET -Headers $headers | Out-Null
        $elapsed = ((Get-Date) - $start).TotalSeconds
        $times += $elapsed
        Write-Host "   Requisicao $num : $([math]::Round($elapsed, 2))s" -ForegroundColor Cyan
    } catch {
        Write-Host "   Requisicao $num : ERRO" -ForegroundColor Red
    }
}

if ($times.Count -gt 0) {
    $avg = ($times | Measure-Object -Average).Average
    $min = ($times | Measure-Object -Minimum).Minimum
    Write-Host "   Tempo medio: $([math]::Round($avg, 2))s" -ForegroundColor Cyan
    Write-Host "   Tempo minimo: $([math]::Round($min, 2))s" -ForegroundColor Cyan
    
    if ($min -ge 0.4) {
        Write-Host "   OK! Rate limiting funcionando (delay minimo aplicado)" -ForegroundColor Green
    } else {
        Write-Host "   AVISO: Rate limiting pode nao estar funcionando" -ForegroundColor Yellow
    }
}

# 3. Verificar Tokens
Write-Host "`n3. Verificando status dos tokens..." -ForegroundColor Yellow
try {
    $tokens = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/tokens" `
        -Method GET -Headers $headers -ErrorAction Stop
    
    if ($tokens.authorized) {
        Write-Host "   OK! Tokens validos" -ForegroundColor Green
        Write-Host "   Status: $($tokens.status)" -ForegroundColor Cyan
        Write-Host "   Expira em: $($tokens.expires_at)" -ForegroundColor Cyan
    } else {
        Write-Host "   AVISO: Tokens nao autorizados" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   AVISO: Nao foi possivel verificar tokens: $_" -ForegroundColor Yellow
}

Write-Host "`n=== TESTE CONCLUIDO ===" -ForegroundColor Cyan
Write-Host "`nVerifique os logs do Flask para mais detalhes:" -ForegroundColor Yellow
Write-Host "docker compose logs flask -f --tail=50" -ForegroundColor Cyan
