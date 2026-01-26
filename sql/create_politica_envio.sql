-- =====================================================
-- TABELA: POLÍTICA DE ENVIO
-- =====================================================
-- Armazena conteúdo da página de política de envio

CREATE TABLE IF NOT EXISTS politica_envio (
    id SERIAL PRIMARY KEY,
    
    -- Título e conteúdo
    titulo VARCHAR(255) DEFAULT 'Política de Envio',
    ultima_atualizacao DATE,
    conteudo TEXT,
    
    -- Seções (JSON array)
    secoes JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ativo BOOLEAN DEFAULT TRUE
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_politica_envio_ativo ON politica_envio(ativo);

-- Comentários
COMMENT ON TABLE politica_envio IS 'Conteúdo da página de política de envio';
COMMENT ON COLUMN politica_envio.conteudo IS 'Texto introdutório da política';
COMMENT ON COLUMN politica_envio.secoes IS 'Array JSON com seções da política';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_politica_envio_timestamp
    BEFORE UPDATE ON politica_envio
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Inserir registro padrão
INSERT INTO politica_envio (
    titulo,
    ultima_atualizacao,
    conteudo,
    secoes,
    ativo
) VALUES (
    'Política de Envio',
    CURRENT_DATE,
    'A LhamaBanana está comprometida em entregar seus produtos com segurança e agilidade. Esta Política de Envio descreve nossos processos de envio, prazos, custos e condições de entrega.',
    '[
        {
            "titulo": "1. Prazos de Envio",
            "conteudo": "Após a confirmação do pagamento, processamos seu pedido em até 2 dias úteis. O prazo de entrega varia conforme a região e o método de envio escolhido:\n\n- Regiões Metropolitanas: 3 a 7 dias úteis\n- Capitais e Grandes Cidades: 5 a 10 dias úteis\n- Interior: 7 a 15 dias úteis\n- Regiões Remotas: 10 a 20 dias úteis\n\nOs prazos começam a contar após a confirmação do pagamento e podem variar em períodos de alta demanda.",
            "ordem": 1
        },
        {
            "titulo": "2. Métodos de Envio",
            "conteudo": "Trabalhamos com as principais transportadoras do país para garantir a melhor opção de entrega:\n\n- Transportadoras parceiras (Jadlog, Azul, etc.)\n- Correios (PAC e SEDEX)\n- Entregas expressas (quando disponível)\n\nO método de envio disponível será exibido no checkout, com opções de frete calculadas automaticamente.",
            "ordem": 2
        },
        {
            "titulo": "3. Cálculo do Frete",
            "conteudo": "O valor do frete é calculado automaticamente com base em:\n\n- Peso total do pedido\n- Dimensões dos produtos\n- CEP de destino\n- Método de envio selecionado\n\nOferecemos frete grátis para pedidos acima de determinado valor (consulte condições promocionais).",
            "ordem": 3
        },
        {
            "titulo": "4. Rastreamento",
            "conteudo": "Após o envio, você receberá por e-mail:\n\n- Código de rastreamento\n- Link para acompanhar sua entrega\n- Previsão de entrega atualizada\n\nVocê também pode acompanhar seu pedido através da sua conta no site.",
            "ordem": 4
        },
        {
            "titulo": "5. Endereço de Entrega",
            "conteudo": "É fundamental que o endereço de entrega esteja completo e correto:\n\n- Verifique todos os dados antes de finalizar o pedido\n- Informe complementos, pontos de referência quando necessário\n- Em caso de erro, entre em contato imediatamente\n\nNão nos responsabilizamos por entregas em endereços incorretos fornecidos pelo cliente.",
            "ordem": 5
        },
        {
            "titulo": "6. Tentativas de Entrega",
            "conteudo": "A transportadora realizará até 3 tentativas de entrega no endereço informado. Caso não seja possível realizar a entrega:\n\n- O produto retornará ao nosso centro de distribuição\n- Você será notificado por e-mail\n- Será necessário pagar novo frete para reenvio\n\nRecomendamos que alguém esteja disponível para receber o pedido ou autorize a entrega.",
            "ordem": 6
        },
        {
            "titulo": "7. Atrasos na Entrega",
            "conteudo": "Em caso de atraso na entrega:\n\n- Entre em contato conosco para investigação\n- Verificaremos o status com a transportadora\n- Em caso de extravio, abriremos processo de busca\n- Se necessário, faremos o reenvio do produto\n\nNos comprometemos a resolver qualquer problema relacionado à entrega.",
            "ordem": 7
        },
        {
            "titulo": "8. Recebimento do Pedido",
            "conteudo": "Ao receber seu pedido:\n\n- Verifique se a embalagem está íntegra\n- Confira se todos os itens estão presentes\n- Em caso de problemas, entre em contato em até 48 horas\n- Guarde a nota fiscal para eventuais trocas ou devoluções",
            "ordem": 8
        },
        {
            "titulo": "9. Contato",
            "conteudo": "Para dúvidas sobre envio ou entrega, entre em contato:\n\n- E-mail: envio@lhamabanana.com\n- Telefone: (00) 12345-6789\n- Atendimento: Segunda a Sexta, 9h às 18h",
            "ordem": 9
        }
    ]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;
