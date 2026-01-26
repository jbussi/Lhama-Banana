-- =====================================================
-- TABELA: CONTEÚDO DE CONTATO
-- =====================================================
-- Armazena conteúdo da página de contato
-- (texto, informações, links)

CREATE TABLE IF NOT EXISTS conteudo_contato (
    id SERIAL PRIMARY KEY,
    
    -- Texto principal
    titulo VARCHAR(255) DEFAULT 'Entre em Contato',
    texto_principal TEXT,
    
    -- Informações de contato (JSON array)
    informacoes JSONB DEFAULT '[]'::jsonb,
    
    -- Links e redes sociais (JSON object)
    links JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ativo BOOLEAN DEFAULT TRUE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_conteudo_contato_ativo ON conteudo_contato(ativo);

-- Comentários
COMMENT ON TABLE conteudo_contato IS 'Conteúdo da página de contato';
COMMENT ON COLUMN conteudo_contato.texto_principal IS 'Texto principal da página de contato';
COMMENT ON COLUMN conteudo_contato.informacoes IS 'Array JSON com informações de contato';
COMMENT ON COLUMN conteudo_contato.links IS 'Object JSON com links e redes sociais';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_conteudo_contato_timestamp
    BEFORE UPDATE ON conteudo_contato
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Inserir registro padrão
INSERT INTO conteudo_contato (
    titulo,
    texto_principal,
    informacoes,
    links,
    ativo
) VALUES (
    'Entre em Contato',
    'Estamos à disposição para esclarecer suas dúvidas, ouvir sugestões ou receber seu feedback. Entre em contato conosco pelo formulário ou utilize um dos canais abaixo:',
    '[
        {
            "tipo": "email",
            "icone": "fas fa-envelope",
            "titulo": "E-mail",
            "valor": "contato@lhamabanana.com.br",
            "link": "mailto:contato@lhamabanana.com.br"
        },
        {
            "tipo": "telefone",
            "icone": "fas fa-phone-alt",
            "titulo": "Telefone/WhatsApp",
            "valor": "(11) 98765-4321",
            "link": "https://wa.me/5511987654321"
        },
        {
            "tipo": "horario",
            "icone": "far fa-clock",
            "titulo": "Horário de Atendimento",
            "valor": "Segunda a Sexta: 9h às 18h\nSábado: 9h às 13h",
            "link": ""
        }
    ]'::jsonb,
    '{
        "instagram": "#",
        "facebook": "#",
        "pinterest": "#",
        "youtube": "#"
    }'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;
