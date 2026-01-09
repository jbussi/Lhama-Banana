# 📦 Sincronização de Pedidos/Vendas com Bling

## ✅ Funcionalidades Implementadas

### 1. Criação Automática de Pedidos no Bling
- ✅ Quando pagamento é confirmado no PagBank, pedido é criado automaticamente no Bling
- ✅ Sincronização manual de pedidos
- ✅ Mapeamento completo de dados (cliente, itens, endereço, frete, desconto)

### 2. Atualização de Status
- ✅ Sincronização de status do Bling para o site
- ✅ Mapeamento de situações do Bling para status locais
- ✅ Rastreamento de NF-e (quando emitida)

### 3. Integração Completa
- ✅ Integrado ao webhook do PagBank
- ✅ Criação automática após pagamento confirmado
- ✅ Logs detalhados de todas as operações

## 📡 Endpoints Disponíveis

### 1. Sincronizar Pedido para Bling

```
POST /api/bling/pedidos/sync/<venda_id>
```

**Exemplo:**
```powershell
$uri = "$ngrokUrl/api/bling/pedidos/sync/123"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "action": "create",
  "bling_pedido_id": 45678,
  "message": "Pedido sincronizado com sucesso (create)"
}
```

### 2. Sincronizar Status do Pedido (Bling → Local)

```
POST /api/bling/pedidos/status/<venda_id>
```

**Exemplo:**
```powershell
$uri = "$ngrokUrl/api/bling/pedidos/status/123"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"
```

**Resposta:**
```json
{
  "success": true,
  "status": "enviado",
  "situacao_bling": "E",
  "message": "Status atualizado com sucesso"
}
```

### 3. Sincronizar Status de Todos os Pedidos

```
POST /api/bling/pedidos/status/sync-all
```

**Exemplo:**
```powershell
$uri = "$ngrokUrl/api/bling/pedidos/status/sync-all"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"
```

**Resposta:**
```json
{
  "success": true,
  "message": "Sincronização de status concluída",
  "total": 10,
  "success": 9,
  "errors": 1,
  "results": [...]
}
```

### 4. Verificar Status de Sincronização

```
GET /api/bling/pedidos/info/<venda_id>
```

**Exemplo:**
```powershell
$uri = "$ngrokUrl/api/bling/pedidos/info/123"
Invoke-RestMethod -Uri $uri -Method GET -Headers @{"ngrok-skip-browser-warning"="true"}
```

**Resposta (Sincronizado):**
```json
{
  "synced": true,
  "bling_pedido_id": 45678,
  "bling_nfe_id": 12345,
  "nfe_numero": 123456,
  "nfe_status": "AUTORIZADA",
  "ultima_sincronizacao": "2026-01-09T18:00:00"
}
```

**Resposta (Não Sincronizado):**
```json
{
  "synced": false,
  "message": "Pedido não sincronizado com Bling"
}
```

## 🔄 Fluxo Automático

### Criação Automática de Pedido

```
1. Cliente faz checkout no site
   ↓
2. Pagamento processado no PagBank
   ↓
3. PagBank confirma pagamento (PAID/AUTHORIZED)
   ↓
4. Webhook do PagBank recebe notificação
   ↓
5. Pedido criado automaticamente no Bling
   ↓
6. Referência salva em bling_pedidos
```

### Atualização de Status

```
1. Status do pedido alterado no Bling
   ↓
2. POST /api/bling/pedidos/status/<venda_id>
   ↓
3. Status atualizado no banco local
   ↓
4. Se NF-e foi emitida, dados salvos
```

## 📊 Mapeamento de Status

### Status Local → Situação Bling

| Status Local | Situação Bling | Descrição |
|--------------|----------------|-----------|
| `pendente_pagamento` | `P` | Pendente |
| `processando_envio` | `E` | Em aberto |
| `enviado` | `E` | Em aberto |
| `entregue` | `B` | Baixado |
| `cancelado_*` | `C` | Cancelado |

### Situação Bling → Status Local

