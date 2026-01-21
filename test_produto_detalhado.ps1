# Teste detalhado de um produto especifico
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$produtoId = 10

$headers = @{
    "ngrok-skip-browser-warning" = "true"
    "Content-Type" = "application/json"
}

Write-Host "Testando sincronizacao do produto $produtoId..." -ForegroundColor Yellow
Write-Host ""

try {
    Write-Host "Enviando requisicao para: $ngrokUrl/api/bling/produtos/sync/$produtoId" -ForegroundColor Gray
    
    $response = Invoke-WebRequest -Uri "$ngrokUrl/api/bling/produtos/sync/$produtoId" -Method POST -Headers $headers -ErrorAction Stop
    
    Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Resposta (raw): $($response.Content)" -ForegroundColor Cyan
    
    if ($response.Content) {
        Write-Host "Resposta (parseada):" -ForegroundColor Cyan
        $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10 | Write-Host
    } else {
        Write-Host "Resposta vazia!" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Erro capturado:" -ForegroundColor Red
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "Status: $statusCode" -ForegroundColor Yellow
    
    if ($_.Exception.Response) {
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            $stream.Close()
            
            Write-Host ""
            Write-Host "Corpo da resposta (raw):" -ForegroundColor Yellow
            Write-Host $responseBody -ForegroundColor Gray
            Write-Host ""
            
            if ($responseBody.Trim()) {
                try {
                    $errorJson = $responseBody | ConvertFrom-Json
                    Write-Host "Erro parseado:" -ForegroundColor Yellow
                    $errorJson | ConvertTo-Json -Depth 10 | Write-Host
                    
                    if ($errorJson.details) {
                        Write-Host ""
                        Write-Host "Detalhes do erro:" -ForegroundColor Red
                        if ($errorJson.details -is [array]) {
                            foreach ($detail in $errorJson.details) {
                                Write-Host "  - $detail" -ForegroundColor Red
                            }
                        } else {
                            Write-Host "  $($errorJson.details)" -ForegroundColor Red
                        }
                    }
                } catch {
                    Write-Host "Nao foi possivel parsear como JSON" -ForegroundColor Gray
                }
            } else {
                Write-Host "Resposta vazia - verifique os logs do servidor Flask" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Erro ao ler resposta: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "Nao foi possivel obter resposta do servidor" -ForegroundColor Red
        Write-Host "Erro completo: $($_.Exception)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Verificando dados do produto no banco..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/status/$produtoId" -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "Status do produto:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 5 | Write-Host
} catch {
    Write-Host "Erro ao verificar status: $($_.Exception.Message)" -ForegroundColor Red
}
