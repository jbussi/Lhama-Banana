-- Tabela para armazenar informações das etiquetas de frete (Melhor Envio)
CREATE TABLE IF NOT EXISTS etiquetas_frete (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE, -- Pedido associado
  codigo_pedido VARCHAR(50) REFERENCES vendas(codigo_pedido), -- Referência adicional ao pedido
  
  -- Dados da Etiqueta do Melhor Envio
  melhor_envio_shipment_id INTEGER, -- ID do envio no Melhor Envio
  melhor_envio_protocol VARCHAR(100), -- Protocolo/número de rastreamento
  melhor_envio_service_id INTEGER, -- ID do serviço escolhido (1=PAC, 2=SEDEX, etc)
  melhor_envio_service_name VARCHAR(100), -- Nome do serviço (PAC, SEDEX, Jadlog, etc)
  
  -- Status da Etiqueta
  status_etiqueta VARCHAR(50) NOT NULL DEFAULT 'pendente' CHECK (
    status_etiqueta IN (
      'pendente',           -- Aguardando criação da etiqueta
      'criada',             -- Etiqueta criada mas não paga
      'paga',               -- Etiqueta paga e pronta para impressão
      'impressa',           -- Etiqueta impressa
      'cancelada',          -- Etiqueta cancelada
      'erro'                -- Erro ao criar etiqueta
    )
  ),
  
  -- Informações do Transportador
  transportadora_nome VARCHAR(100), -- Nome da transportadora (Correios, Jadlog, etc)
  transportadora_codigo VARCHAR(50), -- Código da transportadora no Melhor Envio
  
  -- Dados do Envio (snapshot no momento da criação)
  cep_origem VARCHAR(10) NOT NULL,
  cep_destino VARCHAR(10) NOT NULL,
  peso_total DECIMAL(8, 3), -- Peso em kg
  valor_frete DECIMAL(10, 2), -- Valor do frete
  dimensoes JSONB, -- {largura, altura, comprimento} em cm
  
  -- URL e dados da etiqueta
  url_etiqueta TEXT, -- URL para visualizar/baixar etiqueta
  url_rastreamento TEXT, -- URL de rastreamento do pedido
  codigo_rastreamento VARCHAR(100), -- Código de rastreamento
  
  -- Dados JSON da resposta da API (para debug/auditoria)
  dados_etiqueta_json JSONB,
  
  -- Informações de erro (se houver)
  erro_mensagem TEXT,
  erro_detalhes JSONB,
  
  -- Timestamps
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  paga_em TIMESTAMP, -- Quando a etiqueta foi paga
  impressa_em TIMESTAMP -- Quando a etiqueta foi impressa
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_etiquetas_venda_id ON etiquetas_frete (venda_id);
CREATE INDEX IF NOT EXISTS idx_etiquetas_codigo_pedido ON etiquetas_frete (codigo_pedido);
CREATE INDEX IF NOT EXISTS idx_etiquetas_status ON etiquetas_frete (status_etiqueta);
CREATE INDEX IF NOT EXISTS idx_etiquetas_protocol ON etiquetas_frete (melhor_envio_protocol);
CREATE INDEX IF NOT EXISTS idx_etiquetas_codigo_rastreamento ON etiquetas_frete (codigo_rastreamento);

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_etiquetas_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.atualizado_em = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_etiquetas_update_timestamp ON etiquetas_frete;
CREATE TRIGGER trg_etiquetas_update_timestamp 
BEFORE UPDATE ON etiquetas_frete 
FOR EACH ROW 
EXECUTE FUNCTION update_etiquetas_timestamp();

-- Comentários para documentação
COMMENT ON TABLE etiquetas_frete IS 'Armazena informações das etiquetas de frete criadas via Melhor Envio';
COMMENT ON COLUMN etiquetas_frete.melhor_envio_shipment_id IS 'ID único do envio no Melhor Envio';
COMMENT ON COLUMN etiquetas_frete.melhor_envio_protocol IS 'Protocolo/número de rastreamento da etiqueta';
COMMENT ON COLUMN etiquetas_frete.status_etiqueta IS 'Status atual da etiqueta no fluxo de trabalho';
COMMENT ON COLUMN etiquetas_frete.codigo_rastreamento IS 'Código de rastreamento público (ex: código dos Correios)';

