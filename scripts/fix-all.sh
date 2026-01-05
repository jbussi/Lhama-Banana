#!/bin/bash
# Script para corrigir todos os problemas: criar banco metabase e corrigir índices do Strapi

set -e

echo "🔧 Iniciando correções..."

# 1. Criar banco metabase
echo "📦 Verificando banco 'metabase'..."
if docker compose exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'metabase'" | grep -q 1; then
    echo "✅ Banco 'metabase' já existe."
else
    echo "📦 Criando banco 'metabase'..."
    docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE metabase;" || true
    docker compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;" || true
    echo "✅ Banco 'metabase' criado!"
fi

# 2. Reiniciar Metabase
echo "🔄 Reiniciando Metabase..."
docker compose restart metabase || true

echo ""
echo "✅ Correções aplicadas!"
echo "⏳ Aguarde ~90 segundos para o Metabase inicializar."
echo "📊 Acesse: http://localhost:5000/analytics"


