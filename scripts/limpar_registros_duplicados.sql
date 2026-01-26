-- Script para limpar registros duplicados de conteudo_home
-- Mantém apenas o registro mais antigo (ID 1) e desativa os outros

-- Desativar todos os registros exceto o ID 1
UPDATE conteudo_home SET ativo = FALSE WHERE id != 1;

-- Se o ID 1 não existir, usar o mais antigo
DO $$
DECLARE
    primeiro_id INTEGER;
BEGIN
    SELECT id INTO primeiro_id FROM conteudo_home ORDER BY id ASC LIMIT 1;
    
    IF primeiro_id IS NOT NULL THEN
        UPDATE conteudo_home SET ativo = FALSE WHERE id != primeiro_id;
        UPDATE conteudo_home SET ativo = TRUE WHERE id = primeiro_id;
    END IF;
END $$;

-- Mostrar resultado
SELECT id, hero_titulo, ativo, criado_em, atualizado_em 
FROM conteudo_home 
ORDER BY id;
