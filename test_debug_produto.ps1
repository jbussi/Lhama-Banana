# Teste de debug do produto
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"
$produtoId = 10

$headers = @{
    "ngrok-skip-browser-warning" = "true"
    "Content-Type" = "application/json"
}

Write-Host "Testando endpoint de debug do produto $produtoId..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/produtos/debug/$produtoId" -Method GET -Headers $headers -ErrorAction Stop
    
    Write-Host "Resposta recebida:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
} catch {
    Write-Host "Erro:" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Yellow
    
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $responseBody = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        
        Write-Host "Corpo: $responseBody" -ForegroundColor Gray
    }
}
