#!/bin/bash
# Script de inicialização do banco de dados
# Cria schema e dados iniciais antes de iniciar os serviços

set -e

echo "🗄️  Inicializando banco de dados..."

# Aguardar PostgreSQL estar pronto
echo "⏳ Aguardando PostgreSQL estar pronto..."
until docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "   PostgreSQL ainda não está pronto. Aguardando..."
    sleep 2
done
echo "✅ PostgreSQL está pronto!"

# Verificar se o banco já foi inicializado
DB_EXISTS=$(docker compose exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME:-sistema_usuarios}'" | tr -d ' ')

if [ "$DB_EXISTS" = "1" ]; then
    echo "📋 Banco de dados já existe. Verificando schema..."
    
    # Verificar se as tabelas principais existem
    TABLES_COUNT=$(docker compose exec -T postgres psql -U postgres -d "${DB_NAME:-sistema_usuarios}" -tc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'" | tr -d ' ')
    
    if [ "$TABLES_COUNT" -gt "0" ]; then
        echo "✅ Schema já existe (${TABLES_COUNT} tabelas encontradas). Pulando inicialização."
        exit 0
    fi
fi

# Criar banco de dados se não existir
echo "📦 Criando banco de dados se não existir..."
docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE ${DB_NAME:-sistema_usuarios};" 2>/dev/null || echo "   Banco já existe."

# Restaurar schema do backup ou criar do zero
if [ -f "backup_completo.sql" ]; then
    echo "📥 Restaurando schema do backup_completo.sql..."
    docker compose exec -T postgres psql -U postgres -d "${DB_NAME:-sistema_usuarios}" < backup_completo.sql
    echo "✅ Schema restaurado do backup!"
else
    echo "📝 Criando schema do zero..."
    
    # Executar scripts SQL na ordem
    if [ -f "db/schema.sql" ]; then
        echo "   Executando db/schema.sql..."
        docker compose exec -T postgres psql -U postgres -d "${DB_NAME:-sistema_usuarios}" < db/schema.sql
    fi
    
    # Executar scripts de migração na ordem
    if [ -d "sql" ]; then
        echo "   Executando scripts SQL em sql/..."
        for sql_file in sql/*.sql; do
            if [ -f "$sql_file" ]; then
                echo "     Executando $(basename $sql_file)..."
                docker compose exec -T postgres psql -U postgres -d "${DB_NAME:-sistema_usuarios}" < "$sql_file"
            fi
        done
    fi
    
    echo "✅ Schema criado do zero!"
fi

echo "🎉 Inicialização do banco de dados concluída!"
