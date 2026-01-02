-- =====================================================
-- SCHEMA COMPLETO DO BANCO DE DADOS - LHAMA BANANA
-- =====================================================
-- Este arquivo contém a definição completa do schema do banco de dados.
-- Execute este arquivo para criar todas as tabelas, índices, funções e triggers.
-- 
-- Características:
-- - Auditoria completa de alterações
-- - Logs de ações administrativas
-- - Rastreabilidade de operações
-- - Suporte a painel administrativo (Strapi)
-- - Campos para operação diária
-- - Segurança e integridade de dados
-- =====================================================

-- Garante que estamos no schema público padrão
SET search_path TO public;

-- =====================================================
-- EXTENSÕES
-- =====================================================

-- Extensão para UUID (já vem com PostgreSQL 13+)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- FUNÇÕES AUXILIARES
-- =====================================================

-- Função para atualizar timestamps automaticamente
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.atualizado_em = NOW();
   RETURN NEW;
END;
$$ language plpgsql;

-- Função para criar log de auditoria
CREATE OR REPLACE FUNCTION create_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO auditoria_logs (
        tabela_afetada,
        registro_id,
        acao,
        dados_anteriores,
        dados_novos,
        usuario_id,
        ip_address,
        user_agent
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN row_to_json(OLD)::jsonb ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW)::jsonb ELSE NULL END,
        current_setting('app.user_id', true)::integer,
        current_setting('app.ip_address', true),
        current_setting('app.user_agent', true)
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ language plpgsql;

-- =====================================================
-- TABELAS BASE
-- =====================================================

-- Tabela para gerenciar categorias de produtos e estampas
CREATE TABLE IF NOT EXISTS categorias (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(50) UNIQUE NOT NULL,
  descricao TEXT,
  ordem_exibicao INTEGER DEFAULT 0, -- Para ordenar categorias no painel
  ativo BOOLEAN DEFAULT TRUE, -- Para ativar/desativar categorias
  imagem_url VARCHAR(2000), -- URL da imagem da categoria
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por INTEGER, -- ID do usuário/admin que criou
  atualizado_por INTEGER -- ID do usuário/admin que atualizou
);

-- Tabela para armazenar informações de usuários (clientes e admins)
CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  firebase_uid VARCHAR(128) UNIQUE NOT NULL,
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  genero CHAR(1) DEFAULT 'u' CHECK (genero IN ('m', 'f', 'u')),
  cpf CHAR(11) UNIQUE,
  telefone VARCHAR(15),
  data_nascimento DATE,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  ultimo_login TIMESTAMP, -- Último acesso ao sistema
  imagem_url VARCHAR(2000),
  role VARCHAR(20) DEFAULT 'user' NOT NULL CHECK (role IN ('user', 'admin', 'moderator')),
  ativo BOOLEAN DEFAULT TRUE, -- Para desativar contas
  email_verificado BOOLEAN DEFAULT FALSE, -- Email verificado
  aceita_marketing BOOLEAN DEFAULT FALSE, -- Consentimento para marketing
  total_pedidos INTEGER DEFAULT 0, -- Contador de pedidos (para analytics)
  total_gasto DECIMAL(10, 2) DEFAULT 0 -- Total gasto (para analytics)
);

