-- =====================================================
-- Script de Migração: Tabela Notas Fiscais
-- =====================================================
-- Este script cria a tabela notas_fiscais para controle
-- de emissão automática de notas fiscais
-- =====================================================

-- Criar tabela notas_fiscais
CREATE TABLE IF NOT EXISTS notas_fiscais (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
  codigo_pedido VARCHAR(50) REFERENCES vendas(codigo_pedido),
  
  -- Dados da NFe
  numero_nfe VARCHAR(50),
  serie_nfe VARCHAR(10),
  chave_acesso VARCHAR(44),
  
  -- Status da emissão
  status_emissao VARCHAR(50) NOT NULL DEFAULT 'pendente' CHECK (status_emissao IN (
    'pendente',
    'processando',
    'emitida',
    'erro',
    'cancelada'
  )),
  
  -- Resposta da API externa
  api_response JSONB,
  erro_mensagem TEXT,
  
  -- Datas
  data_emissao TIMESTAMP,
  data_cancelamento TIMESTAMP,
  
  -- Timestamps
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_notas_fiscais_venda_id ON notas_fiscais (venda_id);
CREATE INDEX IF NOT EXISTS idx_notas_fiscais_codigo_pedido ON notas_fiscais (codigo_pedido);
CREATE INDEX IF NOT EXISTS idx_notas_fiscais_status ON notas_fiscais (status_emissao);
CREATE INDEX IF NOT EXISTS idx_notas_fiscais_chave_acesso ON notas_fiscais (chave_acesso);
CREATE INDEX IF NOT EXISTS idx_notas_fiscais_numero_nfe ON notas_fiscais (numero_nfe);

-- Criar trigger para atualizar timestamp
DROP TRIGGER IF EXISTS trg_notas_fiscais_update_timestamp ON notas_fiscais;
CREATE TRIGGER trg_notas_fiscais_update_timestamp 
    BEFORE UPDATE ON notas_fiscais 
    FOR EACH ROW 
    EXECUTE FUNCTION update_timestamp();

-- Comentários para documentação
COMMENT ON TABLE notas_fiscais IS 'Controle de emissão de notas fiscais eletrônicas';
COMMENT ON COLUMN notas_fiscais.status_emissao IS 'Status da emissão: pendente, processando, emitida, erro, cancelada';
COMMENT ON COLUMN notas_fiscais.chave_acesso IS 'Chave de acesso da NFe (44 dígitos)';
COMMENT ON COLUMN notas_fiscais.api_response IS 'Resposta completa da API de NFe em formato JSON';



