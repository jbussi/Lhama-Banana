# 📋 Resumo da Integração Bling - LhamaBanana

## ✅ Implementação Completa

### 1. Autenticação OAuth 2.0
- ✅ Fluxo de autorização completo
- ✅ Gerenciamento de tokens (renovação automática)
- ✅ Endpoints de status e revogação

### 2. Sincronização de Produtos
- ✅ **Local → Bling**: Criar/atualizar produtos no Bling
- ✅ **Bling → Local**: Importar produtos do Bling
- ✅ Validações (NCM, SKU, preço)
- ✅ Mapeamento completo de campos

### 3. Sincronização de Estoque
- ✅ **Bling → Local**: Atualizar estoque do Bling para o site
- ✅ **Local → Bling**: Atualizar estoque do site para o Bling
- ✅ Bidirecional: ambas as direções

### 4. Sincronização de Pedidos/Vendas
- ✅ **Criação Automática**: Quando pagamento é confirmado
- ✅ **Sincronização Manual**: Endpoint para sincronizar pedidos
- ✅ **Atualização de Status**: Do Bling para o site
- ✅ **Rastreamento de NF-e**: Quando emitida

### 5. Estrutura de Banco de Dados
- ✅ Tabela `bling_tokens` (tokens OAuth)
- ✅ Tabela `bling_produtos` (referência produtos)
- ✅ Tabela `bling_pedidos` (referência pedidos)
- ✅ Tabela `bling_sync_logs` (logs de sincronização)

## 🔄 Fluxos Automáticos

### Fluxo 1: Venda Completa
```
1. Cliente faz checkout
   ↓
2. Pagamento processado (PagBank)
   ↓
3. Pagamento confirmado (webhook)
   ↓
4. Pedido criado automaticamente no Bling ✅
   ↓
5. Produtos e valores sincronizados
```

### Fluxo 2: Atualização de Status
```
1. Status alterado no Bling
   ↓
2. POST /api/bling/pedidos/status/<venda_id>
   ↓
3. Status atualizado no site ✅
```

### Fluxo 3: Sincronização de Estoque
```
1. Estoque alterado no Bling
   ↓
2. POST /api/bling/estoque/sync-from-bling
   ↓
3. Estoque atualizado no site ✅
```

## 📡 Endpoints Disponíveis

### Autenticação
- `GET /api/bling/authorize` - Iniciar autorização
- `GET /api/bling/callback` - Callback OAuth
- `GET /api/bling/tokens` - Ver tokens
- `POST /api/bling/revoke` - Revogar autorização
- `GET /api/bling/status` - Status da integração
- `GET /api/bling/test` - Testar conexão

### Produtos
- `POST /api/bling/produtos/sync/<id>` - Sincronizar produto
- `POST /api/bling/produtos/sync-all` - Sincronizar todos
- `POST /api/bling/produtos/import` - Importar do Bling
- `GET /api/bling/produtos/status/<id>` - Ver status

### Estoque
- `POST /api/bling/estoque/sync-from-bling` - Do Bling para local
- `POST /api/bling/estoque/sync-to-bling` - Do local para Bling
- `POST /api/bling/estoque/sync/<id>` - Bidirecional

### Pedidos
- `POST /api/bling/pedidos/sync/<venda_id>` - Sincronizar pedido
- `POST /api/bling/pedidos/status/<venda_id>` - Atualizar status
- `POST /api/bling/pedidos/status/sync-all` - Atualizar todos
- `GET /api/bling/pedidos/info/<venda_id>` - Ver informações

## 🗄️ Tabelas do Banco

### bling_tokens
Armazena tokens OAuth do Bling (access_token, refresh_token, expires_at)

### bling_produtos
Rastreia produtos sincronizados:
- `produto_id` → ID local
- `bling_id` → ID no Bling
- `bling_codigo` → SKU no Bling
- `status_sincronizacao` → 'sync', 'error', 'pending'

