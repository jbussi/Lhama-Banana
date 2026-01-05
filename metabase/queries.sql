-- =====================================================
-- QUERIES SQL PARA DASHBOARDS DO METABASE
-- =====================================================
-- Este arquivo contém todas as queries SQL prontas para uso no Metabase
-- Organizadas por dashboard e métrica
-- =====================================================

-- =====================================================
-- DASHBOARD 1: VENDAS
-- =====================================================

-- 1.1. Total de Vendas (Contador)
SELECT COUNT(*) as total_vendas
FROM vendas;

-- 1.2. Receita Total (Soma)
SELECT COALESCE(SUM(valor_total), 0) as receita_total
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado');

-- 1.3. Ticket Médio (Média)
SELECT 
  COALESCE(AVG(valor_total), 0) as ticket_medio
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado');

-- 1.4. Vendas por Período (Dia)
SELECT 
  DATE(data_venda) as dia,
  COUNT(*) as total_vendas,
  COALESCE(SUM(valor_total), 0) as receita_dia,
  COALESCE(AVG(valor_total), 0) as ticket_medio_dia
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY DATE(data_venda)
ORDER BY dia DESC;

-- 1.5. Vendas por Período (Semana)
SELECT 
  DATE_TRUNC('week', data_venda) as semana,
  COUNT(*) as total_vendas,
  COALESCE(SUM(valor_total), 0) as receita_semana,
  COALESCE(AVG(valor_total), 0) as ticket_medio_semana
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY DATE_TRUNC('week', data_venda)
ORDER BY semana DESC;

-- 1.6. Vendas por Período (Mês)
SELECT 
  DATE_TRUNC('month', data_venda) as mes,
  COUNT(*) as total_vendas,
  COALESCE(SUM(valor_total), 0) as receita_mes,
  COALESCE(AVG(valor_total), 0) as ticket_medio_mes
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY DATE_TRUNC('month', data_venda)
ORDER BY mes DESC;

-- 1.7. Status dos Pedidos (Gráfico de Pizza)
SELECT 
  status_pedido,
  COUNT(*) as quantidade,
  COALESCE(SUM(valor_total), 0) as valor_total
FROM vendas
GROUP BY status_pedido
ORDER BY quantidade DESC;

-- 1.8. Vendas por Status (Últimos 30 dias)
SELECT 
  status_pedido,
  COUNT(*) as quantidade,
  COALESCE(SUM(valor_total), 0) as valor_total
FROM vendas
WHERE data_venda >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY status_pedido
ORDER BY quantidade DESC;

-- =====================================================
-- DASHBOARD 2: PRODUTOS
-- =====================================================

-- 2.1. Produtos Mais Vendidos (Top 10)
SELECT 
  np.nome as nome_produto,
  COUNT(iv.id) as total_vendido,
  SUM(iv.quantidade) as quantidade_total,
  COALESCE(SUM(iv.subtotal), 0) as receita_total
FROM itens_venda iv
JOIN produtos p ON iv.produto_id = p.id
JOIN nome_produto np ON p.nome_produto_id = np.id
JOIN vendas v ON iv.venda_id = v.id
WHERE v.status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY np.id, np.nome
ORDER BY total_vendido DESC
LIMIT 10;

-- 2.2. Produtos Mais Vendidos por Quantidade
SELECT 
  np.nome as nome_produto,
  SUM(iv.quantidade) as quantidade_total,
  COUNT(DISTINCT iv.venda_id) as numero_pedidos,
  COALESCE(SUM(iv.subtotal), 0) as receita_total
FROM itens_venda iv
JOIN produtos p ON iv.produto_id = p.id
JOIN nome_produto np ON p.nome_produto_id = np.id
JOIN vendas v ON iv.venda_id = v.id
WHERE v.status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY np.id, np.nome
ORDER BY quantidade_total DESC
LIMIT 10;

-- 2.3. Estoque Atual vs Estoque Mínimo
SELECT 
  np.nome as nome_produto,
  p.codigo_sku,
  p.estoque,
  p.estoque_minimo,
  (p.estoque - p.estoque_minimo) as diferenca,
  CASE 
    WHEN p.estoque <= 0 THEN 'Sem Estoque'
    WHEN p.estoque <= p.estoque_minimo THEN 'Estoque Baixo'
    ELSE 'Estoque OK'
  END as status_estoque
