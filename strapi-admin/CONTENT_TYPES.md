# Content Types Criados no Strapi

Este documento descreve todos os Content Types criados para o painel administrativo do LhamaBanana.

## 📦 Gestão de Produtos

### 1. Categoria (`categoria`)
- **Descrição**: Categorias de produtos e estampas
- **Campos principais**:
  - `nome` (string, único, obrigatório)
  - `descricao` (text)
  - `ordem_exibicao` (integer)
  - `ativo` (boolean)
  - `imagem_url` (string)
- **Relações**: 
  - `nome_produtos` (oneToMany)
  - `estampas` (oneToMany)

### 2. Tamanho (`tamanho`)
- **Descrição**: Tamanhos disponíveis para produtos
- **Campos principais**:
  - `nome` (string, único, obrigatório)
  - `ordem_exibicao` (integer)
  - `ativo` (boolean)
- **Relações**: 
  - `produtos` (oneToMany)

### 3. Estampa (`estampa`)
- **Descrição**: Estampas disponíveis para produtos
- **Campos principais**:
  - `nome` (string, único, obrigatório)
  - `descricao` (text)
  - `imagem_url` (string, obrigatório)
  - `categoria` (relation → categoria)
  - `sexo` (enum: m/f/u)
  - `custo_por_metro` (decimal, obrigatório)
  - `ativo` (boolean)
  - `ordem_exibicao` (integer)
- **Relações**: 
  - `produtos` (oneToMany)

### 4. Nome do Produto (`nome-produto`)
- **Descrição**: Nomes e descrições base dos produtos
- **Campos principais**:
  - `nome` (string, único, obrigatório)
  - `descricao` (text)
  - `descricao_curta` (string)
  - `categoria` (relation → categoria)
  - `tags` (json array)
  - `peso_kg` (decimal)
  - `dimensoes_largura/altura/comprimento` (decimal)
  - `ativo` (boolean)
  - `destaque` (boolean)
  - `ordem_exibicao` (integer)
  - `meta_title`, `meta_description` (SEO)
  - `slug` (string, único)
- **Relações**: 
  - `produtos` (oneToMany)

### 5. Produto (`produto`)
- **Descrição**: Variações de produtos com estoque
- **Campos principais**:
  - `nome_produto` (relation → nome-produto)
  - `estampa` (relation → estampa)
  - `tamanho` (relation → tamanho)
  - `custo` (decimal, obrigatório)
  - `preco_venda` (decimal, obrigatório)
  - `preco_promocional` (decimal)
  - `estoque` (integer, obrigatório)
  - `estoque_minimo` (integer)
  - `estoque_reservado` (integer)
  - `codigo_sku` (string, único, obrigatório)
  - `codigo_barras` (string)
  - `ativo` (boolean)
- **Relações**: 
  - `imagens` (oneToMany → imagem-produto)

### 6. Imagem do Produto (`imagem-produto`)
- **Descrição**: Imagens dos produtos
- **Campos principais**:
  - `produto` (relation → produto)
  - `url` (string, obrigatório)
  - `ordem` (integer)
  - `descricao` (string)
  - `is_thumbnail` (boolean)

## 🛒 Gestão de Vendas e Pedidos

### 7. Venda / Pedido (`venda`)
- **Descrição**: Pedidos e vendas do sistema
- **Campos principais**:
  - `codigo_pedido` (string, único, obrigatório)
  - `usuario` (relation → usuario)
  - `data_venda` (datetime)
  - `valor_total`, `valor_frete`, `valor_desconto`, `valor_subtotal` (decimal)
  - `cupom` (relation → cupom)
  - Dados de endereço de entrega (snapshot)
  - `status_pedido` (enum: pendente, pendente_pagamento, processando_envio, enviado, entregue, cancelado_pelo_cliente, cancelado_pelo_vendedor, devolvido, reembolsado)
  - `prioridade` (integer: 0=normal, 1=alta, 2=urgente)
  - `responsavel` (relation → usuario)
  - `observacoes` (text)
  - `observacoes_cliente` (text)
- **Relações**: 
  - `itens` (oneToMany → item-venda)
  - `pagamentos` (oneToMany → pagamento)
  - `etiquetas_frete` (oneToMany → etiqueta-frete)
  - `status_historico` (oneToMany → venda-status-historico)

### 8. Item da Venda (`item-venda`)
- **Descrição**: Itens de cada venda
- **Campos principais**:
  - `venda` (relation → venda)
  - `produto` (relation → produto)
  - `quantidade` (integer, obrigatório)
  - `preco_unitario` (decimal, obrigatório)
  - `subtotal` (decimal, obrigatório)
  - `nome_produto_snapshot` (string) - snapshot do produto no momento da venda
  - `sku_produto_snapshot` (string)
  - `detalhes_produto_snapshot` (json)

### 9. Histórico de Status da Venda (`venda-status-historico`)
- **Descrição**: Histórico de alterações de status dos pedidos
- **Campos principais**:
  - `venda` (relation → venda)
  - `status_anterior` (string)
  - `status_novo` (string, obrigatório)
  - `motivo` (text)
  - `observacoes` (text)
  - `usuario` (relation → usuario)
  - `origem` (enum: sistema, admin, webhook, cliente)

