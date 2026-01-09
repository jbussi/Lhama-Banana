-- Script para popular dados de exemplo na loja
-- Execute este script para criar produtos, categorias, estampas, tamanhos e variações de exemplo

-- Inserir categorias de exemplo
INSERT INTO categorias (nome, descricao, ordem_exibicao, ativo) VALUES
('Camisetas', 'Camisetas com estampas exclusivas', 1, TRUE),
('Regatas', 'Regatas confortáveis para o dia a dia', 2, TRUE),
('Moletom', 'Moletons quentinhos e estilosos', 3, TRUE),
('Acessórios', 'Acessórios diversos', 4, TRUE)
ON CONFLICT (nome) DO NOTHING;

-- Inserir tamanhos de exemplo
INSERT INTO tamanho (nome, ordem_exibicao, ativo) VALUES
('P', 1, TRUE),
('M', 2, TRUE),
('G', 3, TRUE),
('GG', 4, TRUE),
('XG', 5, TRUE)
ON CONFLICT (nome) DO NOTHING;

-- Inserir estampas de exemplo (com tecido e sexo)
INSERT INTO estampa (nome, descricao, imagem_url, categoria_id, sexo, tecido, custo_por_metro, ordem_exibicao, ativo) VALUES
('Lhama Feliz', 'Lhama sorridente com óculos de sol', '/static/img/estampas/lhama-feliz.jpg', 
 (SELECT id FROM categorias WHERE nome = 'Camisetas'), 'u', 'Algodão 100%', 25.00, 1, TRUE),
('Lhama Espacial', 'Lhama astronauta explorando o espaço', '/static/img/estampas/lhama-espacial.jpg',
 (SELECT id FROM categorias WHERE nome = 'Camisetas'), 'm', 'Algodão 100%', 28.00, 2, TRUE),
('Lhama Princesa', 'Lhama com coroa e vestido rosa', '/static/img/estampas/lhama-princesa.jpg',
 (SELECT id FROM categorias WHERE nome = 'Camisetas'), 'f', 'Algodão 100%', 28.00, 3, TRUE),
('Lhama Surfista', 'Lhama pegando onda na praia', '/static/img/estampas/lhama-surfista.jpg',
 (SELECT id FROM categorias WHERE nome = 'Regatas'), 'u', 'Poliéster', 22.00, 4, TRUE),
('Lhama Rockstar', 'Lhama com guitarra e óculos escuros', '/static/img/estampas/lhama-rockstar.jpg',
 (SELECT id FROM categorias WHERE nome = 'Camisetas'), 'm', 'Algodão 100%', 30.00, 5, TRUE),
('Lhama Floral', 'Lhama com flores e cores vibrantes', '/static/img/estampas/lhama-floral.jpg',
 (SELECT id FROM categorias WHERE nome = 'Camisetas'), 'f', 'Algodão 100%', 27.00, 6, TRUE),
('Lhama Minimalista', 'Lhama em estilo minimalista preto e branco', '/static/img/estampas/lhama-minimalista.jpg',
 (SELECT id FROM categorias WHERE nome = 'Moletom'), 'u', 'Algodão com Poliéster', 35.00, 7, TRUE),
('Lhama Tropical', 'Lhama com palmeiras e cores tropicais', '/static/img/estampas/lhama-tropical.jpg',
 (SELECT id FROM categorias WHERE nome = 'Regatas'), 'u', 'Poliéster', 24.00, 8, TRUE)
ON CONFLICT (nome) DO NOTHING;

-- Inserir produtos base (nome_produto)
INSERT INTO nome_produto (nome, descricao, descricao_curta, categoria_id, ativo, destaque) VALUES
('Camiseta Básica Lhama', 'Camiseta básica de algodão com estampas exclusivas de lhamas', 
 'Camiseta confortável com estampas únicas', 
 (SELECT id FROM categorias WHERE nome = 'Camisetas'), TRUE, TRUE),
