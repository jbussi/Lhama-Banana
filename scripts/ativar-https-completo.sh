#!/bin/bash

# Script completo para ativar HTTPS
# 1. Obtém certificados SSL
# 2. Verifica se NGINX está configurado corretamente
# 3. Recarrega NGINX

set -e

echo "🔐 Ativando HTTPS - LhamaBanana"
echo "================================"
echo ""

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

# Passo 1: Obter certificados SSL
echo "📝 Passo 1: Obtendo certificados SSL..."
bash ./scripts/obter-certificados-ssl.sh

if [ $? -ne 0 ]; then
    echo "❌ Erro ao obter certificados SSL"
    exit 1
fi

# Passo 2: Verificar se certificados existem
echo ""
echo "📋 Passo 2: Verificando certificados..."
CERT_PATH="/etc/letsencrypt/live/$CERTBOT_DOMAIN"
if docker-compose exec -T certbot test -f "$CERT_PATH/fullchain.pem" 2>/dev/null; then
    echo "✅ Certificado encontrado: $CERT_PATH/fullchain.pem"
else
    echo "❌ Certificado não encontrado em $CERT_PATH"
    exit 1
fi

# Passo 3: Verificar configuração do NGINX
echo ""
echo "📋 Passo 3: Verificando configuração do NGINX..."
if docker-compose exec nginx nginx -t; then
    echo "✅ Configuração do NGINX está correta"
else
    echo "❌ Erro na configuração do NGINX"
    exit 1
fi

# Passo 4: Recarregar NGINX
echo ""
echo "🔄 Passo 4: Recarregando NGINX..."
docker-compose exec nginx nginx -s reload

if [ $? -eq 0 ]; then
    echo "✅ NGINX recarregado com sucesso"
else
    echo "❌ Erro ao recarregar NGINX"
    exit 1
fi

# Passo 5: Verificar HTTPS
echo ""
echo "🔍 Passo 5: Verificando HTTPS..."
sleep 2

# Testar HTTPS do site principal
if curl -s -o /dev/null -w "%{http_code}" https://$CERTBOT_DOMAIN | grep -q "200\|301\|302"; then
    echo "✅ HTTPS funcionando para $CERTBOT_DOMAIN"
else
    echo "⚠️  HTTPS pode não estar funcionando para $CERTBOT_DOMAIN"
    echo "   Verifique manualmente: curl -I https://$CERTBOT_DOMAIN"
fi

echo ""
echo "🎉 HTTPS ativado com sucesso!"
echo ""
echo "📝 Próximos passos:"
echo "   1. Teste manualmente: https://$CERTBOT_DOMAIN"
echo "   2. Verifique redirecionamento HTTP → HTTPS"
echo "   3. Verifique certificado no navegador"
echo ""
echo "   Para ver logs do NGINX:"
echo "   docker-compose logs nginx"
echo ""
echo "   Para ver logs do Certbot:"
echo "   docker-compose logs certbot"