## 👥 Gestão de Usuários

### 10. Usuário (`usuario`)
- **Descrição**: Usuários e clientes do sistema
- **Campos principais**:
  - `firebase_uid` (string, único, obrigatório)
  - `nome` (string, obrigatório)
  - `email` (email, único, obrigatório)
  - `genero` (enum: m/f/u)
  - `cpf` (string, único)
  - `telefone` (string)
  - `data_nascimento` (date)
  - `ultimo_login` (datetime)
  - `imagem_url` (string)
  - `role` (enum: user/admin/moderator)
  - `ativo` (boolean)
  - `email_verificado` (boolean)
  - `aceita_marketing` (boolean)
  - `total_pedidos` (integer)
  - `total_gasto` (decimal)
- **Relações**: 
  - `enderecos` (oneToMany → endereco)
  - `vendas` (oneToMany → venda)

### 11. Endereço (`endereco`)
- **Descrição**: Endereços de entrega dos usuários
- **Campos principais**:
  - `usuario` (relation → usuario)
  - `nome_endereco` (string, obrigatório)
  - `cep`, `rua`, `numero`, `complemento`, `bairro`, `cidade`, `estado` (strings)
  - `referencia` (string)
  - `is_default` (boolean)
  - `email`, `telefone` (string)
  - `ativo` (boolean)

## 🎟️ Gestão de Cupons

### 12. Cupom (`cupom`)
- **Descrição**: Cupons de desconto
- **Campos principais**:
  - `codigo` (string, único, obrigatório)
  - `tipo` (enum: p=percentual, v=valor fixo)
  - `valor` (decimal, obrigatório)
  - `valor_minimo_pedido` (decimal)
  - `validade_inicio`, `validade_fim` (datetime)
  - `uso_maximo` (integer)
  - `uso_maximo_por_usuario` (integer)
  - `uso_atual` (integer)
  - `ativo` (boolean)
  - `descricao` (text)
- **Relações**: 
  - `vendas` (oneToMany → venda)
  - `cupons_usados` (oneToMany → cupom-usado)

### 13. Cupom Usado (`cupom-usado`)
- **Descrição**: Registro de uso de cupons
- **Campos principais**:
  - `cupom` (relation → cupom)
  - `usuario` (relation → usuario)
  - `venda` (relation → venda)
  - `valor_desconto_aplicado` (decimal, obrigatório)
  - `data_uso` (datetime)

## 💳 Gestão de Pagamentos

### 14. Pagamento (`pagamento`)
- **Descrição**: Pagamentos das vendas
- **Campos principais**:
  - `venda` (relation → venda)
  - `pagbank_transaction_id` (string, único)
  - `pagbank_order_id` (string)
  - `forma_pagamento_tipo` (enum: CREDIT_CARD, PIX, BOLETO)
  - `bandeira_cartao` (string)
  - `parcelas`, `valor_parcela` (integer, decimal)
  - `valor_pago`, `valor_original` (decimal)
  - `status_pagamento` (enum: PENDING, AUTHORIZED, PAID, WAITING, DECLINED, REFUNDED, CHARGEBACK, CANCELLED, EXPIRED)
  - `pagbank_qrcode_link`, `pagbank_qrcode_image`, `pagbank_qrcode_text` (text) - Para PIX
  - `pagbank_boleto_link`, `pagbank_barcode_data`, `pagbank_boleto_expires_at` - Para Boleto
  - `cartao_ultimos_digitos`, `cartao_primeiros_digitos` (string) - Para Cartão
  - `json_resposta_api` (json)
  - `tentativas` (integer)
- **Relações**: 
  - `status_historico` (oneToMany → pagamento-status-historico)

### 15. Histórico de Status do Pagamento (`pagamento-status-historico`)
- **Descrição**: Histórico de alterações de status dos pagamentos
- **Campos principais**:
  - `pagamento` (relation → pagamento)
  - `status_anterior` (string)
  - `status_novo` (string, obrigatório)
  - `origem` (enum: webhook, manual, sistema)
  - `dados_adicionais` (json)

## 📦 Gestão de Frete e Etiquetas (COMPLETO)

