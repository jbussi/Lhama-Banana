#!/bin/bash

# =====================================================
# Script para limpar cache do Strapi
# =====================================================
# Este script limpa o cache do Strapi para remover
# registros órfãos que aparecem no admin mas não existem no banco
# =====================================================

echo "🧹 Limpando cache do Strapi..."

# Parar o Strapi
echo "⏸️  Parando o Strapi..."
docker compose stop strapi

# Limpar cache do Strapi
echo "🗑️  Removendo cache..."
docker compose exec strapi rm -rf .cache .tmp dist build 2>/dev/null || true

# Limpar cache do volume (se existir)
echo "🗑️  Limpando cache do volume..."
docker compose run --rm strapi rm -rf .cache .tmp dist build 2>/dev/null || true

# Reiniciar o Strapi
echo "▶️  Reiniciando o Strapi..."
docker compose up -d strapi

echo "✅ Cache limpo! O Strapi será reconstruído na próxima inicialização."
echo "⏳ Aguarde alguns minutos para o Strapi reconstruir o índice..."
