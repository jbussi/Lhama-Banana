-- Tabela para armazenar transportadoras do Bling
-- Usada para preencher dados de transportadora na NF-e
CREATE TABLE IF NOT EXISTS transportadoras_bling (
    id SERIAL PRIMARY KEY,
    bling_id BIGINT UNIQUE NOT NULL,  -- ID do contato no Bling
    nome VARCHAR(255) NOT NULL,
    fantasia VARCHAR(255),
    cnpj VARCHAR(18) UNIQUE NOT NULL,  -- CNPJ sem formatação
    ie VARCHAR(20),  -- Inscrição Estadual
    indicador_ie INTEGER,  -- 1=Contribuinte, 2=Isento, 9=Não Contribuinte
    telefone VARCHAR(50),
    email VARCHAR(255),
    email_nota_fiscal VARCHAR(255),
    
    -- Endereço
    endereco VARCHAR(255),
    numero VARCHAR(50),
    complemento VARCHAR(255),
    bairro VARCHAR(255),
    municipio VARCHAR(255),
    uf CHAR(2),
    cep VARCHAR(10),
    
    -- Dados adicionais
    situacao VARCHAR(1) DEFAULT 'A',  -- A=Ativo, I=Inativo
    tipos_contato JSONB,  -- Array de tipos de contato (ex: [{"id": 123, "descricao": "Transportador"}])
    dados_completos JSONB,  -- Dados completos do Bling para referência
    
    -- Timestamps
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ultima_sincronizacao TIMESTAMP DEFAULT NOW()
);

-- Índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_cnpj ON transportadoras_bling(cnpj);
CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_bling_id ON transportadoras_bling(bling_id);
CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_situacao ON transportadoras_bling(situacao);
CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_nome ON transportadoras_bling(nome);

-- Trigger para atualizar timestamp
CREATE TRIGGER update_transportadoras_bling_timestamp 
BEFORE UPDATE ON transportadoras_bling 
FOR EACH ROW 
EXECUTE FUNCTION update_timestamp();

-- Comentários
COMMENT ON TABLE transportadoras_bling IS 'Transportadoras cadastradas no Bling, sincronizadas automaticamente';
COMMENT ON COLUMN transportadoras_bling.bling_id IS 'ID do contato no Bling';
COMMENT ON COLUMN transportadoras_bling.cnpj IS 'CNPJ sem formatação (apenas números)';
COMMENT ON COLUMN transportadoras_bling.dados_completos IS 'Dados completos retornados pelo Bling (JSON)';
