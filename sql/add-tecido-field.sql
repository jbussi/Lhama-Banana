-- Script para adicionar campo tecido na tabela estampa
-- Execute este script para adicionar suporte a filtros por tecido

-- Adicionar coluna tecido na tabela estampa
ALTER TABLE estampa 
ADD COLUMN IF NOT EXISTS tecido VARCHAR(50);

-- Criar índice para melhor performance nas consultas
CREATE INDEX IF NOT EXISTS idx_estampa_tecido ON estampa(tecido);
CREATE INDEX IF NOT EXISTS idx_estampa_sexo ON estampa(sexo);

-- Comentário para documentação
COMMENT ON COLUMN estampa.tecido IS 'Tipo de tecido/material da estampa (ex: Algodão, Poliéster, Algodão 100%, etc)';






