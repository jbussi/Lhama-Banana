# Script para obter certificados SSL localmente usando ngrok
# Pré-requisito: ngrok deve estar rodando e expondo a porta 80

Write-Host "🔐 Obtendo Certificados SSL Localmente" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se estamos no diretório correto
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ ERRO: Execute este script no diretório Lhama-Banana" -ForegroundColor Red
    exit 1
}

# Carregar variáveis do .env
$envVars = @{}
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match '^\s*([^#][^=]+)=(.*)$' } | ForEach-Object {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        $envVars[$key] = $value
    }
} else {
    Write-Host "❌ Arquivo .env não encontrado!" -ForegroundColor Red
    exit 1
}

# Verificar variáveis obrigatórias
if (-not $envVars.ContainsKey("CERTBOT_EMAIL") -or [string]::IsNullOrWhiteSpace($envVars["CERTBOT_EMAIL"])) {
    Write-Host "❌ CERTBOT_EMAIL não encontrado no .env" -ForegroundColor Red
    Write-Host "   Adicione: CERTBOT_EMAIL=seu-email@exemplo.com" -ForegroundColor Yellow
    exit 1
}

if (-not $envVars.ContainsKey("CERTBOT_DOMAIN") -or [string]::IsNullOrWhiteSpace($envVars["CERTBOT_DOMAIN"])) {
    Write-Host "❌ CERTBOT_DOMAIN não encontrado no .env" -ForegroundColor Red
    Write-Host "   Adicione: CERTBOT_DOMAIN=seu-dominio.ngrok-free.dev" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Para obter um domínio ngrok:" -ForegroundColor Yellow
    Write-Host "   1. Instale ngrok: https://ngrok.com/download" -ForegroundColor White
    Write-Host "   2. Execute: ngrok http 80" -ForegroundColor White
    Write-Host "   3. Use a URL HTTPS gerada (ex: https://abc123.ngrok-free.dev)" -ForegroundColor White
    exit 1
}

$email = $envVars["CERTBOT_EMAIL"]
$domain = $envVars["CERTBOT_DOMAIN"]

Write-Host "📧 Email: $email" -ForegroundColor Cyan
Write-Host "🌐 Domínio: $domain" -ForegroundColor Cyan
Write-Host ""

# Verificar se ngrok está acessível
Write-Host "🔍 Verificando se o domínio está acessível..." -ForegroundColor Yellow
try {
    $testResponse = Invoke-WebRequest -Uri "http://$domain" -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Domínio acessível via HTTP" -ForegroundColor Green
} catch {
    Write-Host "❌ Domínio não está acessível: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Certifique-se de que:" -ForegroundColor Yellow
    Write-Host "   1. ngrok está rodando: ngrok http 80" -ForegroundColor White
    Write-Host "   2. O domínio no .env corresponde à URL do ngrok" -ForegroundColor White
    exit 1
}

Write-Host ""

# Verificar se NGINX está rodando
Write-Host "🔍 Verificando NGINX..." -ForegroundColor Yellow
$nginxStatus = docker-compose ps nginx 2>&1 | Select-String "Up"
if (-not $nginxStatus) {
    Write-Host "⚠️  NGINX não está rodando. Iniciando..." -ForegroundColor Yellow
    docker-compose up -d nginx
    Start-Sleep -Seconds 5
}

Write-Host "✅ NGINX verificado" -ForegroundColor Green
Write-Host ""

# Obter certificado SSL (staging para testes)
Write-Host "📝 Obtendo certificado SSL (modo STAGING para testes)..." -ForegroundColor Cyan
Write-Host ""

$certbotCmd = @(
    "run", "--rm",
    "certbot",
    "certonly",
    "--webroot",
    "--webroot-path=/var/www/certbot",
    "--staging",  # Modo staging (certificados de teste)
    "--email", $email,
    "--agree-tos",
    "--no-eff-email",
    "-d", $domain,
    "--rsa-key-size", "4096"
)

Write-Host "Executando: docker-compose $($certbotCmd -join ' ')" -ForegroundColor Gray
$result = docker-compose $certbotCmd 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Certificado obtido com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
    Write-Host "   1. Descomente os blocos HTTPS no nginx/nginx.conf" -ForegroundColor White
    Write-Host "   2. Recarregue o NGINX: docker-compose exec nginx nginx -s reload" -ForegroundColor White
    Write-Host "   3. Teste HTTPS: https://$domain" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Lembre-se: Certificado é de STAGING (teste) - navegador mostrará aviso" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Erro ao obter certificado" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Saída:" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Possíveis causas:" -ForegroundColor Yellow
    Write-Host "   1. Domínio não aponta para este servidor" -ForegroundColor White
    Write-Host "   2. Porta 80 não está acessível via ngrok" -ForegroundColor White
    Write-Host "   3. NGINX não está servindo /.well-known/acme-challenge/" -ForegroundColor White
}
