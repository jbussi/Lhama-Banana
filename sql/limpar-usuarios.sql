-- Script para remover todos os usuários do banco de dados
-- ATENÇÃO: Esta operação é IRREVERSÍVEL!
-- Os endereços serão removidos automaticamente devido ao ON DELETE CASCADE

-- Ver quantos usuários existem antes de remover
SELECT COUNT(*) as total_usuarios FROM usuarios;

-- Remover todos os usuários
DELETE FROM usuarios;

-- Verificar se foram removidos
SELECT COUNT(*) as usuarios_restantes FROM usuarios;

-- Verificar se os endereços também foram removidos (devido ao CASCADE)
SELECT COUNT(*) as enderecos_restantes FROM enderecos;


