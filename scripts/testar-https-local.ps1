# Script simplificado para testar HTTPS localmente
# Cria certificados auto-assinados para desenvolvimento local

param(
    [string]$Domain = "localhost"
)

Write-Host "🔐 Configurando HTTPS Local - LhamaBanana" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker encontrado" -ForegroundColor Green
Write-Host ""

# Navegar para o diretório do projeto
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
Set-Location $projectDir

Write-Host "📁 Diretório: $projectDir" -ForegroundColor Cyan
Write-Host ""

# Verificar se NGINX está rodando
Write-Host "🔍 Verificando containers..." -ForegroundColor Yellow
$nginxStatus = docker-compose ps nginx 2>&1

if ($nginxStatus -notmatch "Up") {
    Write-Host "⚠️  NGINX não está rodando. Iniciando..." -ForegroundColor Yellow
    docker-compose up -d nginx postgres
    Write-Host "⏳ Aguardando containers iniciarem..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

Write-Host "✅ Containers verificados" -ForegroundColor Green
Write-Host ""

# Verificar configuração NGINX
Write-Host "📋 Testando configuração NGINX..." -ForegroundColor Cyan
$nginxTest = docker-compose exec nginx nginx -t 2>&1 | Out-String

if ($nginxTest -match "successful") {
    Write-Host "✅ Configuração NGINX OK" -ForegroundColor Green
} else {
    Write-Host "❌ Erro na configuração NGINX:" -ForegroundColor Red
    Write-Host $nginxTest -ForegroundColor Gray
    exit 1
}

Write-Host ""

# Verificar se certificados já existem
Write-Host "🔍 Verificando certificados SSL..." -ForegroundColor Cyan
$certExists = docker-compose exec -T certbot test -d "/etc/letsencrypt/live" 2>&1

if ($LASTEXITCODE -eq 0) {
    $certs = docker-compose exec -T certbot ls "/etc/letsencrypt/live" 2>&1 | Where-Object { $_ -notmatch "total|^$" }
    if ($certs) {
        Write-Host "✅ Certificados encontrados:" -ForegroundColor Green
        $certs | ForEach-Object { Write-Host "   - $_" -ForegroundColor Cyan }
    } else {
        Write-Host "⚠️  Nenhum certificado encontrado" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Para obter certificados SSL:" -ForegroundColor Yellow
        Write-Host "   1. Configure CERTBOT_EMAIL e CERTBOT_DOMAIN no .env" -ForegroundColor White
        Write-Host "   2. Use ngrok para expor o servidor: ngrok http 80" -ForegroundColor White
        Write-Host "   3. Execute: docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --staging --email seu-email@exemplo.com -d seu-dominio.ngrok-free.dev" -ForegroundColor White
    }
} else {
    Write-Host "⚠️  Volume de certificados não encontrado" -ForegroundColor Yellow
}

Write-Host ""

# Testar HTTP
Write-Host "🔍 Testando HTTP (porta 80)..." -ForegroundColor Cyan
try {
    $httpTest = Invoke-WebRequest -Uri "http://localhost" -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ HTTP funcionando (Status: $($httpTest.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "⚠️  HTTP não acessível: $_" -ForegroundColor Yellow
}

Write-Host ""

# Testar HTTPS (se certificados existirem)
Write-Host "🔍 Testando HTTPS (porta 443)..." -ForegroundColor Cyan
try {
    $httpsTest = Invoke-WebRequest -Uri "https://localhost" -Method Head -SkipCertificateCheck -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ HTTPS funcionando (Status: $($httpsTest.StatusCode))" -ForegroundColor Green
    Write-Host "   ⚠️  Certificado pode ser auto-assinado ou staging" -ForegroundColor Yellow
} catch {
    Write-Host "⚠️  HTTPS não acessível: $_" -ForegroundColor Yellow
    Write-Host "   Isso é normal se não houver certificados configurados" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Para obter certificados reais, use ngrok e execute o script completo" -ForegroundColor White
Write-Host "   2. Ver logs: docker-compose logs nginx" -ForegroundColor White
Write-Host "   3. Testar manualmente: http://localhost e https://localhost" -ForegroundColor White
Write-Host ""