### bling_pedidos
Rastreia pedidos sincronizados:
- `venda_id` → ID da venda local
- `bling_pedido_id` → ID do pedido no Bling
- `bling_nfe_id` → ID da NF-e (quando emitida)
- `nfe_numero`, `nfe_chave_acesso`, `nfe_status`

### bling_sync_logs
Logs de todas as sincronizações:
- `entity_type` → 'produto', 'pedido', 'nfe', 'cliente'
- `action` → 'create', 'update', 'sync', 'delete'
- `status` → 'success', 'error', 'pending'
- `response_data` → JSONB com resposta da API

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```bash
# Bling OAuth
BLING_CLIENT_ID=seu_client_id
BLING_CLIENT_SECRET=seu_client_secret
BLING_REDIRECT_URI=https://seu-dominio.ngrok-free.dev/api/bling/callback

# URL Base (para webhooks)
NGROK_URL=https://seu-dominio.ngrok-free.dev

# Sincronização Automática (opcional)
BLING_SYNC_ENABLED=true
BLING_SYNC_INTERVAL_STOCK=15  # minutos
BLING_SYNC_INTERVAL_PRODUCTS=360  # minutos (6h)
BLING_WEBHOOK_SECRET=seu_token_secreto
```

## 🚀 Setup Inicial

### 1. Criar Tabelas
```bash
# Executar script SQL
Get-Content sql/create-bling-tables.sql | docker compose exec -T postgres psql -U postgres -d sistema_usuarios
```

### 2. Configurar OAuth
1. Criar aplicação no Bling: https://www.bling.com.br/dev
2. Configurar redirect URI: `https://seu-dominio.ngrok-free.dev/api/bling/callback`
3. Adicionar `BLING_CLIENT_ID` e `BLING_CLIENT_SECRET` no `.env`

### 3. Autorizar Bling
```
GET https://seu-dominio.ngrok-free.dev/api/bling/authorize
```

### 4. Sincronizar Produtos
```powershell
# Importar produtos do Bling ou sincronizar locais
POST /api/bling/produtos/import
POST /api/bling/produtos/sync-all
```

## 📚 Documentação Detalhada

- [BLING_SINCRONIZACAO_PRODUTOS.md](BLING_SINCRONIZACAO_PRODUTOS.md) - Produtos
- [BLING_SINCRONIZACAO_COMPLETA.md](BLING_SINCRONIZACAO_COMPLETA.md) - Sincronização completa
- [BLING_SINCRONIZACAO_PEDIDOS.md](BLING_SINCRONIZACAO_PEDIDOS.md) - Pedidos
- [BLING_OAUTH_SETUP.md](BLING_OAUTH_SETUP.md) - Setup OAuth

## 🎯 Próximos Passos Sugeridos

1. ⏳ Implementar webhook do Bling (quando disponível)
2. ⏳ Worker de polling periódico (estoque a cada 15min)
3. ⏳ Emissão automática de NF-e após pagamento
4. ⏳ Integração com logística (rastreamento)
5. ⏳ Dashboard de sincronização

## 🔍 Troubleshooting

### Problema: Produtos não sincronizam
- Verificar se NCM está preenchido (8 dígitos)
- Verificar se SKU está preenchido
- Verificar logs: `SELECT * FROM bling_sync_logs WHERE entity_type = 'produto'`

### Problema: Pedido não criado automaticamente
- Verificar se pagamento foi confirmado
- Verificar se produtos estão sincronizados
- Sincronizar manualmente: `POST /api/bling/pedidos/sync/<venda_id>`

### Problema: Token expirado
- Renovar automaticamente ou reautorizar: `GET /api/bling/authorize`

## ✅ Status da Implementação

- ✅ OAuth 2.0 completo
- ✅ Sincronização de produtos (bidirecional)
- ✅ Sincronização de estoque (bidirecional)
- ✅ Sincronização de pedidos
- ✅ Criação automática de pedidos
- ✅ Atualização de status
- ✅ Logs e rastreamento
- ⏳ Webhooks (pendente API do Bling)
- ⏳ Polling periódico (pendente implementação worker)

