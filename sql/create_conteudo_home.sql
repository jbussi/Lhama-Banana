-- =====================================================
-- TABELA: CONTEÚDO DA HOME
-- =====================================================
-- Armazena conteúdo dinâmico da página inicial
-- (hero, carrosséis, depoimentos)

CREATE TABLE IF NOT EXISTS conteudo_home (
    id SERIAL PRIMARY KEY,
    
    -- Hero Section
    hero_titulo VARCHAR(255),
    hero_subtitulo TEXT,
    hero_imagem_url TEXT,
    hero_texto_botao VARCHAR(100) DEFAULT 'Comprar Agora',
    
    -- Carrosséis (JSON array)
    carrosseis JSONB DEFAULT '[]'::jsonb,
    
    -- Depoimentos (JSON array)
    depoimentos JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ativo BOOLEAN DEFAULT TRUE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_conteudo_home_ativo ON conteudo_home(ativo);

-- Comentários
COMMENT ON TABLE conteudo_home IS 'Conteúdo dinâmico da página inicial';
COMMENT ON COLUMN conteudo_home.hero_titulo IS 'Título principal da seção hero';
COMMENT ON COLUMN conteudo_home.hero_subtitulo IS 'Subtítulo/descrição da seção hero';
COMMENT ON COLUMN conteudo_home.hero_imagem_url IS 'URL da imagem da hero';
COMMENT ON COLUMN conteudo_home.carrosseis IS 'Array JSON com configurações dos carrosséis';
COMMENT ON COLUMN conteudo_home.depoimentos IS 'Array JSON com depoimentos de clientes';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_conteudo_home_timestamp
    BEFORE UPDATE ON conteudo_home
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Inserir registro padrão
INSERT INTO conteudo_home (
    hero_titulo,
    hero_subtitulo,
    hero_texto_botao,
    carrosseis,
    depoimentos,
    ativo
) VALUES (
    'Noites tranquilas, sorrisos garantidos!',
    'Somos uma marca feita por famílias, para famílias. Aqui você encontra qualidade, conforto e muito carinho em cada detalhe.',
    'Comprar Agora',
    '[
        {
            "nome": "Destaques",
            "slug": "destaques",
            "ativo": true
        },
        {
            "nome": "Mais Vendidos",
            "slug": "vendidos",
            "ativo": true
        },
        {
            "nome": "Coleção Inverno",
            "slug": "inverno",
            "ativo": true
        },
        {
            "nome": "Coleção Verão",
            "slug": "verao",
            "ativo": true
        },
        {
            "nome": "Conjuntos Família",
            "slug": "familia",
            "ativo": true
        }
    ]'::jsonb,
    '[
        {
            "texto": "A LhamaBanana transformou as noites da minha família. A qualidade dos produtos é incrível e o atendimento é excepcional!",
            "nome": "Ana Silva",
            "subtitulo": "Mãe e Cliente desde 2022",
            "ordem": 1,
            "ativo": true
        }
    ]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;
