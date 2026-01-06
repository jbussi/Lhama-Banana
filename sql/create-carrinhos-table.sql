-- Script para criar a tabela carrinhos e carrinho_itens
-- Execute este script se a tabela não existir no banco de dados

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

-- Trigger para atualizar timestamp automaticamente
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.atualizado_em = NOW();
   RETURN NEW;
END;
$$ language plpgsql;

DROP TRIGGER IF EXISTS trg_carrinhos_update_timestamp ON carrinhos;
CREATE TRIGGER trg_carrinhos_update_timestamp 
    BEFORE UPDATE ON carrinhos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS trg_carrinho_itens_update_timestamp ON carrinho_itens;
CREATE TRIGGER trg_carrinho_itens_update_timestamp 
    BEFORE UPDATE ON carrinho_itens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_timestamp();

-- Comentários para documentação
COMMENT ON TABLE carrinhos IS 'Carrinhos de compra dos usuários (logados ou anônimos)';
COMMENT ON TABLE carrinho_itens IS 'Itens dentro de cada carrinho de compra';

