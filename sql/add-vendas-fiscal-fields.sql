-- =====================================================
-- Script de Migração: Campos Fiscais na Tabela Vendas
-- =====================================================
-- Este script adiciona campos para snapshot dos dados fiscais
-- na tabela vendas para emissão de nota fiscal
-- =====================================================

-- Adicionar colunas fiscais na tabela vendas (snapshot dos dados fiscais no momento da venda)
ALTER TABLE vendas 
ADD COLUMN IF NOT EXISTS fiscal_tipo VARCHAR(4),
ADD COLUMN IF NOT EXISTS fiscal_cpf_cnpj VARCHAR(18),
ADD COLUMN IF NOT EXISTS fiscal_nome_razao_social VARCHAR(255),
ADD COLUMN IF NOT EXISTS fiscal_inscricao_estadual VARCHAR(20),
ADD COLUMN IF NOT EXISTS fiscal_inscricao_municipal VARCHAR(20),
ADD COLUMN IF NOT EXISTS fiscal_cep VARCHAR(10),
ADD COLUMN IF NOT EXISTS fiscal_rua VARCHAR(255),
ADD COLUMN IF NOT EXISTS fiscal_numero VARCHAR(20),
ADD COLUMN IF NOT EXISTS fiscal_complemento VARCHAR(100),
ADD COLUMN IF NOT EXISTS fiscal_bairro VARCHAR(100),
ADD COLUMN IF NOT EXISTS fiscal_cidade VARCHAR(100),
ADD COLUMN IF NOT EXISTS fiscal_estado CHAR(2);

-- Adicionar constraint para tipo fiscal (se não existir)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'check_fiscal_tipo' 
        AND conrelid = 'vendas'::regclass
    ) THEN
        ALTER TABLE vendas 
        ADD CONSTRAINT check_fiscal_tipo 
        CHECK (fiscal_tipo IS NULL OR fiscal_tipo IN ('CPF', 'CNPJ'));
    END IF;
END $$;

-- Comentários para documentação
COMMENT ON COLUMN vendas.fiscal_tipo IS 'Tipo de documento fiscal: CPF ou CNPJ';
COMMENT ON COLUMN vendas.fiscal_cpf_cnpj IS 'CPF ou CNPJ do cliente (snapshot no momento da venda)';
COMMENT ON COLUMN vendas.fiscal_nome_razao_social IS 'Nome completo (CPF) ou Razão Social (CNPJ)';
COMMENT ON COLUMN vendas.fiscal_inscricao_estadual IS 'Inscrição Estadual (opcional, apenas para CNPJ)';
COMMENT ON COLUMN vendas.fiscal_inscricao_municipal IS 'Inscrição Municipal (opcional)';

