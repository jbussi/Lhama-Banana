-- Script para criar tabela de avaliações de produtos
-- Execute este script para adicionar suporte a avaliações dinâmicas

-- Criar tabela de avaliações
CREATE TABLE IF NOT EXISTS avaliacoes (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comentario TEXT,
    aprovado BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    UNIQUE(produto_id, usuario_id) -- Um usuário só pode avaliar um produto uma vez
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_avaliacoes_produto_id ON avaliacoes(produto_id);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_usuario_id ON avaliacoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_aprovado ON avaliacoes(aprovado);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_rating ON avaliacoes(rating);

-- Criar trigger para atualizar timestamp
CREATE TRIGGER update_avaliacoes_timestamp
    BEFORE UPDATE ON avaliacoes
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Comentários para documentação
COMMENT ON TABLE avaliacoes IS 'Avaliações de produtos feitas por usuários';
COMMENT ON COLUMN avaliacoes.rating IS 'Nota de 1 a 5 estrelas';
COMMENT ON COLUMN avaliacoes.aprovado IS 'Se a avaliação foi aprovada para exibição (moderação)';






