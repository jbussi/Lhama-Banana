-- =====================================================
-- Script de Migração: Adicionar CPF na tabela cupom_usado
-- =====================================================
-- Este script adiciona a coluna cpf_usuario na tabela cupom_usado
-- para garantir que cada cupom só seja usado por um único CPF
-- =====================================================

-- Adicionar coluna cpf_usuario na tabela cupom_usado
ALTER TABLE cupom_usado
ADD COLUMN IF NOT EXISTS cpf_usuario CHAR(11);

-- Criar índice para otimizar consultas por CPF
CREATE INDEX IF NOT EXISTS idx_cupom_usado_cpf ON cupom_usado (cpf_usuario);

-- Criar índice único para garantir que um cupom só seja usado uma vez por CPF
CREATE UNIQUE INDEX IF NOT EXISTS idx_cupom_usado_cupom_cpf_unique 
ON cupom_usado (cupom_id, cpf_usuario) 
WHERE cpf_usuario IS NOT NULL;

-- Atualizar registros existentes com o CPF do usuário (se existir)
-- Nota: Isso só funciona se as colunas usuario_id e cupom_id existirem
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'cupom_usado' AND column_name = 'usuario_id') THEN
        UPDATE cupom_usado cu
        SET cpf_usuario = u.cpf
        FROM usuarios u
        WHERE cu.usuario_id = u.id 
        AND u.cpf IS NOT NULL
        AND cu.cpf_usuario IS NULL;
    END IF;
END $$;

-- Comentários para documentação
COMMENT ON COLUMN cupom_usado.cpf_usuario IS 'CPF do usuário que utilizou o cupom (para garantir uso único por CPF)';

