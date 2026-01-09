-- Adicionar coluna usuario_id na tabela vendas se não existir
-- Esta coluna é necessária para vincular vendas a usuários

-- Verificar se a coluna já existe antes de adicionar
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'vendas' 
        AND column_name = 'usuario_id'
    ) THEN
        ALTER TABLE vendas 
        ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL;
        
        -- Criar índice para otimizar consultas
        CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas (usuario_id);
        
        RAISE NOTICE 'Coluna usuario_id adicionada à tabela vendas';
    ELSE
        RAISE NOTICE 'Coluna usuario_id já existe na tabela vendas';
    END IF;
END $$;