FROM produtos p
JOIN nome_produto np ON p.nome_produto_id = np.id
WHERE p.ativo = TRUE
ORDER BY diferenca ASC;

-- 2.4. Produtos com Estoque Baixo (Alerta)
SELECT 
  np.nome as nome_produto,
  p.codigo_sku,
  p.estoque,
  p.estoque_minimo,
  (p.estoque_minimo - p.estoque) as falta_estoque
FROM produtos p
JOIN nome_produto np ON p.nome_produto_id = np.id
WHERE p.ativo = TRUE 
  AND p.estoque <= p.estoque_minimo
ORDER BY falta_estoque DESC;

-- 2.5. Produtos Sem Estoque
SELECT 
  np.nome as nome_produto,
  p.codigo_sku,
  p.estoque,
  p.estoque_minimo
FROM produtos p
JOIN nome_produto np ON p.nome_produto_id = np.id
WHERE p.ativo = TRUE 
  AND p.estoque <= 0
ORDER BY np.nome;

-- 2.6. Total de Produtos por Categoria
SELECT 
  c.nome as categoria,
  COUNT(DISTINCT p.id) as total_produtos,
  SUM(p.estoque) as estoque_total
FROM produtos p
JOIN nome_produto np ON p.nome_produto_id = np.id
JOIN categorias c ON np.categoria_id = c.id
WHERE p.ativo = TRUE
GROUP BY c.id, c.nome
ORDER BY total_produtos DESC;

-- =====================================================
-- DASHBOARD 3: PAGAMENTOS
-- =====================================================

-- 3.1. Status de Pagamentos (Gráfico de Pizza)
SELECT 
  status_pagamento,
  COUNT(*) as quantidade,
  COALESCE(SUM(valor_pago), 0) as valor_total
FROM pagamentos
GROUP BY status_pagamento
ORDER BY quantidade DESC;

-- 3.2. Métodos de Pagamento (Gráfico de Barras)
SELECT 
  forma_pagamento_tipo,
  COUNT(*) as quantidade,
  COALESCE(SUM(valor_pago), 0) as valor_total,
  COALESCE(AVG(valor_pago), 0) as ticket_medio
FROM pagamentos
WHERE status_pagamento IN ('PAID', 'AUTHORIZED')
GROUP BY forma_pagamento_tipo
ORDER BY valor_total DESC;

-- 3.3. Taxa de Conversão (Pagos vs Pendentes)
SELECT 
  CASE 
    WHEN status_pagamento IN ('PAID', 'AUTHORIZED') THEN 'Pagos'
    WHEN status_pagamento IN ('PENDING', 'WAITING') THEN 'Pendentes'
    WHEN status_pagamento IN ('DECLINED', 'CANCELLED', 'EXPIRED') THEN 'Cancelados'
    ELSE 'Outros'
  END as status_grupo,
  COUNT(*) as quantidade,
  COALESCE(SUM(valor_pago), 0) as valor_total,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentual
FROM pagamentos
GROUP BY 
  CASE 
    WHEN status_pagamento IN ('PAID', 'AUTHORIZED') THEN 'Pagos'
    WHEN status_pagamento IN ('PENDING', 'WAITING') THEN 'Pendentes'
    WHEN status_pagamento IN ('DECLINED', 'CANCELLED', 'EXPIRED') THEN 'Cancelados'
    ELSE 'Outros'
  END;

-- 3.4. Performance por Método de Pagamento
SELECT 
  forma_pagamento_tipo,
  COUNT(*) as total_tentativas,
  COUNT(CASE WHEN status_pagamento IN ('PAID', 'AUTHORIZED') THEN 1 END) as pagos,
  COUNT(CASE WHEN status_pagamento IN ('PENDING', 'WAITING') THEN 1 END) as pendentes,
  COUNT(CASE WHEN status_pagamento IN ('DECLINED', 'CANCELLED', 'EXPIRED') THEN 1 END) as cancelados,
  ROUND(100.0 * COUNT(CASE WHEN status_pagamento IN ('PAID', 'AUTHORIZED') THEN 1 END) / COUNT(*), 2) as taxa_sucesso,
  COALESCE(SUM(CASE WHEN status_pagamento IN ('PAID', 'AUTHORIZED') THEN valor_pago ELSE 0 END), 0) as receita_total