### 16. Etiqueta de Frete (`etiqueta-frete`) ⭐
- **Descrição**: Etiquetas de frete para envio de pedidos - **Gestão completa de embalagem e impressão**
- **Campos principais**:
  - `venda` (relation → venda) - **Link com o pedido completo**
  - `codigo_pedido` (string)
  - Dados do Melhor Envio:
    - `melhor_envio_shipment_id`, `melhor_envio_protocol`
    - `melhor_envio_service_id`, `melhor_envio_service_name`
  - `status_etiqueta` (enum: pendente, criada, paga, impressa, cancelada, erro, em_transito, entregue)
  - `transportadora_nome`, `transportadora_codigo` (string)
  - Dados de envio:
    - `cep_origem`, `cep_destino` (string, obrigatório)
    - `peso_total`, `valor_frete` (decimal)
    - `dimensoes` (json)
  - URLs e rastreamento:
    - `url_etiqueta` (text) - **URL para visualizar/baixar etiqueta**
    - `url_rastreamento` (text) - **URL de rastreamento**
    - `codigo_rastreamento` (string) - **Código de rastreamento**
  - `dados_etiqueta_json` (json) - **Dados completos da etiqueta**
  - `erro_mensagem`, `erro_detalhes` (text, json) - Para tratamento de erros
  - Timestamps:
    - `paga_em`, `impressa_em`, `enviada_em`, `entregue_em` (datetime)

**Funcionalidades disponíveis através da relação com `venda`:**
- ✅ Visualizar produtos do pedido através de `venda.itens`
- ✅ Ver detalhes completos do pedido
- ✅ Imprimir etiqueta usando `url_etiqueta`
- ✅ Rastrear envio usando `url_rastreamento` ou `codigo_rastreamento`
- ✅ Gerenciar status de embalagem (pendente → criada → paga → impressa → enviada → entregue)

## ⚙️ Configurações

### 17. Configuração (`configuracao`)
- **Descrição**: Configurações gerais do sistema
- **Campos principais**:
  - `chave` (string, único, obrigatório)
  - `valor` (json)
  - `tipo` (string)
  - `descricao` (text)
  - `ativo` (boolean)

---

## 🚀 Como Testar

### 1. Reiniciar o Strapi
```bash
cd Lhama-Banana
docker compose restart strapi
```

### 2. Acessar o Painel Admin
- Acesse: `http://localhost:1337/admin`
- Faça login (primeira vez precisa criar conta admin)

### 3. Verificar Content Types
- No menu lateral, você verá todos os Content Types criados
- Eles estarão organizados por categoria

### 4. Testar CRUD
1. **Criar uma Categoria**:
   - Vá em "Categoria" → "Create new entry"
   - Preencha nome, descrição, etc.
   - Salve

2. **Criar um Tamanho**:
   - Vá em "Tamanho" → "Create new entry"
   - Preencha nome (ex: "P", "M", "G")
   - Salve

3. **Criar uma Estampa**:
   - Vá em "Estampa" → "Create new entry"
   - Preencha nome, imagem_url, categoria, etc.
   - Salve

4. **Criar um Nome de Produto**:
   - Vá em "Nome do Produto" → "Create new entry"
   - Preencha nome, categoria, etc.
   - Salve

5. **Criar um Produto**:
   - Vá em "Produto" → "Create new entry"
   - Selecione nome_produto, estampa, tamanho
   - Preencha preço, estoque, SKU
   - Salve

### 5. Testar Relações
- Ao criar um Produto, você pode ver as relações com Nome do Produto, Estampa e Tamanho
- Ao criar uma Venda, você pode adicionar Itens da Venda
- Ao criar uma Etiqueta de Frete, você pode selecionar a Venda relacionada

### 6. Testar Gestão de Frete
1. **Criar uma Venda** (ou usar uma existente)
2. **Criar uma Etiqueta de Frete**:
   - Vá em "Etiqueta de Frete" → "Create new entry"
   - Selecione a Venda
   - Preencha dados de envio (CEP origem/destino, peso, etc.)
   - Salve
3. **Visualizar produtos do pedido**:
   - Na Etiqueta de Frete criada, clique na relação "Venda"
   - Na Venda, veja os "Itens" para ver todos os produtos
4. **Imprimir etiqueta**:
   - Use o campo `url_etiqueta` para acessar/baixar a etiqueta
   - Ou use `codigo_rastreamento` para rastrear

---

## 📝 Próximos Passos

1. **Configurar Permissões**: Definir quais roles podem acessar/criar/editar cada Content Type
2. **Criar Views Customizadas**: Para gestão de frete com visualização de produtos e impressão
3. **Adicionar Validações**: Validações customizadas nos campos
4. **Criar Hooks**: Para atualizar estoque automaticamente, gerar códigos, etc.
5. **Configurar Filtros**: Filtros avançados para busca de pedidos, produtos, etc.

---

## ⚠️ Observações Importantes

1. **Relações**: Todas as relações foram configuradas corretamente. Certifique-se de criar os registros na ordem correta (ex: Categoria antes de Nome do Produto).

2. **Campos Obrigatórios**: Alguns campos são obrigatórios. O Strapi não permitirá salvar sem preenchê-los.

3. **Enums**: Os campos enum têm valores fixos. Use apenas os valores especificados.

4. **JSON Fields**: Campos do tipo JSON podem armazenar objetos complexos. Use para dados flexíveis.

5. **Timestamps**: Campos `criado_em` e `atualizado_em` são gerenciados automaticamente pelo Strapi (se configurado).

6. **Gestão de Frete**: A relação `venda` na Etiqueta de Frete permite acessar todos os produtos do pedido através de `venda.itens`, facilitando a gestão completa de embalagem.



