#!/bin/bash
# Script de inicialização para criar banco do Metabase
# Executado automaticamente pelo PostgreSQL na primeira inicialização

set -e

# Verificar se o banco já existe
if psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tc "SELECT 1 FROM pg_database WHERE datname = 'metabase'" | grep -q 1; then
    echo "Banco de dados 'metabase' já existe."
else
    echo "Criando banco de dados 'metabase'..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE DATABASE metabase;"
    echo "Banco de dados 'metabase' criado com sucesso."
fi

# Conceder permissões
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "metabase" -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO $POSTGRES_USER;" || true

