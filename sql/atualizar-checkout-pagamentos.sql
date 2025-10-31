-- =====================================================
-- SCRIPT DE ATUALIZAÇÃO DO BANCO DE DADOS
-- Para suportar checkout com PagBank (PIX, Boleto, Cartão)
-- =====================================================

-- Verificar e adicionar campos faltantes na tabela vendas
DO $$
BEGIN
    -- Adicionar valor_frete se não existir
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vendas' AND column_name = 'valor_frete'
    ) THEN
        ALTER TABLE vendas ADD COLUMN valor_frete DECIMAL(10, 2) DEFAULT 0;
        RAISE NOTICE 'Campo valor_frete adicionado à tabela vendas';
    END IF;

    -- Adicionar valor_desconto se não existir
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'vendas' AND column_name = 'valor_desconto'
    ) THEN
        ALTER TABLE vendas ADD COLUMN valor_desconto DECIMAL(10, 2) DEFAULT 0;
        RAISE NOTICE 'Campo valor_desconto adicionado à tabela vendas';
    END IF;

    -- Atualizar status_pedido para incluir 'pendente_pagamento'
    -- Primeiro verifica se a constraint existe
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'vendas' 
        AND constraint_name LIKE '%status_pedido%'
    ) THEN
        -- Remove a constraint antiga se existir
        ALTER TABLE vendas DROP CONSTRAINT IF EXISTS vendas_status_pedido_check;
    END IF;
    
    -- Adiciona nova constraint com todos os status (se ainda não existir)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'vendas' 
        AND constraint_name = 'vendas_status_pedido_check'
    ) THEN
        ALTER TABLE vendas ADD CONSTRAINT vendas_status_pedido_check 
            CHECK (status_pedido IN (
                'pendente', 
                'pendente_pagamento',
                'processando_envio', 
                'enviado', 
                'entregue', 
                'cancelado_pelo_cliente', 
                'cancelado_pelo_vendedor'
            ));
    END IF;
    RAISE NOTICE 'Constraint de status_pedido atualizada';
END $$;

-- Verificar e atualizar tabela pagamentos
DO $$
BEGIN
    -- Verificar se a tabela pagamentos existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'pagamentos'
    ) THEN
        -- Criar tabela pagamentos se não existir
        CREATE TABLE pagamentos (
            id SERIAL PRIMARY KEY,
            venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
            
            pagbank_transaction_id VARCHAR(100) UNIQUE,
            pagbank_order_id VARCHAR(100),
            
            forma_pagamento_tipo VARCHAR(50) NOT NULL CHECK (forma_pagamento_tipo IN ('CREDIT_CARD', 'PIX', 'BOLETO')),
            bandeira_cartao VARCHAR(50),
            parcelas INTEGER DEFAULT 1,
            
            valor_pago DECIMAL(10, 2) NOT NULL,
            
            status_pagamento VARCHAR(50) NOT NULL CHECK (status_pagamento IN ('PENDING', 'AUTHORIZED', 'PAID', 'DECLINED', 'REFUNDED', 'CHARGEBACK')),
            status_detalhe_pagamento VARCHAR(100),
            
            pagbank_qrcode_link TEXT,
            pagbank_qrcode_image TEXT,
            pagbank_boleto_link TEXT,
            pagbank_barcode_data TEXT,
            pagbank_boleto_expires_at TIMESTAMP,
            
            json_resposta_api JSONB,
            
            criado_em TIMESTAMP DEFAULT NOW(),
            atualizado_em TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX idx_pagamentos_venda_id ON pagamentos (venda_id);
        CREATE INDEX idx_pagamentos_transaction_id ON pagamentos (pagbank_transaction_id);
        CREATE INDEX idx_pagamentos_status ON pagamentos (status_pagamento);
        
        RAISE NOTICE 'Tabela pagamentos criada';
    ELSE
        -- Adicionar campos que possam estar faltando
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'pagamentos' AND column_name = 'pagbank_boleto_expires_at'
        ) THEN
            ALTER TABLE pagamentos ADD COLUMN pagbank_boleto_expires_at TIMESTAMP;
            RAISE NOTICE 'Campo pagbank_boleto_expires_at adicionado à tabela pagamentos';
        END IF;

        -- Atualizar constraint de status_pagamento se necessário
        -- Primeiro remove a constraint antiga se existir
        IF EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE table_name = 'pagamentos' 
            AND constraint_name LIKE '%status_pagamento%'
        ) THEN
            ALTER TABLE pagamentos DROP CONSTRAINT IF EXISTS pagamentos_status_pagamento_check;
        END IF;
        
        -- Adiciona nova constraint com todos os status
        ALTER TABLE pagamentos ADD CONSTRAINT pagamentos_status_pagamento_check 
            CHECK (status_pagamento IN ('PENDING', 'AUTHORIZED', 'PAID', 'WAITING', 'DECLINED', 'REFUNDED', 'CHARGEBACK'));
        
        RAISE NOTICE 'Tabela pagamentos atualizada';
    END IF;
END $$;

-- Criar função update_timestamp se não existir
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $func$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$func$ LANGUAGE plpgsql;

-- Criar trigger para atualizar timestamp na tabela pagamentos
DO $$
BEGIN
    -- Criar trigger se não existir
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_pagamentos_update_timestamp'
    ) THEN
        CREATE TRIGGER trg_pagamentos_update_timestamp
            BEFORE UPDATE ON pagamentos
            FOR EACH ROW
            EXECUTE FUNCTION update_timestamp();
        RAISE NOTICE 'Trigger de atualização de timestamp criado para pagamentos';
    END IF;
END $$;

-- Criar índices adicionais para melhor performance
CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas (usuario_id);
CREATE INDEX IF NOT EXISTS idx_vendas_codigo_pedido ON vendas (codigo_pedido);
CREATE INDEX IF NOT EXISTS idx_vendas_status_pedido ON vendas (status_pedido);
CREATE INDEX IF NOT EXISTS idx_vendas_data_venda ON vendas (data_venda);
CREATE INDEX IF NOT EXISTS idx_itens_venda_venda_id ON itens_venda (venda_id);
CREATE INDEX IF NOT EXISTS idx_itens_venda_produto_id ON itens_venda (produto_id);

-- Verificar se a coluna 'role' existe na tabela usuarios
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'usuarios' AND column_name = 'role'
    ) THEN
        ALTER TABLE usuarios ADD COLUMN role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin'));
        RAISE NOTICE 'Campo role adicionado à tabela usuarios';
    END IF;
END $$;

-- Verificar e adicionar coluna email na tabela enderecos (se necessário para checkout)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'enderecos' AND column_name = 'email'
    ) THEN
        ALTER TABLE enderecos ADD COLUMN email VARCHAR(255);
        RAISE NOTICE 'Campo email adicionado à tabela enderecos (opcional)';
    END IF;
END $$;

-- Verificar se a coluna telefone existe na tabela enderecos
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'enderecos' AND column_name = 'telefone'
    ) THEN
        ALTER TABLE enderecos ADD COLUMN telefone VARCHAR(20);
        RAISE NOTICE 'Campo telefone adicionado à tabela enderecos (opcional)';
    END IF;
END $$;

-- Mensagem final
DO $$
BEGIN
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'Atualização do banco de dados concluída com sucesso!';
    RAISE NOTICE 'Todas as tabelas necessárias para checkout foram verificadas/atualizadas.';
    RAISE NOTICE '=====================================================';
END $$;

