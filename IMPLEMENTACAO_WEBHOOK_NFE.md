# 📄 Implementação: Webhook de Aprovação de NFC-e

## ✅ O que foi implementado

### 1. Função para Buscar Pedido por NFC-e ID

**Arquivo:** `blueprints/services/bling_order_service.py`

**Função:** `get_order_by_nfe_id(nfe_id: int) -> Optional[Dict]`

Busca o pedido local relacionado a uma NFC-e usando o ID da nota no Bling.

### 2. Função para Atualizar Situação para "Logística"

**Arquivo:** `blueprints/services/bling_order_service.py`

**Função:** `update_order_situacao_to_logistica(venda_id: int) -> Dict`

Atualiza a situação do pedido no Bling para "Logística", o que dispara automaticamente:
- ✅ Decremento de estoque
- ✅ Emissão de etiqueta
- ✅ Outros processos automáticos do Bling

### 3. Webhook de Nota Fiscal

**Arquivo:** `blueprints/api/webhook.py`

**Função:** `process_nfe_webhook(webhook_data, event, event_id, data)`

**Endpoint:** `/api/webhook/bling` (mesmo endpoint, detecta eventos de nota fiscal)

**Eventos suportados:**
- `consumer_invoice.created` - NFC-e criada
- `consumer_invoice.updated` - NFC-e atualizada (situação mudou)
- `consumer_invoice.deleted` - NFC-e deletada

## 🔄 Fluxo Completo Implementado

```
1. Pedido muda para "Em andamento" no Bling
   ↓
2. Webhook detecta mudança
   ↓
3. Backend emite NFC-e via API do Bling
   ↓
4. Status atualizado para 'nfe_aguardando_aprovacao'
   ↓
5. SEFAZ processa e autoriza NFC-e
   ↓
6. Bling envia webhook consumer_invoice.updated
   ↓
7. Backend detecta situação = 1 (Autorizada)
   ↓
8. Backend atualiza status para 'nfe_autorizada'
   ↓
9. Backend muda situação do pedido no Bling para "Logística"
   ↓
10. Bling automaticamente:
    - Decrementa estoque ✅
    - Emite etiqueta ✅
    - Atualiza status ✅
   ↓
11. Backend atualiza status local para 'pronto_envio'
   ✅ Fluxo completo!
```

## 📋 Status do Pedido

**Status utilizados:**
- `nfe_aguardando_aprovacao` - NFC-e emitida, aguardando SEFAZ
- `nfe_autorizada` - NFC-e autorizada pelo SEFAZ
- `pronto_envio` - Pedido pronto para envio (após Logística no Bling)

## 🔍 Detecção de Aprovação

O webhook detecta aprovação quando:
```python
nfe_situacao == 1  # 1 = Autorizada pelo SEFAZ
```

**Mapeamento de situações:**
- `0` = PENDENTE
- `1` = AUTORIZADA ✅ (dispara atualização)
- `2` = CANCELADA
- `3` = REJEITADA

## 🔧 Configuração Necessária no Bling

Para o webhook funcionar, é necessário:

1. **Adicionar escopo:** `consumer_invoice` na aplicação do Bling
2. **Configurar webhook:** URL do webhook deve ser configurada no Bling
3. **URL do webhook:** `https://seu-dominio.ngrok-free.dev/api/webhook/bling`

## 📝 Estrutura do Payload do Webhook

**Evento Updated (quando situação muda):**
```json
{
  "id": 12345678,
  "tipo": 1,
  "situacao": 1,  // 1 = Autorizada
  "numero": "1234",
  "dataEmissao": "2024-09-27 11:24:56",
  "dataOperacao": "2024-09-27 11:00:00",
  "contato": {
    "id": 12345678
  },
  "naturezaOperacao": {
    "id": 12345678
  },
  "loja": {
    "id": 12345678
  }
}
```

## ⚠️ Validações Implementadas

1. **Assinatura HMAC:** Valida assinatura do webhook
2. **ID da NFC-e:** Verifica se NFC-e existe
3. **Pedido relacionado:** Busca pedido local relacionado
4. **Situação autorizada:** Verifica se situação = 1 antes de processar
5. **Idempotência:** Sempre retorna 200 OK para evitar reenvios

## 🧪 Como Testar

1. Criar pedido no site
2. Sincronizar com Bling
3. Mudar situação para "Em andamento" no Bling
4. Aguardar emissão da NFC-e
5. Aguardar aprovação da SEFAZ
6. Verificar logs do backend para ver processamento do webhook
7. Verificar se pedido mudou para "Logística" no Bling
8. Verificar se estoque foi decrementado
9. Verificar se etiqueta foi emitida

## 📚 Referências

- API Bling Webhooks: https://developer.bling.com.br/referencia/webhooks
- Escopo necessário: `consumer_invoice`
- Situações de NFC-e: 0=PENDENTE, 1=AUTORIZADA, 2=CANCELADA, 3=REJEITADA
