-- =====================================================
-- TABELA DE MAPEAMENTO DE SITUAÇÕES DO BLING
-- =====================================================
-- Armazena o mapeamento entre situações do Bling (ID) e status do site
-- Permite sincronização bidirecional de status entre Bling e site

-- Tabela para armazenar situações do Bling
CREATE TABLE IF NOT EXISTS bling_situacoes (
    id SERIAL PRIMARY KEY,
    bling_situacao_id INTEGER UNIQUE NOT NULL, -- ID da situação no Bling
    nome VARCHAR(255) NOT NULL, -- Nome da situação no Bling (ex: "Em aberto", "Em andamento")
    cor VARCHAR(7), -- Cor da situação no Bling (ex: "#E9DC40")
    id_herdado INTEGER DEFAULT 0, -- ID herdado (do Bling)
    status_site VARCHAR(50), -- Status correspondente no site (ex: "em_processamento")
    ativo BOOLEAN DEFAULT TRUE, -- Se a situação está ativa
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_bling_situacoes_bling_id ON bling_situacoes(bling_situacao_id);
CREATE INDEX IF NOT EXISTS idx_bling_situacoes_status_site ON bling_situacoes(status_site);
CREATE INDEX IF NOT EXISTS idx_bling_situacoes_ativo ON bling_situacoes(ativo);

-- Comentários
COMMENT ON TABLE bling_situacoes IS 'Mapeamento entre situações do Bling (ID) e status do site';
COMMENT ON COLUMN bling_situacoes.bling_situacao_id IS 'ID único da situação no Bling';
COMMENT ON COLUMN bling_situacoes.nome IS 'Nome da situação no Bling';
COMMENT ON COLUMN bling_situacoes.status_site IS 'Status correspondente no site (pode ser NULL se não mapeado)';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_bling_situacoes_timestamp
    BEFORE UPDATE ON bling_situacoes
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- =====================================================
-- ATUALIZAR STATUS_PEDIDO PARA INCLUIR NOVOS STATUS
-- =====================================================

-- Remover constraint antiga se existir
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'vendas_status_pedido_check'
        AND table_name = 'vendas'
    ) THEN
        ALTER TABLE vendas DROP CONSTRAINT vendas_status_pedido_check;
    END IF;
END $$;

-- Adicionar nova constraint com todos os status
ALTER TABLE vendas ADD CONSTRAINT vendas_status_pedido_check 
    CHECK (status_pedido IN (
        -- Status originais
        'pendente', 
        'pendente_pagamento',
        'processando_envio', 
        'enviado', 
        'entregue', 
        'cancelado_pelo_cliente', 
        'cancelado_pelo_vendedor',
        'devolvido',
        'reembolsado',
        -- Novos status para fluxo completo
        'pagamento_aprovado',
        'sincronizado_bling',
        'em_processamento',
        'nfe_aguardando_aprovacao',
        'nfe_autorizada',
        'nfe_enviada_email',
        'estoque_baixado',
        'etiqueta_solicitada',
        'etiqueta_gerada',
        'rastreamento_atualizado',
        'pronto_envio',
        -- Status de erro
        'erro_nfe_timeout',
        'erro_processamento',
        'erro_etiqueta',
        'erro_estoque'
    ));

-- =====================================================
-- ADICIONAR CAMPOS AUXILIARES NA TABELA VENDAS
-- =====================================================

-- Campo para armazenar ID da situação atual no Bling
ALTER TABLE vendas ADD COLUMN IF NOT EXISTS bling_situacao_id INTEGER;

-- Campo para armazenar nome da situação atual no Bling
ALTER TABLE vendas ADD COLUMN IF NOT EXISTS bling_situacao_nome VARCHAR(255);

-- Índice para busca rápida por situação do Bling
CREATE INDEX IF NOT EXISTS idx_vendas_bling_situacao_id ON vendas(bling_situacao_id);

-- Comentários
COMMENT ON COLUMN vendas.bling_situacao_id IS 'ID da situação atual do pedido no Bling';
COMMENT ON COLUMN vendas.bling_situacao_nome IS 'Nome da situação atual do pedido no Bling';
