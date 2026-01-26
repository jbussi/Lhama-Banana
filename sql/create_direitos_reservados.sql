-- =====================================================
-- TABELA: TODOS OS DIREITOS RESERVADOS
-- =====================================================
-- Armazena conteúdo da página de direitos reservados

CREATE TABLE IF NOT EXISTS direitos_reservados (
    id SERIAL PRIMARY KEY,
    
    -- Título e conteúdo
    titulo VARCHAR(255) DEFAULT 'Todos os Direitos Reservados',
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
CREATE INDEX IF NOT EXISTS idx_direitos_reservados_ativo ON direitos_reservados(ativo);

-- Comentários
COMMENT ON TABLE direitos_reservados IS 'Conteúdo da página de direitos reservados';
COMMENT ON COLUMN direitos_reservados.conteudo IS 'Texto introdutório da página';
COMMENT ON COLUMN direitos_reservados.secoes IS 'Array JSON com seções da página';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_direitos_reservados_timestamp
    BEFORE UPDATE ON direitos_reservados
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Inserir registro padrão
INSERT INTO direitos_reservados (
    titulo,
    ultima_atualizacao,
    conteudo,
    secoes,
    ativo
) VALUES (
    'Todos os Direitos Reservados',
    CURRENT_DATE,
    'A LhamaBanana™ respeita e protege os direitos de propriedade intelectual. Esta página descreve os direitos reservados sobre nosso conteúdo, marcas, produtos e serviços.',
    '[
        {
            "titulo": "1. Propriedade Intelectual",
            "conteudo": "Todo o conteúdo deste site, incluindo textos, gráficos, logotipos, ícones, imagens, clipes de áudio, downloads digitais, compilações de dados e software, é propriedade da LhamaBanana™ ou de seus fornecedores de conteúdo e está protegido pelas leis de direitos autorais brasileiras e internacionais.",
            "ordem": 1
        },
        {
            "titulo": "2. Marca Registrada",
            "conteudo": "LhamaBanana™, o logotipo LhamaBanana e todas as marcas relacionadas, nomes comerciais, marcas de serviço e slogans exibidos neste site são marcas registradas ou não registradas da LhamaBanana™ ou de seus afiliados. Você não pode usar essas marcas sem nossa prévia autorização por escrito.",
            "ordem": 2
        },
        {
            "titulo": "3. Uso do Conteúdo",
            "conteudo": "O conteúdo deste site é fornecido apenas para fins informativos e de compra. Você não pode:\n\n- Copiar, reproduzir, distribuir, transmitir, exibir, publicar, licenciar ou criar trabalhos derivados de qualquer parte deste site sem nossa prévia autorização por escrito\n- Usar qualquer conteúdo para fins comerciais sem nossa autorização\n- Remover ou alterar qualquer aviso de direitos autorais ou marca registrada",
            "ordem": 3
        },
        {
            "titulo": "4. Produtos e Design",
            "conteudo": "Todos os produtos, designs, estampas, padrões e criações originais da LhamaBanana™ são protegidos por direitos autorais e propriedade intelectual. A reprodução não autorizada de nossos produtos ou designs é estritamente proibida.",
            "ordem": 4
        },
        {
            "titulo": "5. Imagens e Fotografias",
            "conteudo": "Todas as imagens, fotografias e materiais visuais exibidos neste site são propriedade da LhamaBanana™ ou licenciados para nosso uso. O uso não autorizado dessas imagens é proibido.",
            "ordem": 5
        },
        {
            "titulo": "6. Software e Tecnologia",
            "conteudo": "Qualquer software usado neste site, incluindo código-fonte, scripts, aplicativos e tecnologias relacionadas, é propriedade da LhamaBanana™ ou de seus licenciadores e está protegido por leis de direitos autorais e outras leis de propriedade intelectual.",
            "ordem": 6
        },
        {
            "titulo": "7. Violação de Direitos",
            "conteudo": "Reservamo-nos o direito de tomar medidas legais contra qualquer pessoa que viole nossos direitos de propriedade intelectual, incluindo, mas não limitado a, solicitar indenização por danos e requerer medidas cautelares.",
            "ordem": 7
        },
        {
            "titulo": "8. Links para Terceiros",
            "conteudo": "Este site pode conter links para sites de terceiros. Não somos responsáveis pelo conteúdo ou políticas de privacidade desses sites. O uso de links para sites de terceiros é por sua conta e risco.",
            "ordem": 8
        },
        {
            "titulo": "9. Alterações",
            "conteudo": "Reservamo-nos o direito de modificar este aviso a qualquer momento. As alterações entrarão em vigor imediatamente após a publicação neste site.",
            "ordem": 9
        },
        {
            "titulo": "10. Contato",
            "conteudo": "Para questões relacionadas a direitos autorais, marcas registradas ou propriedade intelectual, entre em contato:\n\n- E-mail: legal@lhamabanana.com\n- Telefone: (00) 12345-6789",
            "ordem": 10
        }
    ]'::jsonb,
    TRUE
) ON CONFLICT DO NOTHING;
