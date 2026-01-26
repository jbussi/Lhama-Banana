#!/bin/bash

# Script para obter certificados SSL do Let's Encrypt
# Uso: ./scripts/obter-certificados-ssl.sh

set -e

# Carregar variáveis do .env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Verificar variáveis obrigatórias
if [ -z "$CERTBOT_EMAIL" ]; then
    echo "❌ ERRO: CERTBOT_EMAIL não está definido no .env"
    exit 1
fi

if [ -z "$CERTBOT_DOMAIN" ]; then
    echo "❌ ERRO: CERTBOT_DOMAIN não está definido no .env"
    exit 1
fi

DOMAIN="$CERTBOT_DOMAIN"
EMAIL="$CERTBOT_EMAIL"
STAGING="${CERTBOT_STAGING:-0}"

echo "🔐 Obtendo certificados SSL para: $DOMAIN"
echo "📧 Email: $EMAIL"

# Verificar se o Nginx está rodando
if ! docker-compose ps | grep -q "lhama_banana_nginx.*Up"; then
    echo "⚠️  Nginx não está rodando. Iniciando..."
    docker-compose up -d nginx
    sleep 5
fi

# Preparar argumentos
STAGING_ARG=""
if [ "$STAGING" = "1" ]; then
    STAGING_ARG="--staging"
    echo "🧪 Modo staging ativado (teste - certificados não são confiáveis)"
fi

# Obter certificado para domínio principal (inclui www)
echo ""
echo "📝 Solicitando certificado para $DOMAIN e www.$DOMAIN..."
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    $STAGING_ARG \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --rsa-key-size 4096

if [ $? -eq 0 ]; then
    echo "✅ Certificado obtido com sucesso para $DOMAIN e www.$DOMAIN!"
else
    echo "❌ Erro ao obter certificado para $DOMAIN"
    exit 1
fi

# Obter certificado para API (se usar subdomínio separado)
if [ -n "$CERTBOT_API_DOMAIN" ]; then
    echo ""
    echo "📝 Solicitando certificado para $CERTBOT_API_DOMAIN..."
    docker-compose run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        $STAGING_ARG \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$CERTBOT_API_DOMAIN" \
        --rsa-key-size 4096
    
    if [ $? -eq 0 ]; then
        echo "✅ Certificado obtido com sucesso para $CERTBOT_API_DOMAIN!"
    else
        echo "⚠️  Erro ao obter certificado para $CERTBOT_API_DOMAIN (continuando...)"
    fi
fi

# Obter certificado para Admin (se usar subdomínio separado)
if [ -n "$CERTBOT_ADMIN_DOMAIN" ]; then
    echo ""
    echo "📝 Solicitando certificado para $CERTBOT_ADMIN_DOMAIN..."
    docker-compose run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        $STAGING_ARG \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$CERTBOT_ADMIN_DOMAIN" \
        --rsa-key-size 4096
    
    if [ $? -eq 0 ]; then
        echo "✅ Certificado obtido com sucesso para $CERTBOT_ADMIN_DOMAIN!"
    else
        echo "⚠️  Erro ao obter certificado para $CERTBOT_ADMIN_DOMAIN (continuando...)"
    fi
fi

# Verificar certificados obtidos
echo ""
echo "📋 Verificando certificados obtidos..."
docker-compose exec certbot ls -la /etc/letsencrypt/live/ || true

echo ""
echo "✅ Certificados SSL obtidos com sucesso!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Descomentar blocos HTTPS no nginx/nginx.conf"
echo "   2. Adicionar redirecionamento HTTP → HTTPS"
echo "   3. Recarregar NGINX: docker-compose exec nginx nginx -s reload"
echo ""
echo "   Ou execute: ./scripts/ativar-https.sh"