-- Tabela para listar endereços de entrega dos usuários
CREATE TABLE IF NOT EXISTS enderecos (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
  nome_endereco VARCHAR(50) NOT NULL,
  cep CHAR(8) NOT NULL,
  rua VARCHAR(255) NOT NULL,
  numero VARCHAR(20) NOT NULL,
  complemento VARCHAR(100),
  bairro VARCHAR(100) NOT NULL,
  cidade VARCHAR(100) NOT NULL,
  estado CHAR(2) NOT NULL,
  referencia VARCHAR(255),
  is_default BOOLEAN DEFAULT FALSE,
  email VARCHAR(255),
  telefone VARCHAR(20),
  ativo BOOLEAN DEFAULT TRUE, -- Para desativar endereços
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- TABELAS DE PRODUTOS
-- =====================================================

-- Tabela para definir nomes e descrições base dos produtos
CREATE TABLE IF NOT EXISTS nome_produto (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) UNIQUE NOT NULL,
  descricao TEXT,
  descricao_curta VARCHAR(255), -- Para cards e listagens
  categoria_id INTEGER REFERENCES categorias(id) NOT NULL,
  tags TEXT[], -- Array de tags para busca
  peso_kg DECIMAL(8, 3) DEFAULT 0, -- Peso padrão do produto
  dimensoes_largura DECIMAL(8, 2) DEFAULT 0, -- em cm
  dimensoes_altura DECIMAL(8, 2) DEFAULT 0, -- em cm
  dimensoes_comprimento DECIMAL(8, 2) DEFAULT 0, -- em cm
  ativo BOOLEAN DEFAULT TRUE,
  destaque BOOLEAN DEFAULT FALSE, -- Produto em destaque
  ordem_exibicao INTEGER DEFAULT 0,
  meta_title VARCHAR(255), -- SEO
  meta_description TEXT, -- SEO
  slug VARCHAR(255) UNIQUE, -- URL amigável
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por INTEGER,
  atualizado_por INTEGER
);

-- Tabela para cadastrar as estampas disponíveis
CREATE TABLE IF NOT EXISTS estampa (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) UNIQUE NOT NULL,
  descricao TEXT,
  imagem_url VARCHAR(2000) NOT NULL,
  categoria_id INTEGER REFERENCES categorias(id) NOT NULL,
  sexo CHAR(1) DEFAULT 'u' CHECK (sexo IN ('m', 'f', 'u')),
  custo_por_metro DECIMAL(10, 2) NOT NULL,
  ativo BOOLEAN DEFAULT TRUE,
  ordem_exibicao INTEGER DEFAULT 0,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por INTEGER,
  atualizado_por INTEGER
);