FROM pagamentos
GROUP BY forma_pagamento_tipo
ORDER BY receita_total DESC;

-- 3.5. Pagamentos por Período (Últimos 30 dias)
SELECT 
  DATE(criado_em) as dia,
  forma_pagamento_tipo,
  COUNT(*) as quantidade,
  COALESCE(SUM(CASE WHEN status_pagamento IN ('PAID', 'AUTHORIZED') THEN valor_pago ELSE 0 END), 0) as receita
FROM pagamentos
WHERE criado_em >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(criado_em), forma_pagamento_tipo
ORDER BY dia DESC, receita DESC;

-- 3.6. Pedidos Pagos vs Abandonados
SELECT 
  CASE 
    WHEN p.status_pagamento IN ('PAID', 'AUTHORIZED') THEN 'Pagos'
    WHEN p.status_pagamento IN ('PENDING', 'WAITING') AND v.data_venda < CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 'Abandonados'
    WHEN p.status_pagamento IN ('PENDING', 'WAITING') THEN 'Pendentes'
    ELSE 'Outros'
  END as status_grupo,
  COUNT(DISTINCT v.id) as quantidade_pedidos,
  COALESCE(SUM(v.valor_total), 0) as valor_total
FROM vendas v
LEFT JOIN pagamentos p ON v.id = p.venda_id
WHERE v.status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY 
  CASE 
    WHEN p.status_pagamento IN ('PAID', 'AUTHORIZED') THEN 'Pagos'
    WHEN p.status_pagamento IN ('PENDING', 'WAITING') AND v.data_venda < CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 'Abandonados'
    WHEN p.status_pagamento IN ('PENDING', 'WAITING') THEN 'Pendentes'
    ELSE 'Outros'
  END;

-- =====================================================
-- DASHBOARD 4: FRETE E ENVIOS
-- =====================================================

-- 4.1. Total de Etiquetas Geradas
SELECT COUNT(*) as total_etiquetas
FROM etiquetas_frete;

-- 4.2. Status de Etiquetas
SELECT 
  status_etiqueta,
  COUNT(*) as quantidade,
  COALESCE(SUM(valor_frete), 0) as custo_total_frete
FROM etiquetas_frete
GROUP BY status_etiqueta
ORDER BY quantidade DESC;

-- 4.3. Etiquetas por Transportadora
SELECT 
  transportadora_nome,
  COUNT(*) as total_etiquetas,
  COALESCE(SUM(valor_frete), 0) as custo_total,
  COALESCE(AVG(valor_frete), 0) as custo_medio
FROM etiquetas_frete
WHERE transportadora_nome IS NOT NULL
GROUP BY transportadora_nome
ORDER BY total_etiquetas DESC;

-- 4.4. Etiquetas Enviadas vs Pendentes
SELECT 
  CASE 
    WHEN status_etiqueta IN ('impressa', 'em_transito', 'entregue') THEN 'Enviadas'
    WHEN status_etiqueta IN ('pendente', 'criada', 'paga') THEN 'Pendentes'
    ELSE 'Outros'
  END as status_grupo,
  COUNT(*) as quantidade,
  COALESCE(SUM(valor_frete), 0) as custo_total
FROM etiquetas_frete
GROUP BY 
  CASE 
    WHEN status_etiqueta IN ('impressa', 'em_transito', 'entregue') THEN 'Enviadas'
    WHEN status_etiqueta IN ('pendente', 'criada', 'paga') THEN 'Pendentes'
    ELSE 'Outros'
  END;

-- 4.5. Tempo Médio de Envio (Dias entre criação e envio)
SELECT 
  AVG(EXTRACT(EPOCH FROM (enviada_em - criado_em)) / 86400) as dias_medio_envio
FROM etiquetas_frete
WHERE enviada_em IS NOT NULL AND criado_em IS NOT NULL;

-- 4.6. Etiquetas por Período (Últimos 30 dias)
SELECT 
  DATE(criado_em) as dia,
  COUNT(*) as total_etiquetas,
  COUNT(CASE WHEN status_etiqueta = 'entregue' THEN 1 END) as entregues,
  COALESCE(SUM(valor_frete), 0) as custo_total
FROM etiquetas_frete
WHERE criado_em >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(criado_em)
ORDER BY dia DESC;

