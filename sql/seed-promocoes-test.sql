-- =====================================================
-- Script para Adicionar Promoções de Teste
-- =====================================================
-- Este script adiciona preco_promocional em alguns produtos
-- para testar a funcionalidade de promoções
-- =====================================================

-- Atualizar alguns produtos com preço promocional (20% de desconto)
-- Seleciona os primeiros 5 produtos e aplica desconto de 20%
UPDATE produtos 
SET preco_promocional = ROUND(preco_venda * 0.8, 2)
WHERE id IN (
    SELECT id 
    FROM produtos 
    WHERE ativo = TRUE 
    AND estoque > 0
    ORDER BY id
    LIMIT 5
);

-- Adicionar alguns produtos com desconto maior (30%)
UPDATE produtos 
SET preco_promocional = ROUND(preco_venda * 0.7, 2)
WHERE id IN (
    SELECT id 
    FROM produtos 
    WHERE ativo = TRUE 
    AND estoque > 0
    AND preco_promocional IS NULL
    ORDER BY id DESC
    LIMIT 3
);

-- Verificar produtos com promoção
SELECT 
    p.id,
    p.codigo_sku,
    np.nome as nome_produto,
    e.nome as estampa,
    t.nome as tamanho,
    p.preco_venda,
    p.preco_promocional,
    ROUND(((p.preco_venda - p.preco_promocional) / p.preco_venda) * 100, 0) as desconto_percentual
FROM produtos p
JOIN nome_produto np ON p.nome_produto_id = np.id
JOIN estampa e ON p.estampa_id = e.id
JOIN tamanho t ON p.tamanho_id = t.id
WHERE p.preco_promocional IS NOT NULL
ORDER BY p.id;




