-- Script de sincronização de relacionamentos
-- Sincroniza dados das tabelas de link para as colunas diretas
-- Execute periodicamente ou após operações em lote no Strapi

-- Sincronizar categoria_id e tecido_id em estampa
UPDATE estampa 
SET categoria_id = (
  SELECT categoria_id 
  FROM estampa_categoria_lnk 
  WHERE estampa_id = estampa.id 
  LIMIT 1
)
WHERE categoria_id IS NULL 
  AND EXISTS (
    SELECT 1 
    FROM estampa_categoria_lnk 
    WHERE estampa_id = estampa.id
  );

UPDATE estampa 
SET tecido_id = (
  SELECT tecido_id 
  FROM estampa_tecido_lnk 
  WHERE estampa_id = estampa.id 
  LIMIT 1
)
WHERE tecido_id IS NULL 
  AND EXISTS (
    SELECT 1 
    FROM estampa_tecido_lnk 
    WHERE estampa_id = estampa.id
  );

-- Sincronizar categoria_id em nome_produto
UPDATE nome_produto 
SET categoria_id = (
  SELECT categoria_id 
  FROM nome_produto_categoria_lnk 
  WHERE nome_produto_id = nome_produto.id 
  LIMIT 1
)
WHERE categoria_id IS NULL 
  AND EXISTS (
    SELECT 1 
    FROM nome_produto_categoria_lnk 
    WHERE nome_produto_id = nome_produto.id
  );

-- Sincronizar nome_produto_id, estampa_id e tamanho_id em produtos
UPDATE produtos 
SET nome_produto_id = (
  SELECT nome_produto_id 
  FROM produtos_nome_produto_lnk 
  WHERE produto_id = produtos.id 
  LIMIT 1
)
WHERE nome_produto_id IS NULL 
  AND EXISTS (
    SELECT 1 
    FROM produtos_nome_produto_lnk 
    WHERE produto_id = produtos.id
  );

UPDATE produtos 
SET estampa_id = (
  SELECT estampa_id 
  FROM produtos_estampa_lnk 
  WHERE produto_id = produtos.id 
  LIMIT 1
)
WHERE estampa_id IS NULL 
  AND EXISTS (
    SELECT 1 
    FROM produtos_estampa_lnk 
    WHERE produto_id = produtos.id
  );

UPDATE produtos 
SET tamanho_id = (
  SELECT tamanho_id 
  FROM produtos_tamanho_lnk 
  WHERE produto_id = produtos.id 
  LIMIT 1
)
WHERE tamanho_id IS NULL 
  AND EXISTS (
    SELECT 1 
    FROM produtos_tamanho_lnk 
    WHERE produto_id = produtos.id
  );
