# 📦 Integração Bling - LhamaBanana

## 🎯 Princípios Fundamentais

### Strapi/Admin Local = Fonte da Verdade
- **Criação**: Produtos são criados APENAS localmente
- **Estrutura**: Categorias, estampas, tamanhos, tecidos são criados localmente
- **Preços**: `preco_venda` e `preco_promocional` gerenciados localmente
- **SEO**: Meta tags, descrições, imagens gerenciadas localmente

### Bling = Apenas ERP Operacional/Fiscal
- **Recebe**: Produtos já criados (via API)
- **Gerencia**: Estoque, SKUs, preço fiscal, pedidos, NF-e, financeiro
- **NÃO cria**: Produtos, categorias, estrutura do catálogo

## 🔄 Fluxos de Sincronização

### 1. Criar e Enviar Produto para Bling

```
Admin cria produto → Banco Local → POST /api/bling/produtos/sync/<produto_id> → Bling
```

**O que é enviado:**
- SKU (`codigo_sku`)
- Nome completo (montado)
- Preço de venda (`preco_venda`, NÃO promocional)
- NCM (obrigatório)
- Estoque inicial
- Código de barras (se houver)
- Peso e dimensões (para frete)
- CEST (se houver)

**O que NÃO é enviado:**
- Preço promocional (gerenciado apenas localmente)
- Categoria, estampa, tamanho (estrutura não é enviada, apenas no nome)

### 2. Sincronizar Estoque do Bling → Local

```
Bling (alterado estoque) → Webhook → Banco Local
```

**Webhook:** `POST /api/webhook/bling` (eventos: `stock.created`, `stock.updated`)

**O que é atualizado:**
- Campo `estoque` no produto local
- Nenhum outro campo é alterado

**Sincronização manual:**
```bash
docker-compose exec flask python scripts/sync_estoque_bling.py
```

### 3. Criar Pedido no Bling

```
Checkout → POST /api/checkout/process → Criar pedido no Bling → Banco Local
```

**O que é enviado:**
- Dados do cliente
- Itens do pedido (SKU, quantidade, preço)
- Endereço de entrega
- Forma de pagamento
- Dados fiscais (CPF/CNPJ)

### 4. Emitir NF-e

```
Pedido aprovado → Webhook → Preparar NF-e → POST /api/bling/nfe/emitir → Bling
```

**Webhook:** `POST /api/webhook/bling` (evento: `invoice.created`)

## 🔐 OAuth 2.0

### Configuração Inicial

1. **Criar aplicação no Bling:**
   - Acesse: https://www.bling.com.br/configuracoes/api-tokens
   - Crie nova aplicação
   - Configure redirect URI: `http://seudominio.com/api/bling/callback`

2. **Configurar no `.env`:**
```bash
BLING_CLIENT_ID=seu-client-id
BLING_CLIENT_SECRET=seu-client-secret
BLING_REDIRECT_URI=http://seudominio.com/api/bling/callback
```

3. **Autorizar aplicação:**
   - Acesse: `http://seudominio.com/api/bling/authorize`
   - Faça login no Bling
   - Autorize as permissões necessárias

### Permissões Necessárias (Scopes)
- `produtos` - Sincronizar catálogo
- `pedidos` - Criar e gerenciar pedidos
- `nfe` - Emitir NF-e
- `estoques` - Controlar estoque
- `contatos` - Gerenciar clientes
- `financeiro` - Contas a receber/pagar

### Renovação de Token
- Tokens são renovados automaticamente quando expiram
- Para renovar manualmente: `http://seudominio.com/api/bling/authorize`

## 📡 Webhooks

### Configuração no Bling

1. Acesse: Bling > Configurações > Webhooks
2. Configure URL: `http://seudominio.com/api/webhook/bling`
3. Selecione eventos:
   - `stock.created` - Estoque criado
   - `stock.updated` - Estoque atualizado
   - `stock.deleted` - Estoque deletado
   - `invoice.created` - NF-e criada
   - `invoice.updated` - NF-e atualizada

### Eventos Processados

#### Estoque
- **stock.created/updated**: Atualiza `estoque` no produto local
- **stock.deleted**: Loga evento (mantém estoque atual)

#### NF-e
- **invoice.created**: Prepara dados para emissão
- **invoice.updated**: Atualiza status da NF-e

## 🔧 Endpoints da API

### Produtos
- `POST /api/bling/produtos/sync/<produto_id>` - Sincronizar produto específico
- `POST /api/bling/produtos/sync-all` - Sincronizar todos os produtos

### Estoque
- `POST /api/bling/estoque/sync-from-bling` - Sincronizar estoque do Bling
- `POST /api/bling/estoque/sync/<produto_id>` - Sincronizar produto específico

### Pedidos
- Criados automaticamente no checkout via `checkout_service.py`

### NF-e
- `POST /api/bling/nfe/emitir/<venda_id>` - Emitir NF-e para venda
- `GET /api/bling/nfe/status/<venda_id>` - Verificar status da NF-e

## 📊 Estrutura de Dados

### Produto no Bling
```json
{
  "nome": "Pijama Adulto - Dinossauro Verde Ultra Soft - M",
  "codigo": "PIJ-ADUL-DIN-VER-M",
  "preco": 89.90,
  "ncm": "61099000",
  "cest": "0300700",
  "estoque": {
    "atual": 10
  },
  "peso": 0.5,
  "largura": 30,
  "altura": 5,
  "comprimento": 40
}
```

### Mapeamento de Campos

| Local (Strapi) | Bling | Observação |
|----------------|-------|------------|
| `codigo_sku` | `codigo` | Obrigatório, único |
| `nome_produto.nome` + variações | `nome` | Montado automaticamente |
| `preco_venda` | `preco` | NÃO envia promocional |
| `ncm` | `ncm` | Obrigatório (8 dígitos) |
| `cest` | `cest` | Opcional (7 dígitos) |
| `estoque` | `estoque.atual` | Sincronizado via webhook |
| `peso_kg` | `peso` | Para cálculo de frete |
| `dimensoes_*` | `largura/altura/comprimento` | Para cálculo de frete |

## ⚠️ Importante

### Estoque
- **Fonte da verdade**: Bling
- **Sincronização**: Automática via webhook
- **Manual**: Script `sync_estoque_bling.py`

### Preços
- **Preço de venda**: Sincronizado com Bling
- **Preço promocional**: Apenas local (não vai para Bling)

### Produtos
- **Criação**: Apenas local (Strapi)
- **Envio**: Manual via API ou admin
- **Estrutura**: Categorias, estampas, etc. não são enviadas

## 🐛 Troubleshooting

### Token expirado
```bash
# Renovar token
curl http://seudominio.com/api/bling/authorize
```

### Estoque não sincroniza
1. Verificar webhook configurado no Bling
2. Verificar logs: `docker-compose logs flask | grep webhook`
3. Sincronizar manualmente: `python scripts/sync_estoque_bling.py`

### Produto não aparece no Bling
1. Verificar se foi sincronizado: `GET /api/bling/produtos/<produto_id>`
2. Verificar logs de erro
3. Tentar sincronizar novamente: `POST /api/bling/produtos/sync/<produto_id>`
