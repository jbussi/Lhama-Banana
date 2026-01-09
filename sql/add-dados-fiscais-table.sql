-- =====================================================
-- Script de Migração: Tabela Dados Fiscais
-- =====================================================
-- Este script cria a tabela dados_fiscais para armazenar
-- informações fiscais dos usuários (CPF/CNPJ e endereço fiscal)
-- =====================================================

-- Criar tabela dados_fiscais
CREATE TABLE IF NOT EXISTS dados_fiscais (
  id SERIAL PRIMARY KEY,
  usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE UNIQUE NOT NULL,
  tipo VARCHAR(4) NOT NULL CHECK (tipo IN ('CPF', 'CNPJ')),
  cpf_cnpj VARCHAR(18) UNIQUE NOT NULL,
  nome_razao_social VARCHAR(255) NOT NULL,
  inscricao_estadual VARCHAR(20),
  inscricao_municipal VARCHAR(20),
  -- Endereço fiscal completo
  cep VARCHAR(10) NOT NULL,
  rua VARCHAR(255) NOT NULL,
  numero VARCHAR(20) NOT NULL,
  complemento VARCHAR(100),
  bairro VARCHAR(100) NOT NULL,
  cidade VARCHAR(100) NOT NULL,
  estado CHAR(2) NOT NULL,
  ativo BOOLEAN DEFAULT TRUE,
  criado_em TIMESTAMP DEFAULT NOW(),
  atualizado_em TIMESTAMP DEFAULT NOW(),
  criado_por INTEGER,
  atualizado_por INTEGER
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_dados_fiscais_usuario_id ON dados_fiscais (usuario_id);
CREATE INDEX IF NOT EXISTS idx_dados_fiscais_cpf_cnpj ON dados_fiscais (cpf_cnpj);
CREATE INDEX IF NOT EXISTS idx_dados_fiscais_ativo ON dados_fiscais (ativo);

-- Criar trigger para atualizar timestamp
DROP TRIGGER IF EXISTS trg_dados_fiscais_update_timestamp ON dados_fiscais;
CREATE TRIGGER trg_dados_fiscais_update_timestamp 
    BEFORE UPDATE ON dados_fiscais 
    FOR EACH ROW 
    EXECUTE FUNCTION update_timestamp();

-- Comentários para documentação
COMMENT ON TABLE dados_fiscais IS 'Dados fiscais dos usuários (CPF/CNPJ e endereço fiscal) - apenas um por usuário';
COMMENT ON COLUMN dados_fiscais.tipo IS 'Tipo de documento: CPF ou CNPJ';
COMMENT ON COLUMN dados_fiscais.nome_razao_social IS 'Nome completo para CPF ou Razão Social para CNPJ';
COMMENT ON COLUMN dados_fiscais.inscricao_estadual IS 'Inscrição Estadual (opcional, apenas para CNPJ)';
COMMENT ON COLUMN dados_fiscais.inscricao_municipal IS 'Inscrição Municipal (opcional)';

