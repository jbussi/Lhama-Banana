-- =====================================================
-- MIGRAÇÃO: Ajustes para Strapi Admin
-- =====================================================
-- Este script aplica as alterações necessárias no banco de dados
-- para alinhar com os modelos simplificados do Strapi
-- =====================================================

-- 1. Remover colunas desnecessárias da tabela estampa
DO $$
BEGIN
    -- Remover custo_por_metro se existir
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'estampa' AND column_name = 'custo_por_metro'
    ) THEN
        ALTER TABLE estampa DROP COLUMN custo_por_metro;
        RAISE NOTICE 'Coluna custo_por_metro removida da tabela estampa';
    END IF;
    
    -- Remover criado_por se existir
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'estampa' AND column_name = 'criado_por'
    ) THEN
        ALTER TABLE estampa DROP COLUMN criado_por;
        RAISE NOTICE 'Coluna criado_por removida da tabela estampa';
    END IF;
    
    -- Remover atualizado_por se existir
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'estampa' AND column_name = 'atualizado_por'
    ) THEN
        ALTER TABLE estampa DROP COLUMN atualizado_por;
        RAISE NOTICE 'Coluna atualizado_por removida da tabela estampa';
    END IF;
END $$;

-- 2. Adicionar coluna tipo na tabela categorias (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'categorias' AND column_name = 'tipo'
    ) THEN
        ALTER TABLE categorias 
        ADD COLUMN tipo VARCHAR(20) DEFAULT 'produto' 
        CHECK (tipo IN ('produto', 'estampa'));
        
        -- Atualizar categorias existentes para 'produto' por padrão
        UPDATE categorias SET tipo = 'produto' WHERE tipo IS NULL;
        
        RAISE NOTICE 'Coluna tipo adicionada à tabela categorias';
    ELSE
        RAISE NOTICE 'Coluna tipo já existe na tabela categorias';
    END IF;
END $$;

-- 3. Remover colunas criado_por e atualizado_por da tabela categorias (se existirem)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'categorias' AND column_name = 'criado_por'
    ) THEN
        ALTER TABLE categorias DROP COLUMN criado_por;
        RAISE NOTICE 'Coluna criado_por removida da tabela categorias';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'categorias' AND column_name = 'atualizado_por'
    ) THEN
        ALTER TABLE categorias DROP COLUMN atualizado_por;
        RAISE NOTICE 'Coluna atualizado_por removida da tabela categorias';
    END IF;
END $$;

-- 4. Remover colunas criado_por e atualizado_por da tabela nome_produto (se existirem)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'nome_produto' AND column_name = 'criado_por'
    ) THEN
        ALTER TABLE nome_produto DROP COLUMN criado_por;
        RAISE NOTICE 'Coluna criado_por removida da tabela nome_produto';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'nome_produto' AND column_name = 'atualizado_por'
    ) THEN
        ALTER TABLE nome_produto DROP COLUMN atualizado_por;
        RAISE NOTICE 'Coluna atualizado_por removida da tabela nome_produto';
    END IF;
END $$;

-- 5. Remover colunas criado_por e atualizado_por da tabela tecidos (se existirem)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tecidos' AND column_name = 'criado_por'
    ) THEN
        ALTER TABLE tecidos DROP COLUMN criado_por;
        RAISE NOTICE 'Coluna criado_por removida da tabela tecidos';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tecidos' AND column_name = 'atualizado_por'
    ) THEN
        ALTER TABLE tecidos DROP COLUMN atualizado_por;
        RAISE NOTICE 'Coluna atualizado_por removida da tabela tecidos';
    END IF;
END $$;

RAISE NOTICE 'Migração concluída com sucesso!';
