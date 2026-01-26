-- Adicionar campo nome_normalizado para facilitar busca de transportadoras
-- Este campo armazena o nome sem acentos, em maiúsculas, sem espaços extras
-- para facilitar a correspondência mesmo com variações do nome

-- Adicionar coluna nome_normalizado
ALTER TABLE transportadoras_bling
ADD COLUMN IF NOT EXISTS nome_normalizado VARCHAR(255);

-- Adicionar coluna fantasia_normalizado
ALTER TABLE transportadoras_bling
ADD COLUMN IF NOT EXISTS fantasia_normalizado VARCHAR(255);

-- Função para normalizar nome (remover acentos, converter para maiúscula, remover espaços extras)
CREATE OR REPLACE FUNCTION normalizar_nome_transportadora(nome_texto TEXT)
RETURNS TEXT AS $$
BEGIN
    IF nome_texto IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Converter para maiúscula
    nome_texto := UPPER(nome_texto);
    
    -- Remover acentos (substituir caracteres acentuados)
    nome_texto := translate(
        nome_texto,
        'ÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ',
        'AAAAEEEIIIOOOOUUUC'
    );
    
    -- Remover espaços extras e trim
    nome_texto := trim(regexp_replace(nome_texto, '\s+', ' ', 'g'));
    
    -- Remover caracteres especiais comuns (mantém apenas letras, números e espaços)
    nome_texto := regexp_replace(nome_texto, '[^A-Z0-9 ]', '', 'g');
    
    RETURN nome_texto;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Atualizar nome_normalizado e fantasia_normalizado para registros existentes
UPDATE transportadoras_bling
SET 
    nome_normalizado = normalizar_nome_transportadora(nome),
    fantasia_normalizado = normalizar_nome_transportadora(fantasia)
WHERE nome_normalizado IS NULL OR fantasia_normalizado IS NULL;

-- Criar índices para busca rápida
CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_nome_normalizado 
ON transportadoras_bling(nome_normalizado) 
WHERE situacao = 'A' AND nome_normalizado IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_fantasia_normalizado 
ON transportadoras_bling(fantasia_normalizado) 
WHERE situacao = 'A' AND fantasia_normalizado IS NOT NULL;

-- Criar índice composto para busca por nome normalizado ou fantasia normalizado
CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_nome_fantasia_normalizado 
ON transportadoras_bling(nome_normalizado, fantasia_normalizado) 
WHERE situacao = 'A';

-- Trigger para atualizar nome_normalizado automaticamente quando nome ou fantasia mudarem
CREATE OR REPLACE FUNCTION update_transportadora_nome_normalizado()
RETURNS TRIGGER AS $$
BEGIN
    NEW.nome_normalizado := normalizar_nome_transportadora(NEW.nome);
    NEW.fantasia_normalizado := normalizar_nome_transportadora(NEW.fantasia);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Remover trigger se já existir
DROP TRIGGER IF EXISTS trigger_update_transportadora_nome_normalizado ON transportadoras_bling;

-- Criar trigger
CREATE TRIGGER trigger_update_transportadora_nome_normalizado
BEFORE INSERT OR UPDATE OF nome, fantasia ON transportadoras_bling
FOR EACH ROW
EXECUTE FUNCTION update_transportadora_nome_normalizado();

-- Comentários
COMMENT ON COLUMN transportadoras_bling.nome_normalizado IS 'Nome normalizado (maiúscula, sem acentos, sem espaços extras) para busca facilitada';
COMMENT ON COLUMN transportadoras_bling.fantasia_normalizado IS 'Fantasia normalizada (maiúscula, sem acentos, sem espaços extras) para busca facilitada';
COMMENT ON FUNCTION normalizar_nome_transportadora IS 'Normaliza nome de transportadora removendo acentos, convertendo para maiúscula e removendo espaços extras';
