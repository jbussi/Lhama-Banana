-- Tabelas para integração com Bling
-- ===================================

-- Tabela para rastrear produtos sincronizados com Bling
CREATE TABLE IF NOT EXISTS bling_produtos (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE UNIQUE NOT NULL,
    bling_id BIGINT NOT NULL, -- BIGINT pois IDs do Bling podem ser muito grandes
    bling_codigo VARCHAR(50) NOT NULL, -- SKU no Bling
    ultima_sincronizacao TIMESTAMP DEFAULT NOW(),
    status_sincronizacao VARCHAR(20) DEFAULT 'sync' CHECK (status_sincronizacao IN ('sync', 'error', 'pending')),
    erro_ultima_sync TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bling_produtos_produto_id ON bling_produtos(produto_id);
CREATE INDEX IF NOT EXISTS idx_bling_produtos_bling_id ON bling_produtos(bling_id);
CREATE INDEX IF NOT EXISTS idx_bling_produtos_bling_codigo ON bling_produtos(bling_codigo);

-- Tabela para logs de sincronização
CREATE TABLE IF NOT EXISTS bling_sync_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('produto', 'pedido', 'nfe', 'cliente')),
    entity_id INTEGER,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'sync', 'delete')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error', 'pending')),
    response_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bling_sync_logs_entity ON bling_sync_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_bling_sync_logs_created_at ON bling_sync_logs(created_at DESC);

-- Tabela para rastrear pedidos sincronizados com Bling
CREATE TABLE IF NOT EXISTS bling_pedidos (
    id SERIAL PRIMARY KEY,
    venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE UNIQUE NOT NULL,
    bling_pedido_id BIGINT NOT NULL, -- BIGINT pois IDs do Bling podem ser muito grandes
    bling_nfe_id BIGINT, -- BIGINT pois IDs do Bling podem ser muito grandes
    nfe_numero INTEGER,
    nfe_chave_acesso VARCHAR(44),
    nfe_xml TEXT, -- XML completo da NF-e
    nfe_status VARCHAR(20), -- 'EMITIDA', 'AUTORIZADA', 'CANCELADA'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bling_pedidos_venda_id ON bling_pedidos(venda_id);
CREATE INDEX IF NOT EXISTS idx_bling_pedidos_bling_pedido_id ON bling_pedidos(bling_pedido_id);
CREATE INDEX IF NOT EXISTS idx_bling_pedidos_nfe_chave_acesso ON bling_pedidos(nfe_chave_acesso);

-- Adicionar coluna bling_id na tabela produtos (opcional, pode usar bling_produtos)
-- ALTER TABLE produtos ADD COLUMN IF NOT EXISTS bling_id INTEGER;

