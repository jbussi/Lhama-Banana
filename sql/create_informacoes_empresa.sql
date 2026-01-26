-- =====================================================
-- TABELA: INFORMAÇÕES DA EMPRESA
-- =====================================================
-- Armazena informações de contato e valores da empresa
-- Usado na home e outras páginas

CREATE TABLE IF NOT EXISTS informacoes_empresa (
    id SERIAL PRIMARY KEY,
    
    -- Contato
    email VARCHAR(255),
    telefone VARCHAR(50),
    whatsapp VARCHAR(50),
    horario_atendimento TEXT,
    
    -- Valores da empresa (JSON array)
    valores JSONB DEFAULT '[]'::jsonb,
    
    -- Redes sociais (JSON object)
    redes_sociais JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ativo BOOLEAN DEFAULT TRUE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_informacoes_empresa_ativo ON informacoes_empresa(ativo);

-- Comentários
COMMENT ON TABLE informacoes_empresa IS 'Informações de contato e valores da empresa';
COMMENT ON COLUMN informacoes_empresa.valores IS 'Array JSON com valores da empresa';
COMMENT ON COLUMN informacoes_empresa.redes_sociais IS 'Object JSON com links das redes sociais';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_informacoes_empresa_timestamp
    BEFORE UPDATE ON informacoes_empresa
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Inserir registro padrão
INSERT INTO informacoes_empresa (
    email,
    telefone,
    whatsapp,
    horario_atendimento,
    valores,
    redes_sociais,
    ativo
) VALUES (
    'contato@lhamabanana.com',
    '(00) 12345-6789',
    '(00) 12345-6789',
    'Segunda a Sexta: 9h às 18h\nSábado: 9h às 12h',
    '[
        {
            "titulo": "Qualidade Premium",
            "descricao": "Usamos apenas os melhores tecidos para garantir conforto e durabilidade em cada peça.",
            "icone": "fas fa-star"
        },
        {
            "titulo": "Design Exclusivo",
            "descricao": "Nossas estampas são criadas por artistas independentes, garantindo peças únicas e cheias de personalidade.",
            "icone": "fas fa-palette"
        },
        {
            "titulo": "Sustentabilidade",
            "descricao": "Comprometidos com o meio ambiente, utilizamos materiais ecológicos e processos de produção responsáveis.",
            "icone": "fas fa-leaf"
        }
    ]'::jsonb,
    '{
        "whatsapp": "https://wa.me/SEUNUMERO",
        "instagram": "https://instagram.com/seuinstagram",
        "facebook": "",
        "pinterest": "",
        "youtube": ""
    }'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;
