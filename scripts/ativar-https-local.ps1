# Script PowerShell para ativar HTTPS localmente
# Usa ngrok para expor o servidor e obtém certificados staging do Let's Encrypt

Write-Host "🔐 Ativando HTTPS Localmente - LhamaBanana" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Docker está rodando
Write-Host "🔍 Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker não encontrado"
    }
    Write-Host "✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERRO: Docker não está instalado ou não está rodando!" -ForegroundColor Red
    Write-Host "   Instale Docker Desktop e tente novamente" -ForegroundColor Yellow
    exit 1
}

# Verificar se docker-compose está disponível
Write-Host "🔍 Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose não encontrado"
    }
    Write-Host "✅ Docker Compose encontrado: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERRO: Docker Compose não está disponível!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Navegar para o diretório do projeto
# O script está em scripts/, então o projeto está um nível acima
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath
Set-Location $projectPath

Write-Host "📁 Diretório do projeto: $projectPath" -ForegroundColor Cyan
Write-Host ""

# Verificar se .env existe
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Arquivo .env não encontrado!" -ForegroundColor Yellow
    Write-Host "   Criando .env a partir de env.example..." -ForegroundColor Yellow
    
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "✅ Arquivo .env criado. Configure as variáveis necessárias." -ForegroundColor Green
    } else {
        Write-Host "❌ ERRO: env.example não encontrado!" -ForegroundColor Red
        exit 1
    }
}

# Carregar variáveis do .env
Write-Host "📋 Carregando variáveis do .env..." -ForegroundColor Yellow
$envVars = @{}
Get-Content ".env" | Where-Object { $_ -match '^\s*([^#][^=]+)=(.*)$' } | ForEach-Object {
    $key = $matches[1].Trim()
    $value = $matches[2].Trim()
    $envVars[$key] = $value
}

# Verificar variáveis obrigatórias
$requiredVars = @("CERTBOT_EMAIL", "CERTBOT_DOMAIN")
$missingVars = @()

foreach ($var in $requiredVars) {
    if (-not $envVars.ContainsKey($var) -or [string]::IsNullOrWhiteSpace($envVars[$var])) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "❌ ERRO: Variáveis obrigatórias não encontradas no .env:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "   - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "💡 Adicione ao arquivo .env:" -ForegroundColor Yellow
    Write-Host "   CERTBOT_EMAIL=seu-email@exemplo.com" -ForegroundColor Yellow
    Write-Host "   CERTBOT_DOMAIN=seu-dominio-ngrok.ngrok-free.dev" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Para obter um domínio ngrok:" -ForegroundColor Yellow
    Write-Host "   1. Instale ngrok: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "   2. Execute: ngrok http 80" -ForegroundColor Yellow
    Write-Host "   3. Use a URL HTTPS gerada (ex: https://abc123.ngrok-free.dev)" -ForegroundColor Yellow
    exit 1
}

$certbotEmail = $envVars["CERTBOT_EMAIL"]
$certbotDomain = $envVars["CERTBOT_DOMAIN"]

Write-Host "✅ Variáveis carregadas:" -ForegroundColor Green
Write-Host "   Email: $certbotEmail" -ForegroundColor Cyan
Write-Host "   Domínio: $certbotDomain" -ForegroundColor Cyan
Write-Host ""

# Verificar se containers estão rodando
Write-Host "🔍 Verificando containers Docker..." -ForegroundColor Yellow
$containers = docker-compose ps --format json | ConvertFrom-Json

$nginxRunning = $false
$certbotRunning = $false

foreach ($container in $containers) {
    if ($container.Name -like "*nginx*" -and $container.State -eq "running") {
        $nginxRunning = $true
    }
    if ($container.Name -like "*certbot*" -and $container.State -eq "running") {
        $certbotRunning = $true
    }
}

if (-not $nginxRunning) {
    Write-Host "⚠️  NGINX não está rodando. Iniciando..." -ForegroundColor Yellow
    docker-compose up -d nginx
    Start-Sleep -Seconds 5
    Write-Host "✅ NGINX iniciado" -ForegroundColor Green
} else {
    Write-Host "✅ NGINX está rodando" -ForegroundColor Green
}

Write-Host ""