-- =====================================================
-- DASHBOARD 5: CUPONS
-- =====================================================

-- 5.1. Cupons Utilizados (Total)
SELECT 
  COUNT(*) as total_cupons_usados,
  COALESCE(SUM(valor_desconto_aplicado), 0) as desconto_total_aplicado
FROM cupom_usado;

-- 5.2. Cupons Mais Utilizados
SELECT 
  c.codigo,
  c.tipo,
  c.valor,
  COUNT(cu.id) as vezes_usado,
  COALESCE(SUM(cu.valor_desconto_aplicado), 0) as desconto_total_aplicado,
  COALESCE(AVG(cu.valor_desconto_aplicado), 0) as desconto_medio
FROM cupom c
LEFT JOIN cupom_usado cu ON c.id = cu.cupom_id
GROUP BY c.id, c.codigo, c.tipo, c.valor
ORDER BY vezes_usado DESC;

-- 5.3. Cupons por Status (Ativos vs Inativos)
SELECT 
  CASE WHEN ativo THEN 'Ativos' ELSE 'Inativos' END as status,
  COUNT(*) as total_cupons,
  SUM(uso_atual) as total_usos,
  COALESCE(SUM(CASE WHEN tipo = 'p' THEN valor ELSE 0 END), 0) as valor_percentual_medio,
  COALESCE(SUM(CASE WHEN tipo = 'v' THEN valor ELSE 0 END), 0) as valor_fixo_total
FROM cupom
GROUP BY ativo;

-- 5.4. Cupons Utilizados por Período
SELECT 
  DATE(cu.data_uso) as dia,
  COUNT(*) as vezes_usado,
  COALESCE(SUM(cu.valor_desconto_aplicado), 0) as desconto_total
FROM cupom_usado cu
GROUP BY DATE(cu.data_uso)
ORDER BY dia DESC;

-- 5.5. Taxa de Uso de Cupons (Usados vs Disponíveis)
SELECT 
  COUNT(DISTINCT c.id) as total_cupons,
  COUNT(DISTINCT cu.cupom_id) as cupons_usados,
  ROUND(100.0 * COUNT(DISTINCT cu.cupom_id) / NULLIF(COUNT(DISTINCT c.id), 0), 2) as taxa_uso
FROM cupom c
LEFT JOIN cupom_usado cu ON c.id = cu.cupom_id
WHERE c.ativo = TRUE;

-- =====================================================
-- DASHBOARD 6: USUÁRIOS E CLIENTES
-- =====================================================

-- 6.1. Total de Usuários
SELECT COUNT(*) as total_usuarios
FROM usuarios
WHERE ativo = TRUE;

-- 6.2. Novos Usuários por Período
SELECT 
  DATE(criado_em) as dia,
  COUNT(*) as novos_usuarios
FROM usuarios
WHERE criado_em >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(criado_em)
ORDER BY dia DESC;

-- 6.3. Usuários por Role
SELECT 
  role,
  COUNT(*) as quantidade
FROM usuarios
WHERE ativo = TRUE
GROUP BY role
ORDER BY quantidade DESC;

-- 6.4. Top Clientes (Maior Gasto)
SELECT 
  u.nome,
  u.email,
  COUNT(DISTINCT v.id) as total_pedidos,
  COALESCE(SUM(v.valor_total), 0) as total_gasto,
  COALESCE(AVG(v.valor_total), 0) as ticket_medio
FROM usuarios u
LEFT JOIN vendas v ON u.id = v.usuario_id
WHERE u.ativo = TRUE 
  AND v.status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY u.id, u.nome, u.email
HAVING COUNT(DISTINCT v.id) > 0
ORDER BY total_gasto DESC
LIMIT 10;

-- 6.5. Clientes por Estado
SELECT 
  e.estado,
  COUNT(DISTINCT u.id) as total_clientes,
  COUNT(DISTINCT v.id) as total_pedidos,
  COALESCE(SUM(v.valor_total), 0) as receita_total
FROM usuarios u
JOIN enderecos e ON u.id = e.usuario_id
LEFT JOIN vendas v ON u.id = v.usuario_id
WHERE u.ativo = TRUE 
  AND e.is_default = TRUE
  AND v.status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY e.estado
ORDER BY total_clientes DESC;

