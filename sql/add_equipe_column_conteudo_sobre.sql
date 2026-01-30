-- =====================================================
-- MIGRATION: Add missing 'equipe' column to conteudo_sobre
-- =====================================================
-- Adds the 'equipe' column that Strapi expects

ALTER TABLE conteudo_sobre
ADD COLUMN IF NOT EXISTS equipe JSONB DEFAULT '[]'::jsonb;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_conteudo_sobre_equipe ON conteudo_sobre USING GIN (equipe);

-- Comment the column
COMMENT ON COLUMN conteudo_sobre.equipe IS 'Array JSON com membros da equipe (campo Strapi)';
