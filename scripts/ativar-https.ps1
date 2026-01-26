# Script PowerShell para ativar HTTPS no servidor
# Uso: .\scripts\ativar-https.ps1 -ServerIP "seu-ip" -Username "usuario" -ProjectPath "/opt/lhama-banana/Lhama-Banana"

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "/opt/lhama-banana/Lhama-Banana",
    
    [Parameter(Mandatory=$false)]
    [string]$SSHKey = ""
)

Write-Host "🔐 Ativando HTTPS - LhamaBanana" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se SSH está disponível
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ ERRO: SSH não está disponível!" -ForegroundColor Red
    Write-Host "   Instale OpenSSH ou use WSL/Git Bash" -ForegroundColor Yellow
    exit 1
}

# Construir comando SSH
$sshCommand = "ssh"
if ($SSHKey) {
    $sshCommand += " -i `"$SSHKey`""
}
$sshCommand += " ${Username}@${ServerIP}"

Write-Host "📡 Conectando ao servidor: ${Username}@${ServerIP}" -ForegroundColor Yellow
Write-Host ""

# Script a ser executado no servidor
$remoteScript = @"
set -e

echo "🔐 Ativando HTTPS - LhamaBanana"
echo "================================"
echo ""

# Navegar para o diretório do projeto
cd $ProjectPath

if [ ! -f "docker-compose.yml" ]; then
    echo "❌ ERRO: docker-compose.yml não encontrado em $ProjectPath"
    exit 1
fi

# Carregar variáveis do .env
if [ -f .env ]; then
    export \$(cat .env | grep -v '^#' | xargs)
    echo "✅ Arquivo .env carregado"
else
    echo "❌ ERRO: Arquivo .env não encontrado!"
    exit 1
fi

# Verificar variáveis obrigatórias
if [ -z "\$CERTBOT_EMAIL" ]; then
    echo "❌ ERRO: CERTBOT_EMAIL não está definido no .env"
    echo "   Adicione: CERTBOT_EMAIL=seu-email@exemplo.com"
    exit 1
fi

if [ -z "\$CERTBOT_DOMAIN" ]; then
    echo "❌ ERRO: CERTBOT_DOMAIN não está definido no .env"
    echo "   Adicione: CERTBOT_DOMAIN=lhamabanana.com"
    exit 1
fi

echo "📧 Email: \$CERTBOT_EMAIL"
echo "🌐 Domínio: \$CERTBOT_DOMAIN"
echo ""

# Verificar se NGINX está rodando
if ! docker-compose ps | grep -q "lhama_banana_nginx.*Up"; then
    echo "⚠️  NGINX não está rodando. Iniciando..."
    docker-compose up -d nginx
    echo "⏳ Aguardando NGINX iniciar..."
    sleep 5
fi

# Passo 1: Obter certificados SSL
echo "📝 Passo 1/4: Obtendo certificados SSL..."
echo ""

STAGING_ARG=""
if [ "\${CERTBOT_STAGING:-0}" = "1" ]; then
    STAGING_ARG="--staging"
    echo "🧪 Modo STAGING ativado (teste)"
fi

docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    \$STAGING_ARG \
    --email "\$CERTBOT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "\$CERTBOT_DOMAIN" \
    -d "www.\$CERTBOT_DOMAIN" \
    --rsa-key-size 4096

if [ \$? -ne 0 ]; then
    echo ""
    echo "❌ Erro ao obter certificado SSL"
    echo ""
    echo "💡 Possíveis causas:"
    echo "   1. Domínio não aponta para este servidor (verifique DNS)"
    echo "   2. Porta 80 bloqueada (verifique firewall)"
    echo "   3. NGINX não está acessível externamente"
    echo ""
    echo "   Verifique os logs:"
    echo "   docker-compose logs certbot"
    exit 1
fi

echo ""
echo "✅ Certificado obtido com sucesso!"
echo ""

# Passo 2: Verificar certificado
echo "📋 Passo 2/4: Verificando certificado..."
CERT_PATH="/etc/letsencrypt/live/\$CERTBOT_DOMAIN"
if docker-compose exec -T certbot test -f "\$CERT_PATH/fullchain.pem" 2>/dev/null; then
    echo "✅ Certificado encontrado: \$CERT_PATH/fullchain.pem"
else
    echo "❌ Certificado não encontrado em \$CERT_PATH"
    exit 1
fi
echo ""

# Passo 3: Verificar configuração NGINX
echo "📋 Passo 3/4: Verificando configuração do NGINX..."
if docker-compose exec nginx nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Configuração do NGINX está correta"
else
    echo "❌ Erro na configuração do NGINX"
    echo ""
    echo "   Verifique os erros acima e corrija o arquivo nginx/nginx.conf"
    docker-compose exec nginx nginx -t
    exit 1
fi
echo ""

# Passo 4: Recarregar NGINX
echo "🔄 Passo 4/4: Recarregando NGINX..."
if docker-compose exec nginx nginx -s reload; then
    echo "✅ NGINX recarregado com sucesso"
else
    echo "❌ Erro ao recarregar NGINX"
    exit 1
fi
echo ""

# Verificar HTTPS
echo "🔍 Verificando HTTPS..."
sleep 3

HTTP_CODE=\$(curl -s -o /dev/null -w "%{http_code}" https://\$CERTBOT_DOMAIN 2>/dev/null || echo "000")

if [ "\$HTTP_CODE" = "200" ] || [ "\$HTTP_CODE" = "301" ] || [ "\$HTTP_CODE" = "302" ]; then
    echo "✅ HTTPS funcionando! (HTTP \$HTTP_CODE)"
else
    echo "⚠️  HTTPS pode não estar funcionando (HTTP \$HTTP_CODE)"
    echo "   Verifique manualmente: curl -I https://\$CERTBOT_DOMAIN"
fi

echo ""
echo "🎉 HTTPS ativado com sucesso!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Teste no navegador: https://\$CERTBOT_DOMAIN"
echo "   2. Verifique o certificado (cadeado verde)"
echo "   3. Teste redirecionamento: http://\$CERTBOT_DOMAIN (deve redirecionar para HTTPS)"
echo ""
echo "📊 Comandos úteis:"
echo "   - Ver logs NGINX: docker-compose logs nginx"
echo "   - Ver logs Certbot: docker-compose logs certbot"
echo "   - Testar HTTPS: curl -I https://\$CERTBOT_DOMAIN"
echo ""
"@

# Executar script no servidor
try {
    $remoteScript | & $sshCommand.Split(' ') | ForEach-Object {
        Write-Host $_
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Erro ao executar script no servidor (código: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ Processo concluído!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ Erro ao conectar ao servidor: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Dicas:" -ForegroundColor Yellow
    Write-Host "   1. Verifique se o servidor está acessível: ping $ServerIP" -ForegroundColor Yellow
    Write-Host "   2. Verifique suas credenciais SSH" -ForegroundColor Yellow
    Write-Host "   3. Se usar chave SSH, especifique: -SSHKey `"caminho/para/chave`"" -ForegroundColor Yellow
    exit 1
}
