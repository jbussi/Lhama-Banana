-- =====================================================
-- TABELA: POLÍTICA DE PRIVACIDADE
-- =====================================================
-- Armazena conteúdo da página de política de privacidade

CREATE TABLE IF NOT EXISTS politica_privacidade (
    id SERIAL PRIMARY KEY,
    
    -- Título e conteúdo
    titulo VARCHAR(255) DEFAULT 'Política de Privacidade',
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
CREATE INDEX IF NOT EXISTS idx_politica_privacidade_ativo ON politica_privacidade(ativo);

-- Comentários
COMMENT ON TABLE politica_privacidade IS 'Conteúdo da página de política de privacidade';
COMMENT ON COLUMN politica_privacidade.conteudo IS 'Texto introdutório da política';
COMMENT ON COLUMN politica_privacidade.secoes IS 'Array JSON com seções da política';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_politica_privacidade_timestamp
    BEFORE UPDATE ON politica_privacidade
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Inserir registro padrão
INSERT INTO politica_privacidade (
    titulo,
    ultima_atualizacao,
    conteudo,
    secoes,
    ativo
) VALUES (
    'Política de Privacidade',
    CURRENT_DATE,
    'A LhamaBanana está comprometida em proteger a privacidade e os dados pessoais de nossos clientes. Esta Política de Privacidade descreve como coletamos, usamos, armazenamos e protegemos suas informações pessoais quando você utiliza nosso site e serviços.',
    '[
        {
            "titulo": "1. Informações que Coletamos",
            "conteudo": "Coletamos informações que você nos fornece diretamente, incluindo:\n\n- Nome completo\n- Endereço de e-mail\n- Telefone\n- Endereço de entrega e cobrança\n- Informações de pagamento (processadas de forma segura por nossos parceiros)\n- Histórico de compras\n- Comunicações conosco (e-mails, mensagens, etc.)",
            "ordem": 1
        },
        {
            "titulo": "2. Como Utilizamos suas Informações",
            "conteudo": "Utilizamos suas informações para:\n\n- Processar e entregar seus pedidos\n- Comunicar-nos com você sobre seus pedidos, produtos e serviços\n- Enviar informações promocionais (com seu consentimento)\n- Melhorar nossos produtos e serviços\n- Prevenir fraudes e garantir a segurança\n- Cumprir obrigações legais",
            "ordem": 2
        },
        {
            "titulo": "3. Compartilhamento de Informações",
            "conteudo": "Não vendemos suas informações pessoais. Podemos compartilhar suas informações apenas com:\n\n- Prestadores de serviços que nos ajudam a operar nosso negócio (processamento de pagamentos, entrega, etc.)\n- Autoridades legais quando exigido por lei\n- Em caso de fusão, aquisição ou venda de ativos",
            "ordem": 3
        },
        {
            "titulo": "4. Segurança dos Dados",
            "conteudo": "Implementamos medidas de segurança técnicas e organizacionais para proteger suas informações pessoais contra acesso não autorizado, alteração, divulgação ou destruição. Utilizamos criptografia SSL/TLS para transmissão de dados e armazenamento seguro.",
            "ordem": 4
        },
        {
            "titulo": "5. Seus Direitos",
            "conteudo": "Você tem o direito de:\n\n- Acessar suas informações pessoais\n- Corrigir informações incorretas\n- Solicitar a exclusão de seus dados\n- Revogar seu consentimento a qualquer momento\n- Solicitar portabilidade dos dados\n- Opor-se ao processamento de seus dados",
            "ordem": 5
        },
        {
            "titulo": "6. Cookies e Tecnologias Similares",
            "conteudo": "Utilizamos cookies e tecnologias similares para melhorar sua experiência, analisar o uso do site e personalizar conteúdo. Você pode gerenciar suas preferências de cookies através das configurações do seu navegador.",
            "ordem": 6
        },
        {
            "titulo": "7. Retenção de Dados",
            "conteudo": "Mantemos suas informações pessoais apenas pelo tempo necessário para cumprir os propósitos descritos nesta política, a menos que um período de retenção mais longo seja exigido ou permitido por lei.",
            "ordem": 7
        },
        {
            "titulo": "8. Alterações nesta Política",
            "conteudo": "Podemos atualizar esta Política de Privacidade periodicamente. Notificaremos você sobre alterações significativas publicando a nova política nesta página e atualizando a data de \"Última atualização\".",
            "ordem": 8
        },
        {
            "titulo": "9. Contato",
            "conteudo": "Se você tiver dúvidas sobre esta Política de Privacidade ou sobre como tratamos suas informações pessoais, entre em contato conosco através de:\n\n- E-mail: privacidade@lhamabanana.com\n- Telefone: (00) 12345-6789",
            "ordem": 9
        }
    ]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;
