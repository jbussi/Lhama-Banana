-- =====================================================
-- SCRIPT DE CRIAÇÃO DA TABELA ORDERS
-- Tabela para gerenciar pedidos com token público para acesso sem login
-- =====================================================

-- Criar tabela orders para gerenciar pedidos com token público
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
    public_token UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'CRIADO' CHECK (status IN (
        'CRIADO', 
        'PENDENTE', 
        'PAGO', 
        'APROVADO', 
        'CANCELADO', 
        'EXPIRADO', 
        'NA TRANSPORTADORA', 
        'ENTREGUE'
    )),
    valor DECIMAL(10, 2) NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_orders_public_token ON orders (public_token);
CREATE INDEX IF NOT EXISTS idx_orders_venda_id ON orders (venda_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_criado_em ON orders (criado_em);

-- Criar trigger para atualizar timestamp
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_orders_update_timestamp'
    ) THEN
        CREATE TRIGGER trg_orders_update_timestamp
            BEFORE UPDATE ON orders
            FOR EACH ROW
            EXECUTE FUNCTION update_timestamp();
        RAISE NOTICE 'Trigger de atualização de timestamp criado para orders';
    END IF;
END $$;

-- Comentários nas colunas
COMMENT ON TABLE orders IS 'Tabela para gerenciar pedidos com token público para acesso sem login';
COMMENT ON COLUMN orders.id IS 'ID único do pedido (UUID)';
COMMENT ON COLUMN orders.venda_id IS 'Referência à tabela vendas';
COMMENT ON COLUMN orders.public_token IS 'Token público único para acessar o status do pedido sem login';
COMMENT ON COLUMN orders.status IS 'Status atual do pedido';
COMMENT ON COLUMN orders.valor IS 'Valor total do pedido';

DO $$
BEGIN
    RAISE NOTICE 'Tabela orders criada com sucesso!';
END $$;

