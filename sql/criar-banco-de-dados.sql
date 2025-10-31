-- Garante que estamos no schema público padrão
SET search_path TO public;

-- Tabela para gerenciar categorias de produtos e estampas
CREATE TABLE IF NOT EXISTS categorias (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(50) UNIQUE NOT NULL, -- Nome da categoria (ex: "Camisetas", "Acessórios", "Geométricas")
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para armazenar informações de usuários (clientes e futuros admins)
CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  firebase_uid VARCHAR(128) UNIQUE NOT NULL, -- ID único de autenticação do Firebase
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  genero CHAR(1) DEFAULT 'u' CHECK (genero IN ('m', 'f', 'u')), -- 'm': masculino, 'f': feminino, 'u': não informado
  cpf CHAR(11) UNIQUE, -- CPF do usuário
  telefone VARCHAR(15), -- Telefone de contato
  data_nascimento DATE, -- Data de nascimento
  criado_em TIMESTAMP DEFAULT NOW(), -- Data e hora de criação do registro
  atualizado_em TIMESTAMP DEFAULT NOW(),
  imagem_url VARCHAR(2000), -- URL da foto de perfil
  -- Role ou permissão do usuário (útil para administradores)
  role VARCHAR(20) DEFAULT 'user' NOT NULL CHECK (role IN ('user', 'admin')) -- Para gerenciar permissões no seu Flask/Admin
);

