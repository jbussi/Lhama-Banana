-- Script para remover campos não utilizados
-- ==========================================
-- Remove: preco_promocional, estoque_reservado, tags
-- ==========================================

-- Remover preco_promocional da tabela produtos
ALTER TABLE produtos DROP COLUMN IF EXISTS preco_promocional;

-- Remover estoque_reservado da tabela produtos
ALTER TABLE produtos DROP COLUMN IF EXISTS estoque_reservado;

-- Remover tags da tabela nome_produto
ALTER TABLE nome_produto DROP COLUMN IF EXISTS tags;

-- Verificar se as colunas foram removidas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('produtos', 'nome_produto')
  AND column_name IN ('preco_promocional', 'estoque_reservado', 'tags')
ORDER BY table_name, column_name;
