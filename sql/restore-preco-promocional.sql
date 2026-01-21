-- Script para restaurar campo preco_promocional
-- ==========================================
-- Strapi é a fonte da verdade, Bling apenas gerencia preço de venda

-- Adicionar preco_promocional de volta à tabela produtos
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='produtos' AND column_name='preco_promocional'
    ) THEN
        ALTER TABLE produtos ADD COLUMN preco_promocional DECIMAL(10, 2);
        RAISE NOTICE '[OK] Campo preco_promocional adicionado';
    ELSE
        RAISE NOTICE '[PULADO] Campo preco_promocional já existe';
    END IF;
END $$;
