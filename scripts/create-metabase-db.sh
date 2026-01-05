#!/bin/bash
# Script para criar o banco de dados do Metabase
# Execute este script quando o PostgreSQL estiver rodando

set -e

echo "Verificando se o banco 'metabase' existe..."

# Verificar se o banco existe
if docker compose exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'metabase'" | grep -q 1; then
    echo "✅ Banco de dados 'metabase' já existe."
else
    echo "📦 Criando banco de dados 'metabase'..."
    docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE metabase;"
    docker compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;"
    echo "✅ Banco de dados 'metabase' criado com sucesso!"
fi

echo "🔄 Reiniciando Metabase..."
docker compose restart metabase

echo "✅ Concluído! Aguarde alguns segundos para o Metabase inicializar."