# Passo 1: Obter certificados SSL (staging para testes)
Write-Host "📝 Passo 1/4: Obtendo certificados SSL (modo STAGING para testes)..." -ForegroundColor Cyan
Write-Host ""

$stagingMode = $true  # Sempre usar staging para testes locais

$certbotArgs = @(
    "run", "--rm",
    "certbot",
    "certonly",
    "--webroot",
    "--webroot-path=/var/www/certbot",
    "--staging",  # Modo staging (certificados de teste)
    "--email", $certbotEmail,
    "--agree-tos",
    "--no-eff-email",
    "-d", $certbotDomain,
    "--rsa-key-size", "4096"
)

Write-Host "Executando: docker-compose $($certbotArgs -join ' ')" -ForegroundColor Gray
$certbotResult = docker-compose $certbotArgs 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Erro ao obter certificado SSL" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Possíveis causas:" -ForegroundColor Yellow
    Write-Host "   1. Domínio ngrok não está acessível publicamente" -ForegroundColor Yellow
    Write-Host "   2. Porta 80 não está exposta via ngrok" -ForegroundColor Yellow
    Write-Host "   3. NGINX não está configurado para servir /.well-known/acme-challenge/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 Saída do comando:" -ForegroundColor Yellow
    Write-Host $certbotResult -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "✅ Certificado obtido com sucesso!" -ForegroundColor Green
Write-Host ""

# Passo 2: Verificar certificado
Write-Host "📋 Passo 2/4: Verificando certificado..." -ForegroundColor Cyan
$certPath = "/etc/letsencrypt/live/$certbotDomain"

$checkCert = docker-compose exec -T certbot test -f "$certPath/fullchain.pem" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Certificado encontrado: $certPath/fullchain.pem" -ForegroundColor Green
} else {
    Write-Host "❌ Certificado não encontrado em $certPath" -ForegroundColor Red
    Write-Host "   Verifique os logs: docker-compose logs certbot" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Passo 3: Verificar configuração NGINX
Write-Host "📋 Passo 3/4: Verificando configuração do NGINX..." -ForegroundColor Cyan
$nginxTest = docker-compose exec nginx nginx -t 2>&1

if ($nginxTest -match "successful") {
    Write-Host "✅ Configuração do NGINX está correta" -ForegroundColor Green
} else {
    Write-Host "❌ Erro na configuração do NGINX" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Saída:" -ForegroundColor Yellow
    Write-Host $nginxTest -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Verifique o arquivo nginx/nginx.conf" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Passo 4: Recarregar NGINX
Write-Host "🔄 Passo 4/4: Recarregando NGINX..." -ForegroundColor Cyan
$reloadResult = docker-compose exec nginx nginx -s reload 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ NGINX recarregado com sucesso" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao recarregar NGINX" -ForegroundColor Red
    Write-Host $reloadResult -ForegroundColor Gray
    exit 1
}

Write-Host ""

# Verificar HTTPS
Write-Host "🔍 Verificando HTTPS..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "https://$certbotDomain" -Method Head -SkipCertificateCheck -ErrorAction SilentlyContinue
    $httpCode = $response.StatusCode
    
    if ($httpCode -eq 200 -or $httpCode -eq 301 -or $httpCode -eq 302) {
        Write-Host "✅ HTTPS funcionando! (HTTP $httpCode)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  HTTPS retornou código HTTP $httpCode" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Não foi possível verificar HTTPS automaticamente" -ForegroundColor Yellow
    Write-Host "   Teste manualmente: https://$certbotDomain" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 HTTPS ativado localmente com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Teste no navegador: https://$certbotDomain" -ForegroundColor White
Write-Host "   2. ⚠️  Certificado é de STAGING (teste) - navegador mostrará aviso" -ForegroundColor Yellow
Write-Host "   3. Para produção, remova --staging e use domínio real" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 Comandos úteis:" -ForegroundColor Cyan
Write-Host "   - Ver logs NGINX: docker-compose logs nginx" -ForegroundColor White
Write-Host "   - Ver logs Certbot: docker-compose logs certbot" -ForegroundColor White
Write-Host "   - Testar HTTPS: Invoke-WebRequest -Uri https://$certbotDomain -SkipCertificateCheck" -ForegroundColor White
Write-Host ""
