#!/bin/bash

# Script para configurar SSL automaticamente
# Uso: ./scripts/setup-ssl.sh

set -e

DOMAIN=${CERTBOT_DOMAIN:-}
EMAIL=${CERTBOT_EMAIL:-joao.paulo.bussi1@gmail.com}
STAGING=${CERTBOT_STAGING:-0}

if [ -z "$DOMAIN" ]; then
    echo "❌ ERRO: CERTBOT_DOMAIN não está definido!"
    echo "   Defina a variável CERTBOT_DOMAIN no arquivo .env ou exporte-a:"
    echo "   export CERTBOT_DOMAIN=seudominio.com"
    exit 1
fi

echo "🔐 Configurando SSL para: $DOMAIN"
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

if [ $? -eq 0 ]; then
    echo "✅ Certificado obtido com sucesso!"
    
    # Verificar qual domínio foi usado (pode ser diferente se houver www)
    ACTUAL_DOMAIN=$(docker-compose -f ./Lhama-Banana/docker-compose.yml exec -T certbot ls /etc/letsencrypt/live/ 2>/dev/null | head -1 | tr -d '\r\n' || echo "$DOMAIN")
    
    echo "📋 Domínio do certificado: $ACTUAL_DOMAIN"
    echo "🔧 Ativando HTTPS no Nginx..."
    
    # Aqui você precisaria editar o nginx.conf para descomentar o bloco HTTPS
    # e substituir SEU_DOMINIO pelo domínio real
    echo "⚠️  IMPORTANTE: Você precisa:"
    echo "   1. Editar nginx/nginx.conf"
    echo "   2. Descomentar o bloco server HTTPS (linhas 167-265)"
    echo "   3. Substituir \$host por $ACTUAL_DOMAIN nos caminhos dos certificados"
    echo "   4. Ou usar o template: nginx/nginx-ssl.conf.template"
    echo ""
    echo "   Exemplo de substituição:"
    echo "   ssl_certificate /etc/letsencrypt/live/$ACTUAL_DOMAIN/fullchain.pem;"
    echo "   ssl_certificate_key /etc/letsencrypt/live/$ACTUAL_DOMAIN/privkey.pem;"
    echo ""
    echo "🔄 Recarregando Nginx..."
    docker-compose -f ./Lhama-Banana/docker-compose.yml exec nginx nginx -s reload
    
    echo "🎉 Certificado SSL configurado! Acesse: https://$DOMAIN"
else
    echo "❌ Erro ao obter certificado. Verifique os logs:"
    echo "   docker-compose -f ./Lhama-Banana/docker-compose.yml logs certbot"
    exit 1
fi
