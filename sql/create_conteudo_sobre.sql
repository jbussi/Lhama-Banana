-- =====================================================
-- TABELA: CONTEÚDO SOBRE NÓS
-- =====================================================
-- Armazena conteúdo da página sobre nós
-- (história, valores, equipe)

CREATE TABLE IF NOT EXISTS conteudo_sobre (
    id SERIAL PRIMARY KEY,
    
    -- Nossa História
    historia_titulo VARCHAR(255) DEFAULT 'Nossa História',
    historia_conteudo TEXT,
    
    -- Nossos Valores
    valores_titulo VARCHAR(255) DEFAULT 'Nossos Valores',
    valores_conteudo JSONB DEFAULT '[]'::jsonb,
    
    -- Nossa Equipe
    equipe_titulo VARCHAR(255) DEFAULT 'Nossa Equipe',
    equipe_conteudo JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ativo BOOLEAN DEFAULT TRUE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_conteudo_sobre_ativo ON conteudo_sobre(ativo);

-- Comentários
COMMENT ON TABLE conteudo_sobre IS 'Conteúdo da página sobre nós';
COMMENT ON COLUMN conteudo_sobre.historia_conteudo IS 'Texto da história da empresa';
COMMENT ON COLUMN conteudo_sobre.valores_conteudo IS 'Array JSON com valores da empresa';
COMMENT ON COLUMN conteudo_sobre.equipe_conteudo IS 'Array JSON com membros da equipe';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_conteudo_sobre_timestamp
    BEFORE UPDATE ON conteudo_sobre
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Inserir registro padrão
INSERT INTO conteudo_sobre (
    historia_titulo,
    historia_conteudo,
    valores_titulo,
    valores_conteudo,
    equipe_titulo,
    equipe_conteudo,
    ativo
) VALUES (
    'Nossa História',
    'Olá! Somos a LhamaBanana, uma marca que nasceu da paixão por moda divertida, conforto inigualável e, é claro, lhamas fofinhas! 🦙✨

Tudo começou em 2020, quando nossa fundadora, Ana, estava procurando por uma camiseta estampada com lhamas para presentear uma amiga. Para sua surpresa, não encontrou muitas opções que combinassem qualidade, estilo e um toque de humor. Foi aí que surgiu a ideia: por que não criar uma marca que une moda casual a estampas únicas de lhamas e frutas tropicais?

Com um pequeno investimento inicial e muito amor pelo que fazemos, demos vida à LhamaBanana. Começamos com uma pequena coleção de camisetas e, em pouco tempo, nossa comunidade de clientes apaixonados por lhamas começou a crescer!',
    'Nossos Valores',
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
    'Nossa Equipe',
    '[
        {
            "nome": "Ana Silva",
            "cargo": "Fundadora & CEO",
            "descricao": "A mente criativa por trás da LhamaBanana, Ana adora desenhar novas estampas e cuidar de suas plantinhas.",
            "foto": "",
            "redes_sociais": {
                "instagram": "#",
                "linkedin": "#",
                "twitter": "#"
            }
        },
        {
            "nome": "Carlos Mendes",
            "cargo": "Diretor de Operações",
            "descricao": "Garante que tudo funcione perfeitamente, dos pedidos à logística. Nosso mestre da organização!",
            "foto": "",
            "redes_sociais": {
                "instagram": "#",
                "linkedin": "#"
            }
        },
        {
            "nome": "Juliana Costa",
            "cargo": "Designer Chefe",
            "descricao": "Transforma ideias em estampas incríveis. Ama café forte e suas duas lhamas de estimação, Paco e Lola.",
            "foto": "",
            "redes_sociais": {
                "instagram": "#",
                "behance": "#"
            }
        }
    ]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;
