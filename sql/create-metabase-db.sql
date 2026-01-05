-- =====================================================
-- CRIAÇÃO DO BANCO DE DADOS DO METABASE
-- =====================================================
-- Execute este script para criar o banco de dados "metabase"
-- usado pelo Metabase para armazenar configurações internas.
-- =====================================================

-- Criar banco de dados do Metabase se não existir
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase') THEN
        CREATE DATABASE metabase;
        RAISE NOTICE 'Banco de dados "metabase" criado com sucesso.';
    ELSE
        RAISE NOTICE 'Banco de dados "metabase" já existe.';
    END IF;
END
$$;

-- Conceder permissões ao usuário postgres
GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;

-- Comentário
COMMENT ON DATABASE metabase IS 'Banco de dados interno do Metabase para armazenar configurações, dashboards e queries';