-- Tabela para listar os tamanhos disponíveis
CREATE TABLE IF NOT EXISTS tamanho (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(20) UNIQUE NOT NULL,
  ordem_exibicao INTEGER DEFAULT 0, -- Para ordenar tamanhos
  ativo BOOLEAN DEFAULT TRUE,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para controlar as variações de produtos em estoque
CREATE TABLE IF NOT EXISTS produtos (
  id SERIAL PRIMARY KEY,
  nome_produto_id INTEGER REFERENCES nome_produto(id) ON DELETE CASCADE,
  estampa_id INTEGER REFERENCES estampa(id) ON DELETE CASCADE,
  tamanho_id INTEGER REFERENCES tamanho(id) ON DELETE CASCADE,
  UNIQUE (nome_produto_id, estampa_id, tamanho_id),
  custo DECIMAL(10, 2) NOT NULL,
  preco_venda DECIMAL(10, 2) NOT NULL,
  preco_promocional DECIMAL(10, 2), -- Preço em promoção
  estoque INTEGER NOT NULL DEFAULT 0,
  estoque_minimo INTEGER DEFAULT 0, -- Alerta de estoque baixo
  estoque_reservado INTEGER DEFAULT 0, -- Estoque reservado para pedidos pendentes
  codigo_sku VARCHAR(50) UNIQUE NOT NULL,
  codigo_barras VARCHAR(50), -- Código de barras (EAN)
  ativo BOOLEAN DEFAULT TRUE,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por INTEGER,
  atualizado_por INTEGER
);

CREATE TABLE IF NOT EXISTS imagens_produto (
  id SERIAL PRIMARY KEY,
  produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE,
  url VARCHAR(2000) NOT NULL,
  ordem INTEGER DEFAULT 0,
  descricao VARCHAR(255),
  is_thumbnail BOOLEAN DEFAULT FALSE,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- TABELAS DE CUPONS
-- =====================================================

-- Tabela para gerenciar cupons de desconto
CREATE TABLE IF NOT EXISTS cupom (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(20) UNIQUE NOT NULL,
  tipo CHAR(1) NOT NULL CHECK (tipo IN ('p', 'v')), -- 'p': percentual, 'v': valor fixo
  valor DECIMAL(10, 2) NOT NULL,
  valor_minimo_pedido DECIMAL(10, 2) DEFAULT 0, -- Valor mínimo do pedido para usar o cupom
  validade_inicio TIMESTAMP, -- Data de início da validade
  validade_fim TIMESTAMP, -- Data de fim da validade
  uso_maximo INTEGER, -- Número máximo de vezes que o cupom pode ser usado no total
  uso_maximo_por_usuario INTEGER DEFAULT 1, -- Máximo de usos por usuário
  uso_atual INTEGER DEFAULT 0,
  ativo BOOLEAN DEFAULT TRUE,
  descricao TEXT, -- Descrição do cupom
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por INTEGER,
  atualizado_por INTEGER
);

-- Tabela para registrar o uso de cupons por usuários
CREATE TABLE IF NOT EXISTS cupom_usado (
  id SERIAL PRIMARY KEY,
  cupom_id INTEGER REFERENCES cupom(id) NOT NULL,
  usuario_id INTEGER REFERENCES usuarios(id),
  venda_id INTEGER REFERENCES vendas(id), -- Referência à venda onde foi usado
  valor_desconto_aplicado DECIMAL(10, 2) NOT NULL, -- Valor real do desconto aplicado
  data_uso TIMESTAMP DEFAULT NOW(),
  UNIQUE (cupom_id, usuario_id, venda_id) -- Garante rastreabilidade completa
);

-- =====================================================
-- TABELAS DE VENDAS E PEDIDOS
-- =====================================================

-- Tabela de Vendas (Pedidos)
CREATE TABLE IF NOT EXISTS vendas (
  id SERIAL PRIMARY KEY,
  codigo_pedido VARCHAR(50) UNIQUE NOT NULL,
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
  data_venda TIMESTAMP DEFAULT NOW(),
  valor_total DECIMAL(10, 2) NOT NULL,
  valor_frete DECIMAL(10, 2) DEFAULT 0,
  valor_desconto DECIMAL(10, 2) DEFAULT 0,
  valor_subtotal DECIMAL(10, 2) NOT NULL, -- Subtotal antes de frete e desconto
  cupom_id INTEGER REFERENCES cupom(id), -- Cupom aplicado (se houver)
  
  -- Dados de Endereço (snapshot para auditoria)
  endereco_entrega_id INTEGER REFERENCES enderecos(id) ON DELETE SET NULL,
  nome_recebedor VARCHAR(255),
  rua_entrega VARCHAR(255) NOT NULL,
  numero_entrega VARCHAR(50) NOT NULL,
  complemento_entrega VARCHAR(255),
  bairro_entrega VARCHAR(255) NOT NULL,
  cidade_entrega VARCHAR(255) NOT NULL,
  estado_entrega CHAR(2) NOT NULL,
  cep_entrega VARCHAR(10) NOT NULL,
  telefone_entrega VARCHAR(20),
  email_entrega VARCHAR(255),
  
  -- Status de Pedido
  status_pedido VARCHAR(20) NOT NULL DEFAULT 'pendente_pagamento' CHECK (status_pedido IN (
    'pendente', 
    'pendente_pagamento',
    'processando_envio', 
    'enviado', 
    'entregue', 
    'cancelado_pelo_cliente', 
    'cancelado_pelo_vendedor',
    'devolvido',
    'reembolsado'
  )),
  
  -- Informações de Auditoria e Segurança
  cliente_ip VARCHAR(45),
  user_agent TEXT,
  origem VARCHAR(50) DEFAULT 'web', -- 'web', 'mobile', 'api'
  
  -- Informações de Fulfillment
  data_envio TIMESTAMP, -- Quando foi enviado
  data_entrega_estimada DATE, -- Data estimada de entrega
  data_entrega_real TIMESTAMP, -- Data real de entrega
  observacoes TEXT, -- Observações internas do pedido
  observacoes_cliente TEXT, -- Observações do cliente
  
  -- Campos para operação diária
  prioridade INTEGER DEFAULT 0, -- 0=normal, 1=alta, 2=urgente
  responsavel_id INTEGER REFERENCES usuarios(id), -- Admin responsável pelo pedido
  
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para detalhar os itens de cada venda
CREATE TABLE IF NOT EXISTS itens_venda (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
  produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL,
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  preco_unitario DECIMAL(10, 2) NOT NULL,
  subtotal DECIMAL(10, 2) NOT NULL,
  
  -- Snapshot do Produto (para histórico imutável)
  nome_produto_snapshot VARCHAR(255) NOT NULL,
  sku_produto_snapshot VARCHAR(50),
  detalhes_produto_snapshot JSONB, -- Detalhes completos do produto no momento da venda
  
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para gerenciar pedidos com token público
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
    public_token UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'CRIADO' CHECK (status IN (
        'CRIADO', 
        'PENDENTE', 
        'PAGO', 
        'APROVADO', 
        'CANCELADO', 
        'EXPIRADO', 
        'NA TRANSPORTADORA', 
        'ENTREGUE'
    )),
    valor DECIMAL(10, 2) NOT NULL,
    token_expires_at TIMESTAMP, -- Quando o token expira (opcional)
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- TABELAS DE PAGAMENTOS
-- =====================================================

-- Tabela de Pagamentos
CREATE TABLE IF NOT EXISTS pagamentos (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
  
  pagbank_transaction_id VARCHAR(100) UNIQUE,
  pagbank_order_id VARCHAR(100),
  
  forma_pagamento_tipo VARCHAR(50) NOT NULL CHECK (forma_pagamento_tipo IN ('CREDIT_CARD', 'PIX', 'BOLETO')),
  bandeira_cartao VARCHAR(50),
  parcelas INTEGER DEFAULT 1,
  valor_parcela DECIMAL(10, 2), -- Valor de cada parcela
  
  valor_pago DECIMAL(10, 2) NOT NULL,
  valor_original DECIMAL(10, 2), -- Valor original antes de qualquer ajuste
  
  -- Status do Pagamento
  status_pagamento VARCHAR(50) NOT NULL DEFAULT 'PENDING' CHECK (status_pagamento IN (
    'PENDING', 
    'AUTHORIZED', 
    'PAID', 
    'WAITING', 
    'DECLINED', 
    'REFUNDED', 
    'CHARGEBACK',
    'CANCELLED',
    'EXPIRED'
  )),
  status_detalhe_pagamento VARCHAR(100),
  
  -- Dados específicos por tipo de pagamento
  pagbank_qrcode_link TEXT,
  pagbank_qrcode_image TEXT,
  pagbank_qrcode_text TEXT, -- Código PIX completo
  pagbank_boleto_link TEXT,
  pagbank_barcode_data TEXT,
  pagbank_boleto_expires_at TIMESTAMP,
  
  -- Informações de cartão (últimos dígitos, se disponível)
  cartao_ultimos_digitos VARCHAR(4),
  cartao_primeiros_digitos VARCHAR(6),
  
  -- Auditoria
  json_resposta_api JSONB,
  tentativas INTEGER DEFAULT 1, -- Número de tentativas de pagamento
  
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  pago_em TIMESTAMP -- Quando foi pago
);

-- Tabela para histórico de alterações de status de pagamento
CREATE TABLE IF NOT EXISTS pagamento_status_historico (
  id SERIAL PRIMARY KEY,
  pagamento_id INTEGER REFERENCES pagamentos(id) ON DELETE CASCADE,
  status_anterior VARCHAR(50),
  status_novo VARCHAR(50) NOT NULL,
  motivo TEXT, -- Motivo da mudança de status
  origem VARCHAR(50) DEFAULT 'sistema', -- 'sistema', 'webhook', 'admin', 'api'
  dados_adicionais JSONB,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- TABELAS DE CARRINHO
-- =====================================================

-- Tabela para armazenar os carrinhos dos usuários/sessões
CREATE TABLE IF NOT EXISTS carrinhos (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
  session_id VARCHAR(255) UNIQUE,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  expira_em TIMESTAMP, -- Quando o carrinho expira (opcional)
  UNIQUE (usuario_id)
);

-- Tabela para os itens dentro de cada carrinho
CREATE TABLE IF NOT EXISTS carrinho_itens (
  id SERIAL PRIMARY KEY,
  carrinho_id INTEGER REFERENCES carrinhos(id) ON DELETE CASCADE,
  produto_id INTEGER REFERENCES produtos(id) ON DELETE RESTRICT,
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  preco_unitario_no_momento DECIMAL(10, 2) NOT NULL,
  adicionado_em TIMESTAMP DEFAULT NOW(),
  UNIQUE (carrinho_id, produto_id)
);

-- =====================================================
-- TABELAS DE FRETE E ETIQUETAS
-- =====================================================

-- Tabela para armazenar informações das etiquetas de frete
CREATE TABLE IF NOT EXISTS etiquetas_frete (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
  codigo_pedido VARCHAR(50) REFERENCES vendas(codigo_pedido),
  
  -- Dados da Etiqueta do Melhor Envio
  melhor_envio_shipment_id INTEGER,
  melhor_envio_protocol VARCHAR(100),
  melhor_envio_service_id INTEGER,
  melhor_envio_service_name VARCHAR(100),
  
  -- Status da Etiqueta
  status_etiqueta VARCHAR(50) NOT NULL DEFAULT 'pendente' CHECK (
    status_etiqueta IN (
      'pendente',
      'criada',
      'paga',
      'impressa',
      'cancelada',
      'erro',
      'em_transito',
      'entregue'
    )
  ),
  
  -- Informações do Transportador
  transportadora_nome VARCHAR(100),
  transportadora_codigo VARCHAR(50),
  
  -- Dados do Envio (snapshot)
  cep_origem VARCHAR(10) NOT NULL,
  cep_destino VARCHAR(10) NOT NULL,
  peso_total DECIMAL(8, 3),
  valor_frete DECIMAL(10, 2),
  dimensoes JSONB,
  
  -- URL e dados da etiqueta
  url_etiqueta TEXT,
  url_rastreamento TEXT,
  codigo_rastreamento VARCHAR(100),
  
  -- Dados JSON da resposta da API
  dados_etiqueta_json JSONB,
  
  -- Informações de erro
  erro_mensagem TEXT,
  erro_detalhes JSONB,
  
  -- Timestamps
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  paga_em TIMESTAMP,
  impressa_em TIMESTAMP,
  enviada_em TIMESTAMP, -- Quando foi enviada
  entregue_em TIMESTAMP -- Quando foi entregue
);

-- =====================================================
-- TABELAS DE AUDITORIA E LOGS
-- =====================================================

-- Tabela para logs de auditoria (alterações em tabelas importantes)
CREATE TABLE IF NOT EXISTS auditoria_logs (
  id SERIAL PRIMARY KEY,
  tabela_afetada VARCHAR(100) NOT NULL,
  registro_id INTEGER NOT NULL,
  acao VARCHAR(10) NOT NULL CHECK (acao IN ('INSERT', 'UPDATE', 'DELETE')),
  dados_anteriores JSONB,
  dados_novos JSONB,
  usuario_id INTEGER REFERENCES usuarios(id),
  ip_address VARCHAR(45),
  user_agent TEXT,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para logs de ações administrativas
CREATE TABLE IF NOT EXISTS admin_logs (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER REFERENCES usuarios(id) NOT NULL,
  acao VARCHAR(100) NOT NULL, -- Ex: 'criar_produto', 'atualizar_estoque', 'cancelar_pedido'
  entidade_tipo VARCHAR(50), -- Tipo da entidade afetada: 'produto', 'pedido', 'usuario', etc.
  entidade_id INTEGER, -- ID da entidade afetada
  descricao TEXT, -- Descrição da ação
  dados_anteriores JSONB,
  dados_novos JSONB,
  ip_address VARCHAR(45),
  user_agent TEXT,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para histórico de alterações de status de pedidos
CREATE TABLE IF NOT EXISTS venda_status_historico (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
  status_anterior VARCHAR(20),
  status_novo VARCHAR(20) NOT NULL,
  motivo TEXT,
  observacoes TEXT,
  usuario_id INTEGER REFERENCES usuarios(id), -- Quem alterou
  origem VARCHAR(50) DEFAULT 'sistema', -- 'sistema', 'admin', 'webhook', 'cliente'
  criado_em TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- TABELAS DE CONFIGURAÇÕES E OPERAÇÃO
-- =====================================================

-- Tabela para configurações do sistema
CREATE TABLE IF NOT EXISTS configuracoes (
  id SERIAL PRIMARY KEY,
  chave VARCHAR(100) UNIQUE NOT NULL,
  valor TEXT,
  tipo VARCHAR(20) DEFAULT 'string' CHECK (tipo IN ('string', 'number', 'boolean', 'json')),
  descricao TEXT,
  categoria VARCHAR(50), -- 'geral', 'pagamento', 'frete', 'email', etc.
  editavel BOOLEAN DEFAULT TRUE, -- Se pode ser editado pelo admin
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  atualizado_por INTEGER REFERENCES usuarios(id)
);

-- Tabela para notificações do sistema
CREATE TABLE IF NOT EXISTS notificacoes (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
  tipo VARCHAR(50) NOT NULL, -- 'pedido', 'pagamento', 'envio', 'sistema'
  titulo VARCHAR(255) NOT NULL,
  mensagem TEXT NOT NULL,
  link VARCHAR(500), -- Link relacionado à notificação
  lida BOOLEAN DEFAULT FALSE,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para métricas e analytics (para dashboard)
CREATE TABLE IF NOT EXISTS metricas_diarias (
  id SERIAL PRIMARY KEY,
  data DATE NOT NULL UNIQUE,
  total_vendas INTEGER DEFAULT 0,
  total_receita DECIMAL(10, 2) DEFAULT 0,
  total_pedidos INTEGER DEFAULT 0,
  total_produtos_vendidos INTEGER DEFAULT 0,
  total_usuarios_novos INTEGER DEFAULT 0,
  ticket_medio DECIMAL(10, 2) DEFAULT 0,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- ÍNDICES PARA OTIMIZAÇÃO
-- =====================================================

-- Índices para usuários
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios (email);
CREATE INDEX IF NOT EXISTS idx_usuarios_firebase_uid ON usuarios (firebase_uid);
CREATE INDEX IF NOT EXISTS idx_usuarios_role ON usuarios (role);
CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios (ativo);
CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_login ON usuarios (ultimo_login);

-- Índices para vendas
CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_vendas_codigo_pedido ON vendas (codigo_pedido);
CREATE INDEX IF NOT EXISTS idx_vendas_status_pedido ON vendas (status_pedido);
CREATE INDEX IF NOT EXISTS idx_vendas_data_venda ON vendas (data_venda);
CREATE INDEX IF NOT EXISTS idx_vendas_responsavel_id ON vendas (responsavel_id);
CREATE INDEX IF NOT EXISTS idx_vendas_cupom_id ON vendas (cupom_id);

-- Índices para itens de venda
CREATE INDEX IF NOT EXISTS idx_itens_venda_venda_id ON itens_venda (venda_id);
CREATE INDEX IF NOT EXISTS idx_itens_venda_produto_id ON itens_venda (produto_id);

-- Índices para produtos
CREATE INDEX IF NOT EXISTS idx_produtos_sku ON produtos (codigo_sku);
CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos (ativo);
CREATE INDEX IF NOT EXISTS idx_produtos_estoque ON produtos (estoque);
CREATE INDEX IF NOT EXISTS idx_produtos_nome_produto_id ON produtos (nome_produto_id);

-- Índices para nome_produto
CREATE INDEX IF NOT EXISTS idx_nome_produto_categoria_id ON nome_produto (categoria_id);
CREATE INDEX IF NOT EXISTS idx_nome_produto_ativo ON nome_produto (ativo);
CREATE INDEX IF NOT EXISTS idx_nome_produto_slug ON nome_produto (slug);

-- Índices para orders
CREATE INDEX IF NOT EXISTS idx_orders_public_token ON orders (public_token);
CREATE INDEX IF NOT EXISTS idx_orders_venda_id ON orders (venda_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_criado_em ON orders (criado_em);

-- Índices para pagamentos
CREATE INDEX IF NOT EXISTS idx_pagamentos_venda_id ON pagamentos (venda_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_transaction_id ON pagamentos (pagbank_transaction_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_status ON pagamentos (status_pagamento);
CREATE INDEX IF NOT EXISTS idx_pagamentos_criado_em ON pagamentos (criado_em);

-- Índices para etiquetas
CREATE INDEX IF NOT EXISTS idx_etiquetas_venda_id ON etiquetas_frete (venda_id);
CREATE INDEX IF NOT EXISTS idx_etiquetas_codigo_pedido ON etiquetas_frete (codigo_pedido);
CREATE INDEX IF NOT EXISTS idx_etiquetas_status ON etiquetas_frete (status_etiqueta);
CREATE INDEX IF NOT EXISTS idx_etiquetas_protocol ON etiquetas_frete (melhor_envio_protocol);
CREATE INDEX IF NOT EXISTS idx_etiquetas_codigo_rastreamento ON etiquetas_frete (codigo_rastreamento);

-- Índices para auditoria
CREATE INDEX IF NOT EXISTS idx_auditoria_tabela ON auditoria_logs (tabela_afetada);
CREATE INDEX IF NOT EXISTS idx_auditoria_registro_id ON auditoria_logs (registro_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_id ON auditoria_logs (usuario_id);
CREATE INDEX IF NOT EXISTS idx_auditoria_criado_em ON auditoria_logs (criado_em);

-- Índices para admin_logs
CREATE INDEX IF NOT EXISTS idx_admin_logs_usuario_id ON admin_logs (usuario_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_acao ON admin_logs (acao);
CREATE INDEX IF NOT EXISTS idx_admin_logs_entidade ON admin_logs (entidade_tipo, entidade_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_criado_em ON admin_logs (criado_em);

-- Índices para histórico
CREATE INDEX IF NOT EXISTS idx_venda_status_historico_venda_id ON venda_status_historico (venda_id);
CREATE INDEX IF NOT EXISTS idx_pagamento_status_historico_pagamento_id ON pagamento_status_historico (pagamento_id);

-- Índices para notificações
CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario_id ON notificacoes (usuario_id);
CREATE INDEX IF NOT EXISTS idx_notificacoes_lida ON notificacoes (lida);
CREATE INDEX IF NOT EXISTS idx_notificacoes_criado_em ON notificacoes (criado_em);

-- =====================================================
-- TRIGGERS PARA ATUALIZAÇÃO AUTOMÁTICA DE TIMESTAMPS
-- =====================================================

DROP TRIGGER IF EXISTS trg_categorias_update_timestamp ON categorias;
CREATE TRIGGER trg_categorias_update_timestamp BEFORE UPDATE ON categorias FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_usuarios_update_timestamp ON usuarios;
CREATE TRIGGER trg_usuarios_update_timestamp BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_enderecos_update_timestamp ON enderecos;
CREATE TRIGGER trg_enderecos_update_timestamp BEFORE UPDATE ON enderecos FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_nome_produto_update_timestamp ON nome_produto;
CREATE TRIGGER trg_nome_produto_update_timestamp BEFORE UPDATE ON nome_produto FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_estampa_update_timestamp ON estampa;
CREATE TRIGGER trg_estampa_update_timestamp BEFORE UPDATE ON estampa FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_tamanho_update_timestamp ON tamanho;
CREATE TRIGGER trg_tamanho_update_timestamp BEFORE UPDATE ON tamanho FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_produtos_update_timestamp ON produtos;
CREATE TRIGGER trg_produtos_update_timestamp BEFORE UPDATE ON produtos FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_imagens_produto_update_timestamp ON imagens_produto;
CREATE TRIGGER trg_imagens_produto_update_timestamp BEFORE UPDATE ON imagens_produto FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_cupom_update_timestamp ON cupom;
CREATE TRIGGER trg_cupom_update_timestamp BEFORE UPDATE ON cupom FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_vendas_update_timestamp ON vendas;
CREATE TRIGGER trg_vendas_update_timestamp BEFORE UPDATE ON vendas FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_itens_venda_update_timestamp ON itens_venda;
CREATE TRIGGER trg_itens_venda_update_timestamp BEFORE UPDATE ON itens_venda FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_pagamentos_update_timestamp ON pagamentos;
CREATE TRIGGER trg_pagamentos_update_timestamp BEFORE UPDATE ON pagamentos FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_carrinhos_update_timestamp ON carrinhos;
CREATE TRIGGER trg_carrinhos_update_timestamp BEFORE UPDATE ON carrinhos FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_carrinho_itens_update_timestamp ON carrinho_itens;
CREATE TRIGGER trg_carrinho_itens_update_timestamp BEFORE UPDATE ON carrinho_itens FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_orders_update_timestamp ON orders;
CREATE TRIGGER trg_orders_update_timestamp BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_etiquetas_update_timestamp ON etiquetas_frete;
CREATE TRIGGER trg_etiquetas_update_timestamp BEFORE UPDATE ON etiquetas_frete FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_configuracoes_update_timestamp ON configuracoes;
CREATE TRIGGER trg_configuracoes_update_timestamp BEFORE UPDATE ON configuracoes FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- =====================================================
-- TRIGGERS PARA HISTÓRICO DE STATUS
-- =====================================================

-- Trigger para histórico de status de vendas
CREATE OR REPLACE FUNCTION log_venda_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status_pedido IS DISTINCT FROM NEW.status_pedido THEN
        INSERT INTO venda_status_historico (
            venda_id,
            status_anterior,
            status_novo,
            usuario_id,
            origem
        ) VALUES (
            NEW.id,
            OLD.status_pedido,
            NEW.status_pedido,
            current_setting('app.user_id', true)::integer,
            current_setting('app.origem', true)
        );
    END IF;
    RETURN NEW;
END;
$$ language plpgsql;

DROP TRIGGER IF EXISTS trg_venda_status_historico ON vendas;
CREATE TRIGGER trg_venda_status_historico
    AFTER UPDATE OF status_pedido ON vendas
    FOR EACH ROW
    EXECUTE FUNCTION log_venda_status_change();

-- Trigger para histórico de status de pagamentos
CREATE OR REPLACE FUNCTION log_pagamento_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status_pagamento IS DISTINCT FROM NEW.status_pagamento THEN
        INSERT INTO pagamento_status_historico (
            pagamento_id,
            status_anterior,
            status_novo,
            origem,
            dados_adicionais
        ) VALUES (
            NEW.id,
            OLD.status_pagamento,
            NEW.status_pagamento,
            current_setting('app.origem', true),
            jsonb_build_object(
                'usuario_id', current_setting('app.user_id', true),
                'ip_address', current_setting('app.ip_address', true)
            )
        );
    END IF;
    RETURN NEW;
END;
$$ language plpgsql;

DROP TRIGGER IF EXISTS trg_pagamento_status_historico ON pagamentos;
CREATE TRIGGER trg_pagamento_status_historico
    AFTER UPDATE OF status_pagamento ON pagamentos
    FOR EACH ROW
    EXECUTE FUNCTION log_pagamento_status_change();

-- =====================================================
-- COMENTÁRIOS PARA DOCUMENTAÇÃO
-- =====================================================

COMMENT ON TABLE usuarios IS 'Usuários do sistema (clientes e administradores)';
COMMENT ON TABLE vendas IS 'Pedidos/vendas do e-commerce';
COMMENT ON TABLE pagamentos IS 'Transações de pagamento via gateway';
COMMENT ON TABLE orders IS 'Pedidos com token público para acesso sem login';
COMMENT ON TABLE etiquetas_frete IS 'Etiquetas de frete criadas via Melhor Envio';
COMMENT ON TABLE auditoria_logs IS 'Logs de auditoria de alterações em tabelas importantes';
COMMENT ON TABLE admin_logs IS 'Logs de ações administrativas';
COMMENT ON TABLE venda_status_historico IS 'Histórico de alterações de status de pedidos';
COMMENT ON TABLE pagamento_status_historico IS 'Histórico de alterações de status de pagamentos';
COMMENT ON TABLE configuracoes IS 'Configurações do sistema editáveis pelo admin';
COMMENT ON TABLE notificacoes IS 'Notificações para usuários';
COMMENT ON TABLE metricas_diarias IS 'Métricas diárias para dashboard e analytics';