('Regata Esportiva Lhama', 'Regata esportiva perfeita para o verão', 
 'Regata leve e confortável', 
 (SELECT id FROM categorias WHERE nome = 'Regatas'), TRUE, TRUE),
('Moletom Lhama', 'Moletom quentinho e estiloso', 
 'Moletom perfeito para o inverno', 
 (SELECT id FROM categorias WHERE nome = 'Moletom'), TRUE, FALSE)
ON CONFLICT (nome) DO NOTHING;

-- Inserir variações de produtos (produtos) com estoque
-- Camiseta Básica Lhama - Lhama Feliz
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    35.00,
    59.90,
    50,
    'CAM-LHAMA-FELIZ-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Camiseta Básica Lhama'
  AND e.nome = 'Lhama Feliz'
  AND t.nome IN ('P', 'M', 'G', 'GG')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 50;

-- Camiseta Básica Lhama - Lhama Espacial
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    38.00,
    64.90,
    30,
    'CAM-LHAMA-ESPACIAL-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Camiseta Básica Lhama'
  AND e.nome = 'Lhama Espacial'
  AND t.nome IN ('M', 'G', 'GG', 'XG')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 30;

-- Camiseta Básica Lhama - Lhama Princesa
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    38.00,
    64.90,
    40,
    'CAM-LHAMA-PRINCESA-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Camiseta Básica Lhama'
  AND e.nome = 'Lhama Princesa'
  AND t.nome IN ('P', 'M', 'G')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 40;

-- Camiseta Básica Lhama - Lhama Rockstar
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    40.00,
    69.90,
    25,
    'CAM-LHAMA-ROCKSTAR-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Camiseta Básica Lhama'
  AND e.nome = 'Lhama Rockstar'
  AND t.nome IN ('M', 'G', 'GG')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 25;

-- Camiseta Básica Lhama - Lhama Floral
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    37.00,
    64.90,
    35,
    'CAM-LHAMA-FLORAL-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Camiseta Básica Lhama'
  AND e.nome = 'Lhama Floral'
  AND t.nome IN ('P', 'M', 'G', 'GG')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 35;

-- Regata Esportiva Lhama - Lhama Surfista
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    30.00,
    49.90,
    45,
    'REG-LHAMA-SURFISTA-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Regata Esportiva Lhama'
  AND e.nome = 'Lhama Surfista'
  AND t.nome IN ('P', 'M', 'G', 'GG')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 45;

-- Regata Esportiva Lhama - Lhama Tropical
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    32.00,
    54.90,
    40,
    'REG-LHAMA-TROPICAL-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Regata Esportiva Lhama'
  AND e.nome = 'Lhama Tropical'
  AND t.nome IN ('M', 'G', 'GG', 'XG')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 40;

-- Moletom Lhama - Lhama Minimalista
INSERT INTO produtos (nome_produto_id, estampa_id, tamanho_id, custo, preco_venda, estoque, codigo_sku, ativo)
SELECT 
    np.id,
    e.id,
    t.id,
    55.00,
    99.90,
    20,
    'MOL-LHAMA-MINIMALISTA-' || t.nome,
    TRUE
FROM nome_produto np, estampa e, tamanho t
WHERE np.nome = 'Moletom Lhama'
  AND e.nome = 'Lhama Minimalista'
  AND t.nome IN ('M', 'G', 'GG', 'XG')
ON CONFLICT (nome_produto_id, estampa_id, tamanho_id) DO UPDATE SET estoque = 20;

-- Inserir imagens de exemplo (usando placeholder por enquanto)
-- Nota: Você precisará substituir essas URLs por imagens reais
INSERT INTO imagens_produto (produto_id, url, ordem, is_thumbnail)
SELECT 
    p.id,
    '/static/img/placeholder.jpg',
    1,
    TRUE
FROM produtos p
WHERE NOT EXISTS (
    SELECT 1 FROM imagens_produto ip WHERE ip.produto_id = p.id
)
LIMIT 100;






