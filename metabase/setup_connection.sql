-- =====================================================
-- SCRIPT DE CONFIGURAÇÃO INICIAL DO METABASE
-- =====================================================
-- Este script ajuda a verificar a conexão com o banco
-- Execute no PostgreSQL para testar as queries antes
-- de configurar no Metabase
-- =====================================================

-- Verificar se o banco está acessível
SELECT 
  current_database() as banco_atual,
  current_user as usuario_atual,
  version() as versao_postgres;

-- Verificar tabelas principais
SELECT 
  table_name,
  table_type
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'vendas', 
    'produtos', 
    'usuarios', 
    'cupom', 
    'pagamentos', 
    'etiquetas_frete',
    'itens_venda'
  )
ORDER BY table_name;

-- Contar registros nas tabelas principais
SELECT 
  'vendas' as tabela, COUNT(*) as total FROM vendas
UNION ALL
SELECT 
  'produtos' as tabela, COUNT(*) as total FROM produtos
UNION ALL
SELECT 
  'usuarios' as tabela, COUNT(*) as total FROM usuarios
UNION ALL
SELECT 
  'cupom' as tabela, COUNT(*) as total FROM cupom
UNION ALL
SELECT 
  'pagamentos' as tabela, COUNT(*) as total FROM pagamentos
UNION ALL
SELECT 
  'etiquetas_frete' as tabela, COUNT(*) as total FROM etiquetas_frete
UNION ALL
SELECT 
  'itens_venda' as tabela, COUNT(*) as total FROM itens_venda;

-- Testar query simples de vendas
SELECT 
  COUNT(*) as total_vendas,
  COALESCE(SUM(valor_total), 0) as receita_total
FROM vendas
WHERE status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado');

-- Verificar estrutura da tabela vendas
SELECT 
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'vendas'
ORDER BY ordinal_position;


