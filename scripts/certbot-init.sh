#!/bin/bash

# Script para inicializar certificados SSL com Certbot
# Uso: ./scripts/certbot-init.sh

set -e

# Variáveis de ambiente (podem ser definidas no .env)
DOMAIN=${CERTBOT_DOMAIN:-}
EMAIL=${CERTBOT_EMAIL:-joao.paulo.bussi1@gmail.com}
STAGING=${CERTBOT_STAGING:-0}

if [ -z "$DOMAIN" ]; then
    echo "❌ ERRO: CERTBOT_DOMAIN não está definido!"
    echo "   Defina a variável CERTBOT_DOMAIN no arquivo .env ou exporte-a:"
    echo "   export CERTBOT_DOMAIN=seudominio.com"
    exit 1
fi

echo "🔐 Inicializando certificado SSL para: $DOMAIN"
echo "📧 Email: $EMAIL"

# Verificar se o Nginx está rodando
if ! docker ps | grep -q lhama_banana_nginx; then
    echo "⚠️ Nginx não está rodando. Iniciando..."
    docker-compose -f ./Lhama-Banana/docker-compose.yml up -d nginx
    sleep 5
fi

# Preparar argumentos
STAGING_ARG=""
if [ "$STAGING" = "1" ]; then
    STAGING_ARG="--staging"
    echo "🧪 Modo staging ativado (teste)"
fi

# Obter certificado
echo "📝 Solicitando certificado do Let's Encrypt..."
docker-compose -f ./Lhama-Banana/docker-compose.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    $STAGING_ARG \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    --rsa-key-size 4096

echo "✅ Certificado obtido com sucesso!"
echo "🔄 Recarregando Nginx..."
docker-compose -f ./Lhama-Banana/docker-compose.yml exec nginx nginx -s reload

echo "🎉 Certificado SSL configurado! Acesse: https://$DOMAIN"
