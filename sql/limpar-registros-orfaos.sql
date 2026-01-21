-- =====================================================
-- LIMPEZA DE REGISTROS ÓRFÃOS DO STRAPI
-- =====================================================
-- Este script remove registros órfãos que aparecem no admin do Strapi
-- mas não existem mais no banco de dados (categorias 31, 32 e nome_produto 9)
-- 
-- IMPORTANTE: Execute este script apenas se você tem certeza de que
-- esses registros não devem existir mais.
-- =====================================================

-- 1. Verificar se os registros existem no banco
SELECT 'Verificando categorias 31 e 32...' AS status;
SELECT id, nome FROM categorias WHERE id IN (31, 32);

SELECT 'Verificando nome_produto 9...' AS status;
SELECT id, nome FROM nome_produto WHERE id = 9;

-- 2. Limpar referências das categorias 31 e 32 (se existirem)
DO $$
BEGIN
    -- Limpar referências de categoria 31
    IF EXISTS (SELECT 1 FROM categorias WHERE id = 31) THEN
        DELETE FROM estampa_categoria_lnk WHERE categoria_id = 31;
        DELETE FROM nome_produto_categoria_lnk WHERE categoria_id = 31;
        UPDATE estampa SET categoria_id = NULL WHERE categoria_id = 31;
        UPDATE nome_produto SET categoria_id = NULL WHERE categoria_id = 31;
        RAISE NOTICE 'Referências da categoria 31 limpas';
    ELSE
        RAISE NOTICE 'Categoria 31 não existe no banco (já foi deletada)';
    END IF;
    
    -- Limpar referências de categoria 32
    IF EXISTS (SELECT 1 FROM categorias WHERE id = 32) THEN
        DELETE FROM estampa_categoria_lnk WHERE categoria_id = 32;
        DELETE FROM nome_produto_categoria_lnk WHERE categoria_id = 32;
        UPDATE estampa SET categoria_id = NULL WHERE categoria_id = 32;
        UPDATE nome_produto SET categoria_id = NULL WHERE categoria_id = 32;
        RAISE NOTICE 'Referências da categoria 32 limpas';
    ELSE
        RAISE NOTICE 'Categoria 32 não existe no banco (já foi deletada)';
    END IF;
END $$;

-- 3. Limpar referências do nome_produto 9 (se existir)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM nome_produto WHERE id = 9) THEN
        DELETE FROM nome_produto_categoria_lnk WHERE nome_produto_id = 9;
        DELETE FROM produtos_nome_produto_lnk WHERE nome_produto_id = 9;
        UPDATE produtos SET nome_produto_id = NULL WHERE nome_produto_id = 9;
        RAISE NOTICE 'Referências do nome_produto 9 limpas';
    ELSE
        RAISE NOTICE 'Nome produto 9 não existe no banco (já foi deletado)';
    END IF;
END $$;

-- 4. Deletar os registros se ainda existirem
DELETE FROM categorias WHERE id IN (31, 32);
DELETE FROM nome_produto WHERE id = 9;

-- 5. Limpar registros órfãos das tabelas internas do Strapi
-- O Strapi 5 usa uma tabela para mapear documentIds
-- Vamos limpar entradas órfãs relacionadas a esses IDs

-- Limpar da tabela de documentos do Strapi (se existir)
DO $$
BEGIN
    -- Verificar se a tabela existe
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%categoria%document%'
    ) THEN
        -- Tentar encontrar e deletar documentos órfãos
        -- Nota: O nome exato da tabela pode variar dependendo da versão do Strapi
        RAISE NOTICE 'Tabela de documentos encontrada, mas limpeza manual pode ser necessária';
    END IF;
END $$;

-- 6. Verificar resultados
SELECT 'Verificação final - Categorias 31 e 32:' AS status;
SELECT id, nome FROM categorias WHERE id IN (31, 32);

SELECT 'Verificação final - Nome produto 9:' AS status;
SELECT id, nome FROM nome_produto WHERE id = 9;

SELECT 'Limpeza concluída!' AS status;