-- Tabela para listar endereços de entrega dos usuários
CREATE TABLE IF NOT EXISTS enderecos (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE, -- Chave estrangeira para o ID do usuário
  nome_endereco VARCHAR(50) NOT NULL, -- Nome dado ao endereço (ex: "Minha Casa", "Trabalho")
  cep CHAR(8) NOT NULL, -- Código de Endereçamento Postal (8 dígitos)
  rua VARCHAR(255) NOT NULL,
  numero VARCHAR(20) NOT NULL,
  complemento VARCHAR(100), -- Complemento (ex: "Apto 101")
  bairro VARCHAR(100) NOT NULL,
  cidade VARCHAR(100) NOT NULL,
  estado CHAR(2) NOT NULL, -- Sigla do estado (ex: "SP")
  referencia VARCHAR(255), -- Ponto de referência para facilitar a entrega
  is_default BOOLEAN DEFAULT FALSE, -- Indica se é o endereço padrão do usuário
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para definir nomes e descrições base dos produtos (ex: "Camiseta", "Caneca")
CREATE TABLE IF NOT EXISTS nome_produto (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) UNIQUE NOT NULL, -- Nome genérico do produto (ex: "Camiseta Básica")
  descricao TEXT, -- Descrição detalhada do nome do produto
  categoria_id INTEGER REFERENCES categorias(id) NOT NULL, -- Relacionamento com a tabela de categorias
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para cadastrar as estampas disponíveis (ex: "Geométrica Azul", "Coração Vermelho")
CREATE TABLE IF NOT EXISTS estampa (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(100) UNIQUE NOT NULL, -- Nome da estampa
  descricao TEXT, -- Descrição da estampa
  imagem_url VARCHAR(2000) NOT NULL, -- URL da imagem da estampa
  categoria_id INTEGER REFERENCES categorias(id) NOT NULL, -- Relacionamento com a tabela de categorias
  sexo CHAR(1) DEFAULT 'u' CHECK (sexo IN ('m', 'f', 'u')), -- Sexo para qual a estampa é mais indicada
  custo_por_metro DECIMAL(10, 2) NOT NULL, -- Custo de produção por metro (ou unidade, se aplicável)
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para listar os tamanhos disponíveis (ex: "P", "M", "G", "GG", "Único")
CREATE TABLE IF NOT EXISTS tamanho (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(20) UNIQUE NOT NULL, -- Nome do tamanho
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para controlar as variações de produtos em estoque
-- Uma "variacao de produto" é uma combinação específica de nome_produto, estampa e tamanho.
CREATE TABLE IF NOT EXISTS produtos (
  id SERIAL PRIMARY KEY,
  nome_produto_id INTEGER REFERENCES nome_produto(id) ON DELETE CASCADE, -- Referência ao nome base do produto
  estampa_id INTEGER REFERENCES estampa(id) ON DELETE CASCADE, -- Referência à estampa aplicada
  tamanho_id INTEGER REFERENCES tamanho(id) ON DELETE CASCADE, -- Referência ao tamanho
  UNIQUE (nome_produto_id, estampa_id, tamanho_id), -- Garante unicidade da variação
  custo DECIMAL(10, 2) NOT NULL, -- Custo de produção desta variação específica
  preco_venda DECIMAL(10, 2) NOT NULL, -- Preço de venda para esta variação
  estoque INTEGER NOT NULL DEFAULT 0, -- Quantidade em estoque
  codigo_sku VARCHAR(50) UNIQUE NOT NULL, -- Código SKU único para esta variação (ex: CAMISETAPRETA-GEOMETRICA-M)
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS imagens_produto (
  id SERIAL PRIMARY KEY,
  produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE, -- Chave estrangeira para a tabela 'produtos'
  url VARCHAR(2000) NOT NULL, -- A URL da imagem no Firebase Cloud Storage
  ordem INTEGER DEFAULT 0, -- Para definir a ordem de exibição das imagens (ex: 0=principal, 1=secundária, etc.)
  descricao VARCHAR(255), -- Texto alternativo (alt text) para SEO e acessibilidade
  is_thumbnail BOOLEAN DEFAULT FALSE, -- Indica se esta é a imagem principal/miniatura do produto
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para gerenciar cupons de desconto
CREATE TABLE IF NOT EXISTS cupom (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(20) UNIQUE NOT NULL, -- Código do cupom (ex: "VERAO2024")
  tipo CHAR(1) NOT NULL CHECK (tipo IN ('p', 'v')), -- 'p': percentual, 'v': valor fixo
  valor DECIMAL(10, 2) NOT NULL, -- Valor do desconto (ex: 10.00 para 10% ou R$10,00)
  validade DATE, -- Data de validade do cupom
  uso_maximo INTEGER, -- Número máximo de vezes que o cupom pode ser usado no total
  uso_atual INTEGER DEFAULT 0, -- Contador de usos atuais
  ativo BOOLEAN DEFAULT TRUE, -- Status do cupom (ativo/inativo)
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para registrar o uso de cupons por usuários
CREATE TABLE IF NOT EXISTS cupom_usado (
  id SERIAL PRIMARY KEY,
  cupom_id INTEGER REFERENCES cupom(id) NOT NULL, -- Referência ao cupom usado
  usuario_id INTEGER REFERENCES usuarios(id) NOT NULL, -- Referência ao usuário que usou o cupom
  UNIQUE (cupom_id, usuario_id), -- Garante que um usuário só pode usar um cupom uma vez
  data_uso TIMESTAMP DEFAULT NOW() -- Data e hora que o cupom foi usado
);

-- Tabela de Vendas (Pedidos)
CREATE TABLE IF NOT EXISTS vendas (
  id SERIAL PRIMARY KEY,
  codigo_pedido VARCHAR(50) UNIQUE NOT NULL, -- Código único do pedido (visível ao usuário/para controle)
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL, -- Cliente que fez a compra (NULL para usuário não logado)
  data_venda TIMESTAMP DEFAULT NOW(), -- Data e hora da venda
  valor_total DECIMAL(10, 2) NOT NULL, -- Valor total da venda

  -- Dados de Endereço (para auditoria e histórico, mesmo que o endereço original seja alterado)
  endereco_entrega_id INTEGER REFERENCES enderecos(id) ON DELETE SET NULL, -- Endereço de entrega para este pedido (NULL se o endereço for gravado diretamente na venda)
  nome_recebedor VARCHAR(255),
  rua_entrega VARCHAR(255) NOT NULL,
  numero_entrega VARCHAR(50) NOT NULL,
  complemento_entrega VARCHAR(255),
  bairro_entrega VARCHAR(255) NOT NULL,
  cidade_entrega VARCHAR(255) NOT NULL,
  estado_entrega CHAR(2) NOT NULL,
  cep_entrega VARCHAR(10) NOT NULL,

  -- Status de Pedido (Logística / Fulfillment)
  status_pedido VARCHAR(20) NOT NULL CHECK (status_pedido IN ('pendente', 'processando_envio', 'enviado', 'entregue', 'cancelado_pelo_cliente', 'cancelado_pelo_vendedor')),
  
  -- Informações de Auditoria
  cliente_ip VARCHAR(45), -- IP do cliente no momento da compra (para segurança/fraude)
  user_agent TEXT,        -- User-Agent do navegador/dispositivo do cliente
  
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para detalhar os itens de cada venda
CREATE TABLE IF NOT EXISTS itens_venda (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE, -- Referência à venda à qual o item pertence
  produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL, -- Referência ao ID do produto original
  quantidade INTEGER NOT NULL,
  preco_unitario DECIMAL(10, 2) NOT NULL, -- Preço unitário do produto NO MOMENTO DA VENDA
  subtotal DECIMAL(10, 2) NOT NULL, -- Subtotal deste item (quantidade * preco_unitario)
  
  -- Snapshot do Produto (CRÍTICO para histórico e auditoria)
  nome_produto_snapshot VARCHAR(255) NOT NULL,
  sku_produto_snapshot VARCHAR(50),
  detalhes_produto_snapshot JSONB, 

  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- NOVA TABELA: Pagamentos (para rastrear transações com Gateway)
CREATE TABLE IF NOT EXISTS pagamentos (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE, -- Venda a qual este pagamento pertence
  
  pagbank_transaction_id VARCHAR(100) UNIQUE, -- ID da transação no PagBank (CRÍTICO para webhooks)
  pagbank_order_id VARCHAR(100), -- Opcional: ID do pedido no PagBank se diferente do transaction_id
  
  forma_pagamento_tipo VARCHAR(50) NOT NULL CHECK (forma_pagamento_tipo IN ('CREDIT_CARD', 'PIX', 'BOLETO')), -- Tipo genérico de pagamento PagBank
  bandeira_cartao VARCHAR(50), -- Se for cartão de crédito (VISA, MASTERCARD, etc.)
  parcelas INTEGER DEFAULT 1, -- Número de parcelas (para cartão de crédito)
  
  valor_pago DECIMAL(10, 2) NOT NULL, -- Valor real que foi enviado ao PagBank para esta tentativa
  
  -- Status do Pagamento (diretamente do PagBank)
  status_pagamento VARCHAR(50) NOT NULL CHECK (status_pagamento IN ('PENDING', 'AUTHORIZED', 'PAID', 'DECLINED', 'REFUNDED', 'CHARGEBACK')),
  status_detalhe_pagamento VARCHAR(100), -- Detalhes adicionais do status PagBank (ex: 'PAID', 'DECLINED_BY_ANTI_FRAUD')
  
  pagbank_qrcode_link TEXT, -- Link para QR Code (se PIX)
  pagbank_qrcode_image TEXT, -- Dados da imagem do QR Code (se PIX)
  pagbank_boleto_link TEXT, -- Link para boleto (se BOLETO)
  pagbank_barcode_data TEXT, -- Código de barras do boleto (se BOLETO)
  
  json_resposta_api JSONB, -- Opcional: Armazenar a resposta JSON completa da API do PagBank para depuração
  
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Tabela para armazenar os carrinhos dos usuários/sessões
CREATE TABLE IF NOT EXISTS carrinhos (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE, -- referencia usuários.id (INTEGER)
  session_id VARCHAR(255) UNIQUE, -- ID de sessão anônima (UUID do localStorage)
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  UNIQUE (usuario_id)
);

-- Tabela para os itens dentro de cada carrinho
CREATE TABLE IF NOT EXISTS carrinho_itens (
  id SERIAL PRIMARY KEY,
  carrinho_id INTEGER REFERENCES carrinhos(id) ON DELETE CASCADE,
  produto_id INTEGER REFERENCES produtos(id) ON DELETE RESTRICT, -- referencia produtos.id (INTEGER)
  quantidade INTEGER NOT NULL CHECK (quantidade > 0),
  preco_unitario_no_momento DECIMAL(10, 2) NOT NULL,
  adicionado_em TIMESTAMP DEFAULT NOW(),
  UNIQUE (carrinho_id, produto_id) -- Impede duplicatas no mesmo carrinho
);

-- Índices para otimização de busca
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios (email);
CREATE INDEX IF NOT EXISTS idx_usuarios_firebase_uid ON usuarios (firebase_uid);
CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_vendas_codigo_pedido ON vendas (codigo_pedido);
CREATE INDEX IF NOT EXISTS idx_itens_venda_venda_id ON itens_venda (venda_id);
CREATE INDEX IF NOT EXISTS idx_produtos_sku ON produtos (codigo_sku);

-- Função para atualizar timestamps
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.atualizado_em = NOW();
   RETURN NEW;
END;
$$ language plpgsql;

-- Criação dos gatilhos de forma idempotente
DROP TRIGGER IF EXISTS trg_categorias_update_timestamp ON categorias;
CREATE TRIGGER trg_categorias_update_timestamp BEFORE UPDATE ON categorias FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_usuarios_update_timestamp ON usuarios;
CREATE TRIGGER trg_usuarios_update_timestamp BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_enderecos_update_timestamp ON enderecos;
CREATE TRIGGER trg_enderecos_update_timestamp BEFORE UPDATE ON enderecos FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_nome_produto_update_timestamp ON nome_produto;
CREATE TRIGGER trg_nome_produto_update_timestamp BEFORE UPDATE ON nome_produto FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_estampa_update_timestamp ON estampa;
CREATE TRIGGER trg_estampa_update_timestamp BEFORE UPDATE ON estampa FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_tamanho_update_timestamp ON tamanho;
CREATE TRIGGER trg_tamanho_update_timestamp BEFORE UPDATE ON tamanho FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_produtos_update_timestamp ON produtos;
CREATE TRIGGER trg_produtos_update_timestamp BEFORE UPDATE ON produtos FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_imagens_produto_update_timestamp ON imagens_produto;
CREATE TRIGGER trg_imagens_produto_update_timestamp BEFORE UPDATE ON imagens_produto FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_cupom_update_timestamp ON cupom;
CREATE TRIGGER trg_cupom_update_timestamp BEFORE UPDATE ON cupom FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_vendas_update_timestamp ON vendas;
CREATE TRIGGER trg_vendas_update_timestamp BEFORE UPDATE ON vendas FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_itens_venda_update_timestamp ON itens_venda;
CREATE TRIGGER trg_itens_venda_update_timestamp BEFORE UPDATE ON itens_venda FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_pagamentos_update_timestamp ON pagamentos;
CREATE TRIGGER trg_pagamentos_update_timestamp BEFORE UPDATE ON pagamentos FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_carrinhos_update_timestamp ON carrinhos;
CREATE TRIGGER trg_carrinhos_update_timestamp BEFORE UPDATE ON carrinhos FOR EACH ROW EXECUTE PROCEDURE update_timestamp();

DROP TRIGGER IF EXISTS trg_carrinho_itens_update_timestamp ON carrinho_itens;
CREATE TRIGGER trg_carrinho_itens_update_timestamp BEFORE UPDATE ON carrinho_itens FOR EACH ROW EXECUTE PROCEDURE update_timestamp();