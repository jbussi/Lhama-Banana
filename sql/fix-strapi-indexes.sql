-- =====================================================
-- CORREÇÃO DE ÍNDICES FALTANTES DO STRAPI
-- =====================================================
-- Este script cria os índices que o Strapi espera encontrar
-- mas que não existem no banco de dados.
-- 
-- Esses índices são relacionados a tabelas internas do Strapi:
-- - Workflows
-- - Permissões
-- - Roles
-- - API Tokens
-- - Audit Logs
-- =====================================================

-- Verificar e criar índices faltantes apenas se as tabelas existirem
-- (O Strapi cria essas tabelas automaticamente, então verificamos primeiro)

DO $$
BEGIN
    -- Índice para strapi_workflows_stages_workflow_lnk
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'strapi_workflows_stages_workflow_lnk') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'strapi_workflows_stages_workflow_lnk_unique') THEN
            CREATE UNIQUE INDEX IF NOT EXISTS strapi_workflows_stages_workflow_lnk_unique 
            ON strapi_workflows_stages_workflow_lnk(workflow_id, stage_id);
        END IF;
    END IF;

    -- Índice para strapi_workflows_stages_permissions_lnk
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'strapi_workflows_stages_permissions_lnk') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'strapi_workflows_stages_permissions_lnk_unique') THEN
            CREATE UNIQUE INDEX IF NOT EXISTS strapi_workflows_stages_permissions_lnk_unique 
            ON strapi_workflows_stages_permissions_lnk(stage_id, permission_id);
        END IF;
    END IF;

    -- Índice para admin_permissions_role_lnk
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'admin_permissions_role_lnk') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'admin_permissions_role_lnk_unique') THEN
            CREATE UNIQUE INDEX IF NOT EXISTS admin_permissions_role_lnk_unique 
            ON admin_permissions_role_lnk(permission_id, role_id);
        END IF;
    END IF;

    -- Índice para admin_users_roles_lnk
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'admin_users_roles_lnk') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'admin_users_roles_lnk_unique') THEN
            CREATE UNIQUE INDEX IF NOT EXISTS admin_users_roles_lnk_unique 
            ON admin_users_roles_lnk(user_id, role_id);
        END IF;
    END IF;

    -- Índice para strapi_api_token_permissions_token_lnk
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'strapi_api_token_permissions_token_lnk') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'strapi_api_token_permissions_token_lnk_unique') THEN
            CREATE UNIQUE INDEX IF NOT EXISTS strapi_api_token_permissions_token_lnk_unique 
            ON strapi_api_token_permissions_token_lnk(api_token_id, api_token_permission_id);
        END IF;
    END IF;

    -- Índice para strapi_transfer_token_permissions_token_lnk
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'strapi_transfer_token_permissions_token_lnk') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'strapi_transfer_token_permissions_token_lnk_unique') THEN
            CREATE UNIQUE INDEX IF NOT EXISTS strapi_transfer_token_permissions_token_lnk_unique 
            ON strapi_transfer_token_permissions_token_lnk(transfer_token_id, transfer_token_permission_id);
        END IF;
    END IF;

    -- Índice para strapi_audit_logs_user_lnk
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'strapi_audit_logs_user_lnk') THEN
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'strapi_audit_logs_user_lnk_unique') THEN
            CREATE UNIQUE INDEX IF NOT EXISTS strapi_audit_logs_user_lnk_unique 
            ON strapi_audit_logs_user_lnk(audit_log_id, user_id);
        END IF;
    END IF;

    RAISE NOTICE 'Verificação de índices do Strapi concluída.';
END $$;

-- =====================================================
-- NOTA: Esses erros são apenas avisos de migração
-- =====================================================
-- O Strapi tenta renomear índices durante migrações automáticas.
-- Se os índices não existem, o Strapi os criará automaticamente
-- na próxima sincronização. Esses erros podem ser ignorados com
-- segurança, pois não afetam o funcionamento do sistema.
-- =====================================================


