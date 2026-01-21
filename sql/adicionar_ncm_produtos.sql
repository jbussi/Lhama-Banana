-- Adicionar coluna NCM na tabela produtos se não existir
-- NCM é obrigatório para sincronização com Bling

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'produtos' 
        AND column_name = 'ncm'
    ) THEN
        ALTER TABLE produtos 
        ADD COLUMN ncm VARCHAR(8);
        
        COMMENT ON COLUMN produtos.ncm IS 'NCM (Nomenclatura Comum do Mercosul) - Obrigatório para Bling';
        
        RAISE NOTICE 'Coluna NCM adicionada com sucesso!';
    ELSE
        RAISE NOTICE 'Coluna NCM já existe.';
    END IF;
END $$;

-- Atualizar produtos de teste com NCMs válidos
UPDATE produtos 
SET ncm = '61091000'  -- Camisetas de algodão
WHERE codigo_sku LIKE 'CAM-%' 
AND (ncm IS NULL OR ncm = '');

UPDATE produtos 
SET ncm = '61092000'  -- Regatas
WHERE codigo_sku LIKE 'REG-%' 
AND (ncm IS NULL OR ncm = '');
