-- =====================================================
-- Script de Migração: Tabela Tecidos e Campo NCM
-- =====================================================
-- Este script:
-- 1. Cria a tabela tecidos
-- 2. Migra dados do campo VARCHAR tecido (se existir) para a nova tabela
-- 3. Adiciona tecido_id na tabela estampa
-- 4. Remove o campo VARCHAR tecido da tabela estampa
-- 5. Adiciona campo ncm na tabela produtos
-- =====================================================

-- Criar tabela tecidos
CREATE TABLE IF NOT EXISTS tecidos (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) UNIQUE NOT NULL,
  descricao TEXT,
  ativo BOOLEAN DEFAULT TRUE,
  ordem_exibicao INTEGER DEFAULT 0,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por INTEGER,
  atualizado_por INTEGER
);

-- Criar índices para tecidos
CREATE INDEX IF NOT EXISTS idx_tecidos_ativo ON tecidos (ativo);
CREATE INDEX IF NOT EXISTS idx_tecidos_nome ON tecidos (nome);

-- Migrar dados do campo VARCHAR tecido (se existir) para a nova tabela
-- Primeiro, inserir valores únicos do campo tecido na tabela tecidos
DO $$
DECLARE
    tecido_nome VARCHAR(100);
    tecido_id INTEGER;
BEGIN
    -- Verificar se a coluna tecido existe
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'estampa' 
        AND column_name = 'tecido'
    ) THEN
        -- Inserir valores únicos do campo tecido na tabela tecidos
        FOR tecido_nome IN 
            SELECT DISTINCT tecido 
            FROM estampa 
            WHERE tecido IS NOT NULL AND tecido != ''
        LOOP
            INSERT INTO tecidos (nome, ativo)
            VALUES (tecido_nome, TRUE)
            ON CONFLICT (nome) DO NOTHING;
        END LOOP;
        
        -- Adicionar coluna tecido_id na tabela estampa
        ALTER TABLE estampa 
        ADD COLUMN IF NOT EXISTS tecido_id INTEGER REFERENCES tecidos(id);
        
        -- Atualizar tecido_id baseado no campo tecido
        UPDATE estampa e
        SET tecido_id = t.id
        FROM tecidos t
        WHERE e.tecido = t.nome
        AND e.tecido IS NOT NULL
        AND e.tecido != '';
        
        -- Criar índice para tecido_id
        CREATE INDEX IF NOT EXISTS idx_estampa_tecido_id ON estampa(tecido_id);
        
        -- Remover o campo VARCHAR tecido
        ALTER TABLE estampa DROP COLUMN IF EXISTS tecido;
        
        -- Remover índice antigo se existir
        DROP INDEX IF EXISTS idx_estampa_tecido;
    ELSE
        -- Se a coluna tecido não existe, apenas adicionar tecido_id
        ALTER TABLE estampa 
        ADD COLUMN IF NOT EXISTS tecido_id INTEGER REFERENCES tecidos(id);
        
        CREATE INDEX IF NOT EXISTS idx_estampa_tecido_id ON estampa(tecido_id);
    END IF;
END $$;

-- Adicionar campo ncm na tabela produtos
ALTER TABLE produtos 
ADD COLUMN IF NOT EXISTS ncm VARCHAR(8);

-- Criar trigger para atualizar timestamp em tecidos
DROP TRIGGER IF EXISTS trg_tecidos_update_timestamp ON tecidos;
CREATE TRIGGER trg_tecidos_update_timestamp 
    BEFORE UPDATE ON tecidos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_timestamp();

-- Comentários para documentação
COMMENT ON TABLE tecidos IS 'Tipos de tecidos disponíveis para estampas';
COMMENT ON COLUMN estampa.tecido_id IS 'Referência ao tipo de tecido da estampa';
COMMENT ON COLUMN produtos.ncm IS 'NCM (Nomenclatura Comum do Mercosul) - 8 dígitos para emissão de nota fiscal';