-- =====================================================
-- DASHBOARD 7: MÉTRICAS OPERACIONAIS
-- =====================================================

-- 7.1. Pedidos por Prioridade
SELECT 
  CASE 
    WHEN prioridade = 0 THEN 'Normal'
    WHEN prioridade = 1 THEN 'Alta'
    WHEN prioridade = 2 THEN 'Urgente'
    ELSE 'Não Definida'
  END as prioridade,
  COUNT(*) as quantidade
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado', 'entregue')
GROUP BY prioridade
ORDER BY prioridade DESC;

-- 7.2. Tempo Médio de Processamento (Criação até Envio)
SELECT 
  AVG(EXTRACT(EPOCH FROM (data_envio - data_venda)) / 3600) as horas_medio_processamento
FROM vendas
WHERE data_envio IS NOT NULL 
  AND data_venda IS NOT NULL
  AND status_pedido IN ('enviado', 'entregue');

-- 7.3. Pedidos Atrasados (Sem Envio após 3 dias)
SELECT 
  v.codigo_pedido,
  v.data_venda,
  v.status_pedido,
  EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v.data_venda)) / 86400 as dias_em_aberto,
  v.valor_total
FROM vendas v
WHERE v.status_pedido IN ('processando_envio', 'pendente_pagamento')
  AND v.data_venda < CURRENT_TIMESTAMP - INTERVAL '3 days'
  AND v.data_envio IS NULL
ORDER BY dias_em_aberto DESC;

-- 7.4. Taxa de Cancelamento
SELECT 
  COUNT(CASE WHEN status_pedido IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor') THEN 1 END) as cancelados,
  COUNT(*) as total_pedidos,
  ROUND(100.0 * COUNT(CASE WHEN status_pedido IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor') THEN 1 END) / NULLIF(COUNT(*), 0), 2) as taxa_cancelamento
FROM vendas;

-- 7.5. Receita por Origem (Web, Mobile, API)
SELECT 
  origem,
  COUNT(*) as total_pedidos,
  COALESCE(SUM(valor_total), 0) as receita_total,
  COALESCE(AVG(valor_total), 0) as ticket_medio
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY origem
ORDER BY receita_total DESC;

-- =====================================================
-- DASHBOARD 8: VISÃO GERAL (OVERVIEW)
-- =====================================================

-- 8.1. Métricas Principais (Últimos 30 dias)
SELECT 
  COUNT(DISTINCT v.id) as total_vendas,
  COALESCE(SUM(v.valor_total), 0) as receita_total,
  COALESCE(AVG(v.valor_total), 0) as ticket_medio,
  COUNT(DISTINCT v.usuario_id) as clientes_unicos,
  COUNT(DISTINCT p.id) as produtos_vendidos,
  COUNT(DISTINCT ef.id) as etiquetas_geradas
FROM vendas v
LEFT JOIN itens_venda iv ON v.id = iv.venda_id
LEFT JOIN produtos p ON iv.produto_id = p.id
LEFT JOIN etiquetas_frete ef ON v.id = ef.venda_id
WHERE v.data_venda >= CURRENT_DATE - INTERVAL '30 days'
  AND v.status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado');

-- 8.2. Comparativo Mensal (Últimos 6 meses)
SELECT 
  TO_CHAR(DATE_TRUNC('month', data_venda), 'YYYY-MM') as mes,
  COUNT(*) as total_vendas,
  COALESCE(SUM(valor_total), 0) as receita,
  COALESCE(AVG(valor_total), 0) as ticket_medio
FROM vendas
WHERE data_venda >= CURRENT_DATE - INTERVAL '6 months'
  AND status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY DATE_TRUNC('month', data_venda)
ORDER BY mes DESC;

-- 8.3. Top 5 Produtos do Mês
SELECT 
  np.nome as produto,
  SUM(iv.quantidade) as quantidade_vendida,
  COALESCE(SUM(iv.subtotal), 0) as receita
FROM itens_venda iv
JOIN produtos p ON iv.produto_id = p.id
JOIN nome_produto np ON p.nome_produto_id = np.id
JOIN vendas v ON iv.venda_id = v.id
WHERE v.data_venda >= DATE_TRUNC('month', CURRENT_DATE)
  AND v.status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
GROUP BY np.id, np.nome
ORDER BY quantidade_vendida DESC
LIMIT 5;