| Situação Bling | Status Local | Descrição |
|----------------|--------------|-----------|
| `A` | `pendente_pagamento` | Aberto |
| `E` | `processando_envio` | Em aberto |
| `B` | `entregue` | Baixado |
| `F` | `enviado` | Faturado |
| `C` | `cancelado_pelo_vendedor` | Cancelado |
| `P` | `pendente_pagamento` | Pendente |

## 📋 Dados Sincronizados

### Dados do Cliente
- Nome
- CPF/CNPJ
- Inscrição Estadual (se CNPJ)
- Email
- Telefone/Celular

### Endereço de Entrega
- Rua, número, complemento
- Bairro
- Cidade, Estado, CEP

### Itens do Pedido
- Produto (via referência Bling)
- Quantidade
- Preço unitário
- Subtotal

### Valores
- Valor total
- Frete
- Desconto (cupons)

### Observações
- Código do pedido local
- Origem (site LhamaBanana)

## ⚠️ Requisitos

### Para Sincronização Automática Funcionar

1. ✅ Produtos devem estar sincronizados com Bling
   - Itens sem referência Bling podem falhar
   - Produto precisa ter `bling_produto_id`

2. ✅ Dados do cliente completos
   - CPF/CNPJ obrigatório
   - Endereço completo

3. ✅ Bling autorizado
   - Tokens OAuth válidos
   - Verificar: `GET /api/bling/tokens`

## 🔍 Verificar Logs

### Ver pedidos sincronizados

```sql
SELECT 
    v.id,
    v.codigo_pedido,
    v.status_pedido,
    bp.bling_pedido_id,
    bp.nfe_numero,
    bp.nfe_status,
    bp.updated_at
FROM vendas v
JOIN bling_pedidos bp ON v.id = bp.venda_id
ORDER BY bp.updated_at DESC;
```

### Ver logs de sincronização

```sql
SELECT * FROM bling_sync_logs 
WHERE entity_type = 'pedido' 
ORDER BY created_at DESC 
LIMIT 20;
```

## 🧪 Testar

### Teste 1: Sincronizar Pedido Manualmente

```powershell
# Substituir 123 pelo ID da venda
$uri = "$ngrokUrl/api/bling/pedidos/sync/123"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json" | ConvertTo-Json -Depth 10
```

### Teste 2: Verificar Status

```powershell
# Ver se pedido está sincronizado
$uri = "$ngrokUrl/api/bling/pedidos/info/123"
Invoke-RestMethod -Uri $uri -Method GET -Headers @{"ngrok-skip-browser-warning"="true"} | ConvertTo-Json -Depth 10
```

### Teste 3: Atualizar Status do Bling

```powershell
# Sincronizar status do Bling para local
$uri = "$ngrokUrl/api/bling/pedidos/status/123"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json" | ConvertTo-Json -Depth 10
```

## 🐛 Troubleshooting

### Erro: "Produto não está sincronizado com Bling"

**Solução:**
- Sincronize os produtos primeiro: `POST /api/bling/produtos/sync/<produto_id>`
- Ou importe produtos do Bling: `POST /api/bling/produtos/import`

### Erro: "CPF/CNPJ obrigatório"

**Solução:**
- Verifique se dados fiscais estão preenchidos na venda
- Campo `fiscal_cpf_cnpj` não pode estar vazio

### Pedido não criado automaticamente

**Possíveis causas:**
1. Pagamento não foi confirmado (verificar webhook)
2. Erro na sincronização (verificar logs)
3. Produtos não sincronizados

**Solução:**
- Verificar logs: `SELECT * FROM bling_sync_logs WHERE entity_type = 'pedido' ORDER BY created_at DESC`
- Sincronizar manualmente: `POST /api/bling/pedidos/sync/<venda_id>`

## 📝 Próximos Passos

1. ✅ Criação automática de pedidos
2. ✅ Sincronização de status
3. ⏳ Webhook do Bling para atualizações automáticas
4. ⏳ Emissão automática de NF-e
5. ⏳ Integração com logística (rastreamento)

## 🔗 Links Úteis

- [Documentação API Bling - Pedidos](https://developer.bling.com.br/referencia/pedidos)
- Teste da API: `GET /api/bling/test`
- Status: `GET /api/bling/status`

