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

-- PRIMEIRO: Renomear índices existentes (se existirem) para evitar conflitos
-- O Strapi tenta renomear índices durante migrações, mas eles podem não existir

DO $$
DECLARE
    index_record RECORD;
BEGIN
    -- Lista de renames que o Strapi tenta fazer
    FOR index_record IN 
        SELECT unnest(ARRAY[
            'tecidos_documents_index',
            'usuarios_documents_index', 
            'vendas_documents_index',
            'venda_status_historico_documents_index',
            'admin_permissions_documents_index',
            'admin_users_documents_index',
            'admin_roles_documents_index',
            'strapi_api_tokens_documents_index',
            'strapi_api_token_permissions_documents_index',
            'strapi_transfer_tokens_documents_index',
            'strapi_transfer_token_permissions_documents_index',
            'strapi_sessions_documents_index',
            'files_related_mph_order_index',
            'files_related_mph_id_column_index',
            'files_folder_lnk_unique',
            'upload_folders_parent_lnk_unique',
            'strapi_release_actions_release_lnk_unique',
            'strapi_workflows_stage_required_to_publish_lnk_unique',
            'strapi_workflows_stages_workflow_lnk_unique',
            'strapi_workflows_stages_permissions_lnk_unique',
            'cupom_usado_cupom_lnk_unique',
            'cupom_usado_usuario_lnk_unique',
            'cupom_usado_venda_lnk_unique',
            'enderecos_usuario_lnk_unique',
            'estampa_categoria_lnk_unique',
            'estampa_tecido_lnk_unique',
            'etiquetas_frete_venda_lnk_unique',
            'imagens_produto_produto_lnk_unique',
            'itens_venda_venda_lnk_unique',
            'itens_venda_produto_lnk_unique',
            'nome_produto_categoria_lnk_unique',
            'pagamentos_venda_lnk_unique',
            'pagamento_status_historico_pagamento_lnk_unique',
            'produtos_nome_produto_lnk_unique',
            'produtos_estampa_lnk_unique',
            'produtos_tamanho_lnk_unique',
            'vendas_usuario_lnk_unique',
            'vendas_cupom_lnk_unique',
            'vendas_responsavel_lnk_unique',
            'venda_status_historico_venda_lnk_unique',
            'venda_status_historico_usuario_lnk_unique',
            'admin_permissions_role_lnk_unique',
            'admin_users_roles_lnk_unique'
        ]) as old_name,
        unnest(ARRAY[
            'tecidos_documents_idx',
            'usuarios_documents_idx',
            'vendas_documents_idx',
            'venda_status_historico_documents_idx',
            'admin_permissions_documents_idx',
            'admin_users_documents_idx',
            'admin_roles_documents_idx',
            'strapi_api_tokens_documents_idx',
            'strapi_api_token_permissions_documents_idx',
            'strapi_transfer_tokens_documents_idx',
            'strapi_transfer_token_permissions_documents_idx',
            'strapi_sessions_documents_idx',
            'files_related_mph_oidx',
            'files_related_mph_idix',
            'files_folder_lnk_uq',
            'upload_folders_parent_lnk_uq',
            'strapi_release_actions_release_lnk_uq',
            'strapi_workflows_stage_required_to_publish_lnk_uq',
            'strapi_workflows_stages_workflow_lnk_uq',
            'strapi_workflows_stages_permissions_lnk_uq',
            'cupom_usado_cupom_lnk_uq',
            'cupom_usado_usuario_lnk_uq',
            'cupom_usado_venda_lnk_uq',
            'enderecos_usuario_lnk_uq',
            'estampa_categoria_lnk_uq',
            'estampa_tecido_lnk_uq',
            'etiquetas_frete_venda_lnk_uq',
            'imagens_produto_produto_lnk_uq',
            'itens_venda_venda_lnk_uq',
            'itens_venda_produto_lnk_uq',
            'nome_produto_categoria_lnk_uq',
            'pagamentos_venda_lnk_uq',
            'pagamento_status_historico_pagamento_lnk_uq',
            'produtos_nome_produto_lnk_uq',
            'produtos_estampa_lnk_uq',
            'produtos_tamanho_lnk_uq',
            'vendas_usuario_lnk_uq',
            'vendas_cupom_lnk_uq',
            'vendas_responsavel_lnk_uq',
            'venda_status_historico_venda_lnk_uq',
            'venda_status_historico_usuario_lnk_uq',
            'admin_permissions_role_lnk_uq',
            'admin_users_roles_lnk_uq'
        ]) as new_name
    LOOP
        -- Verificar se o índice antigo existe e o novo não
        IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = index_record.old_name) 
           AND NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = index_record.new_name) THEN
            EXECUTE format('ALTER INDEX %I RENAME TO %I', index_record.old_name, index_record.new_name);
            RAISE NOTICE 'Renomeado índice % para %', index_record.old_name, index_record.new_name;
        ELSIF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = index_record.new_name) THEN
            RAISE NOTICE 'Índice % já existe, pulando rename', index_record.new_name;
        ELSE
            RAISE NOTICE 'Índice % não encontrado, pulando rename', index_record.old_name;
        END IF;
    END LOOP;
END $$;

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


