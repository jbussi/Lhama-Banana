# ETAPA 4 - Sincronização de Estoque

## ✅ O Que Foi Implementado

### 1. **Sincronização Bidirecional**

#### Bling → LhamaBanana (`sync_stock_from_bling`)
- Atualiza estoque local com valores do Bling
- Bling é considerado fonte de verdade para estoque
- Suporta produto específico ou todos os produtos sincronizados

#### LhamaBanana → Bling (`sync_stock_to_bling`)
- Envia estoque local para o Bling
- Mantém outros campos do produto no Bling
- Atualiza apenas campo `estoque.atual`

### 2. **Gerenciamento Automático de Estoque**

#### Após Venda Confirmada (`update_stock_after_sale`)
- Quando pagamento é confirmado (webhook PagBank)
- Estoque já foi decrementado localmente na criação do pedido
- Função sincroniza estoque atualizado com Bling
- Executado automaticamente quando status muda para `processando_envio`

#### Cancelamento/Devolução (`revert_stock_on_cancellation`)
- Quando pedido é cancelado/devolvido/reembolsado
- Reverte estoque (incrementa) tanto local quanto no Bling
- Tratamento automático baseado em mudança de status

#### Gerenciamento Inteligente (`handle_order_status_change`)
- Detecta mudança de status do pedido
- Aplica regras automaticamente:
  - `processando_envio`, `enviado`, `entregue`: Sincroniza estoque (já decrementado)
  - `cancelado_*`, `devolvido`, `reembolsado`: Reverte estoque
  - Outros status: Não afeta estoque

### 3. **Consistência de Estoque (`ensure_stock_consistency`)**
- Compara estoque local com Bling
- Sincroniza do Bling para local (Bling = fonte de verdade)
- Útil para corrigir divergências

### 4. **Integração Automática**

#### Webhook PagBank
- Quando pagamento confirmado → sincroniza estoque com Bling
- Executado automaticamente após mudança de status

#### Admin (Atualização Manual)
- Quando admin atualiza status → gerencia estoque automaticamente
- Cancelamentos revertem estoque automaticamente

## 🔄 Fluxos de Estoque

### Fluxo 1: Venda Normal (Pagamento Confirmado)

```
1. Cliente cria pedido
   ↓
2. Estoque decrementado localmente (checkout_service)
   ↓
3. Pagamento confirmado (webhook PagBank)
   ↓
4. Status muda para 'processando_envio'
   ↓
5. update_stock_after_sale() → Sincroniza estoque com Bling
   ✅ Estoque consistente entre sistemas
```

### Fluxo 2: Cancelamento de Pedido

```
1. Admin cancela pedido (status → 'cancelado_pelo_vendedor')
   ↓
2. handle_order_status_change() detecta mudança
   ↓
3. revert_stock_on_cancellation() é chamado
   ↓
4. Estoque incrementado localmente
   ↓
5. Estoque sincronizado com Bling
   ✅ Estoque revertido e consistente
```

### Fluxo 3: Sincronização Periódica (Worker)

```
1. Worker executa periodicamente (configurável)
   ↓
2. sync_stock_from_bling() para todos os produtos
   ↓
3. Estoque local atualizado com valores do Bling
   ✅ Consistência garantida periodicamente
```

## 📋 Regras de Negócio

### Quando Estoque é Atualizado:

1. **Venda Confirmada** (pagamento aprovado)
   - Estoque já foi decrementado na criação
   - Apenas sincroniza com Bling

2. **Cancelamento**
   - Incrementa estoque local
   - Sincroniza com Bling

3. **Devolução**
   - Incrementa estoque local
   - Sincroniza com Bling

4. **Reembolso**
   - Incrementa estoque local
   - Sincroniza com Bling

### Quando Estoque NÃO é Alterado:

- Pedido pendente
- Mudança de status entre `enviado` → `entregue`
- Outras mudanças de status que não afetam estoque

## 🔧 Endpoints Disponíveis

### Sincronizar Estoque do Bling → Local
```http
POST /api/bling/estoque/sync-from-bling
Content-Type: application/json

{
  "produto_id": 123  // opcional, se omitido sincroniza todos
}
```

### Sincronizar Estoque Local → Bling
```http
POST /api/bling/estoque/sync-to-bling
Content-Type: application/json

{
  "produto_id": 123  // opcional, se omitido sincroniza todos
}
```

### Sincronizar Produto Específico (Bidirecional)
```http
POST /api/bling/estoque/sync/{produto_id}
```

### Verificar Consistência
```http
POST /api/bling/estoque/consistency
Content-Type: application/json

{
  "produto_id": 123  // opcional
}
```

## 📊 Estrutura de Resposta

### Sucesso:
```json
{
  "success": true,
  "total": 5,
  "success": 5,
  "errors": 0,
  "results": [
    {
      "produto_id": 123,
      "success": true,
      "estoque_novo": 45
    }
  ]
}
```

### Erro:
```json
{
  "success": false,
  "error": "Produto não encontrado",
  "total": 0,
  "results": []
}
```

## 🎯 Como Testar

### Teste 1: Sincronizar Estoque do Bling

```powershell
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

# Sincronizar todos os produtos
Invoke-RestMethod -Uri "$ngrokUrl/api/bling/estoque/sync-from-bling" `
    -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} `
    -ContentType "application/json" -Body '{}'
```

### Teste 2: Sincronizar Estoque para Bling

```powershell
# Sincronizar produto específico
Invoke-RestMethod -Uri "$ngrokUrl/api/bling/estoque/sync-to-bling" `
    -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} `
    -ContentType "application/json" -Body '{"produto_id": 1}'
```

### Teste 3: Verificar Fluxo de Venda

1. Criar pedido no site (estoque decrementa localmente)
2. Simular pagamento confirmado (webhook PagBank)
3. Verificar logs: estoque sincronizado com Bling
4. Verificar no Bling: estoque atualizado

### Teste 4: Verificar Cancelamento

1. Cancelar pedido (via admin)
2. Verificar logs: estoque revertido
3. Verificar no banco: estoque incrementado
4. Verificar no Bling: estoque sincronizado

## ⚠️ Armadilhas Evitadas

1. **Duplicação de Decremento**
   - ✅ Estoque só é decrementado uma vez (na criação do pedido)
   - ✅ Após confirmação, apenas sincroniza (não decrementa novamente)

2. **Falta de Reversão em Cancelamento**
   - ✅ Cancelamento reverte estoque automaticamente
   - ✅ Aplica para todos os status de cancelamento

3. **Divergência entre Sistemas**
   - ✅ Worker periódico mantém consistência
   - ✅ Bling é fonte de verdade

4. **Produtos Não Sincronizados**
   - ✅ Verifica se produto está sincronizado antes de atualizar Bling
   - ✅ Logs indicam produtos não sincronizados

5. **Rate Limiting**
   - ✅ Delay entre requisições (0.5s)
   - ✅ Tratamento de erros 429

## 📝 Próximos Passos

Após validar sincronização de estoque:
- **ETAPA 5**: Clientes (criação automática)
- **ETAPA 6**: Pedidos (criação no Bling com CFOP)
- **ETAPA 7**: NF-e (emissão automática)


