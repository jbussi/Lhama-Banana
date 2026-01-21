-- Adicionar campos de transportadora na tabela vendas
-- Esses dados são escolhidos no checkout e usados na emissão da NFC-e

ALTER TABLE vendas
ADD COLUMN IF NOT EXISTS transportadora_nome VARCHAR(255),
ADD COLUMN IF NOT EXISTS transportadora_cnpj VARCHAR(18),
ADD COLUMN IF NOT EXISTS transportadora_ie VARCHAR(20),
ADD COLUMN IF NOT EXISTS transportadora_uf CHAR(2),
ADD COLUMN IF NOT EXISTS transportadora_municipio VARCHAR(255),
ADD COLUMN IF NOT EXISTS transportadora_endereco VARCHAR(255),
ADD COLUMN IF NOT EXISTS transportadora_numero VARCHAR(50),
ADD COLUMN IF NOT EXISTS transportadora_complemento VARCHAR(255),
ADD COLUMN IF NOT EXISTS transportadora_bairro VARCHAR(255),
ADD COLUMN IF NOT EXISTS transportadora_cep VARCHAR(10),
ADD COLUMN IF NOT EXISTS melhor_envio_service_id INTEGER,
ADD COLUMN IF NOT EXISTS melhor_envio_service_name VARCHAR(100);

-- Comentários para documentação
COMMENT ON COLUMN vendas.transportadora_nome IS 'Nome da transportadora escolhida no checkout';
COMMENT ON COLUMN vendas.transportadora_cnpj IS 'CNPJ da transportadora';
COMMENT ON COLUMN vendas.transportadora_ie IS 'Inscrição Estadual da transportadora';
COMMENT ON COLUMN vendas.transportadora_uf IS 'UF da transportadora';
COMMENT ON COLUMN vendas.transportadora_municipio IS 'Município da transportadora';
COMMENT ON COLUMN vendas.melhor_envio_service_id IS 'ID do serviço do Melhor Envio escolhido (1=PAC, 2=SEDEX, etc)';
COMMENT ON COLUMN vendas.melhor_envio_service_name IS 'Nome do serviço do Melhor Envio escolhido';
