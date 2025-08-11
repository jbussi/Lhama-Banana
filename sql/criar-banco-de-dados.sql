-- Criação do schema
SET search_path TO public;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  firebase_uid VARCHAR(128) UNIQUE NOT NULL,  -- ID do Firebase
  nome VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  genero CHAR(1) DEFAULT 'u' CHECK (genero IN ('m', 'f', 'u')) 
  cpf CHAR(11) UNIQUE,
  telefone VARCHAR(15),
  data_nascimento DATE,
  criado_em TIMESTAMP DEFAULT NOW(),
  usuario_autenticado BOOLEAN DEFAULT FALSE,
  imagem_url VARCHAR(2000)
);

-- Tabela de endereços de entrega
CREATE TABLE IF NOT EXISTS enderecos (
  id SERIAL PRIMARY KEY,
  usuario_uid VARCHAR(128) REFERENCES usuarios(firebase_uid) ON DELETE CASCADE,
  nome VARCHAR(12) NOT NULL,
  rua VARCHAR(255) NOT NULL,
  numero VARCHAR(20) NOT NULL,
  complemento VARCHAR(100) NOT NULL,
  bairro VARCHAR(100) NOT NULL,
  cidade VARCHAR(100) NOT NULL,
  estado VARCHAR(50) NOT NULL,
  cep CHAR(8) NOT NULL,
  criado_em TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nome_produto (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(20) NOT NULL UNIQUE,
  categoria VARCHAR(20) NOT NULL UNIQUE
)

CREATE TABLE IF NOT EXISTS estampa (
  id SERIAL PRIMARY KEY,
  nome VARCHAR(20) NOT NULL UNIQUE,
  categoria VARCHAR(20) NOT NULL UNIQUE,
  sexo CHAR(1) CHECK (sexo IN ('m', 'f', 'u')) NOT NULL
  custo_por_metro DECIMAL(10, 2)
)

CREATE TABLE IF NOT EXISTS tamanho (
  id SERIAL PRIMARY KEY,
  tamanho VARCHAR(10) UNIQUE
)

CREATE TABLE IF NOT EXISTS produtos (
  id SERIAL PRIMARY KEY,
  produto_id INTEGER REFERENCES nome_produto(id) ON DELETE CASCADE,
  estampa_id INTEGER REFERENCES estampa(id) ON DELETE CASCADE,
  tamanho_id INTEGER REFERENCES tamanho(id) ON DELETE CASCADE,
  UNIQUE (produto_id, estampa_id, tamanho_id),
  custo DECIMAL(10, 2) NOT NULL,
  preco_base DECIMAL(10, 2) NOT NULL,
  estoque INTEGER NOT NULL DEFAULT 0,
  imagem_url VARCHAR(2000),
  codigo_sku VARCHAR(20) UNIQUE
)

CREATE TABLE IF NOT EXISTS cupom (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(15) NOT NULL UNIQUE,
  tipo char(1) CHECK (tipo IN ('p', 'v')) NOT NULL,
  valor DECIMAL(4, 2) NOT NULL,
  validade DATE,
  criado_em DATE DEFAULT NOW(),
  uso_maximo INTEGER,
  uso_atual INTEGER DEFAULT 0,
  ativo BOOLEAN DEFAULT FALSE
)

CREATE TABLE IF NOT EXISTS cupom_usado (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(15) REFERENCES cupom(codigo) NOT NULL,
  cpf CHAR(11) REFERENCES usuarios(cpf) NOT NULL,
  UNIQUE (codigo, cpf),
  data_uso DATE NOT NULL
)

-- Tabela de vendas
CREATE TABLE IF NOT EXISTS vendas (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(15) NOT NULL,
  usuario_uid VARCHAR(128) REFERENCES usuarios(firebase_uid) ON DELETE SET NULL,
  data_venda TIMESTAMP DEFAULT NOW(),
  valor_total DECIMAL(10, 2) NOT NULL,
  valor_frete DECIMAL(10, 2) NOT NULL,
  cupom_usado VARCHAR(15) REFERENCES,
  forma_pagamento VARCHAR CHECK (forma_pagamento in ('pix', 'boleto', 'credito1X', 'credito2X', 'credito3X', 'credito4X', 'credito5X', 'credito6X', 'credito7X', 'credito8X', 'credito9X', 'credito10X', 'credito11X', 'credito12X')) NOT NULL,
  status_pedido VARCHAR CHECK (status_pedido in ('pendente', 'pago', 'enviado', 'entregue'), 'cancelado')   
);

CREATE TABLE IF NOT EXISTS itens_venda (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR REFERENCES vendas(codigo) NOT NULL,
  codigo_sku VARCHAR REFERENCES produtos(codigo_sku) NOT NULL,
  quantidade INTEGER NOT NULL,
  preco_base DECIMAL(10, 2) REFERENCES produtos(preco_base),
  subtotal 
)