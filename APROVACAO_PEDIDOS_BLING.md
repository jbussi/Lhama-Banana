# Aprovação de Pedidos e Notificações no Bling

## 📋 Aprovação de Pedidos

### Situações de Pedidos no Bling

O Bling utiliza **situações** para controlar o estado dos pedidos:

| Situação | Código | Descrição |
|----------|--------|-----------|
| **Pendente** | `P` | Aguardando aprovação/pagamento |
| **Em Aberto** | `E` | Aprovado, pronto para processamento/envio |
| **Baixado** | `B` | Entregue/finalizado |
| **Faturado** | `F` | Nota fiscal emitida |
| **Cancelado** | `C` | Pedido cancelado |

### Fluxo de Aprovação

```
1. Pedido criado no Bling
   ↓ Situação: 'P' (Pendente)
   
2. Pagamento confirmado (webhook PagBank)
   ↓ Status local: 'pendente_pagamento' → 'processando_envio'
   
3. Admin aprova pedido no Bling
   ↓ POST /api/bling/pedidos/approve/{venda_id}
   ↓ Situação: 'P' → 'E' (Em Aberto)
   ↓ Status local: 'processando_envio'
   
4. Processamento/envio
   ↓ Situação mantém 'E'
   
5. Entrega finalizada
   ↓ Situação: 'E' → 'B' (Baixado)
   ↓ Status local: 'entregue'
```

### Endpoint de Aprovação

**POST** `/api/bling/pedidos/approve/{venda_id}`

Este endpoint:
- Busca o pedido no Bling
- Verifica se está na situação 'P' (Pendente)
- Atualiza para situação 'E' (Em aberto)
- Atualiza status local para `processando_envio`
- Retorna confirmação da aprovação

**Exemplo de resposta:**
```json
{
  "success": true,
  "message": "Pedido aprovado com sucesso no Bling",
  "bling_pedido_id": 12345,
  "situacao_anterior": "P",
  "situacao_nova": "E",
  "status_local_atualizado": "processando_envio"
}
```

### Quando Aprovar um Pedido

**Aprovar quando:**
- ✅ Pagamento foi confirmado (webhook PagBank)
- ✅ Dados do pedido estão corretos
- ✅ Produtos estão disponíveis em estoque
- ✅ Cliente e endereço validados

**Não aprovar quando:**
- ❌ Pagamento ainda não confirmado
- ❌ Dados fiscais incompletos
- ❌ Produtos sem estoque
- ❌ Endereço inválido

## 🔔 Notificações do Bling

### Configuração de Webhooks no Bling

O Bling oferece **webhooks** para notificar sobre eventos importantes. Para configurar notificações quando um pedido é pago e precisa ser aprovado:

### Opção 1: Webhooks da API Bling

**Configuração via API (se disponível):**

1. Acesse a **Central de Extensões** no Bling
2. Vá para **"Minhas Instalações"**
3. Selecione sua integração
4. Configure **"Integração Automática"**
5. Ative **"Situação da importação automática de pedidos"**

### Opção 2: Notificações por Email

O Bling pode enviar emails quando:
- Novo pedido é criado
- Pedido muda de situação
- Pagamento é confirmado

**Configurar:**
1. Acesse **Configurações** → **Notificações**
2. Ative notificações por email para:
   - "Novo pedido de venda"
   - "Pagamento recebido"
   - "Pedido aguardando aprovação"

### Opção 3: Polling (Verificação Periódica)

Nossa implementação atual usa **polling** para verificar mudanças:

**Endpoint:** `POST /api/bling/pedidos/status/sync-all`

Este endpoint:
- Busca todos os pedidos sincronizados
- Verifica situação atual no Bling
- Atualiza status local se houver mudanças

**Recomendação:** Executar periodicamente (a cada 5-15 minutos) via cron job ou task scheduler.

### Opção 4: Webhooks Customizados (Futuro)

Para implementar webhooks do Bling:

1. **Criar endpoint para receber webhooks:**
   ```python
   @bling_bp.route('/webhooks/bling', methods=['POST'])
   def bling_webhook():
       # Validar assinatura do webhook
       # Processar evento
       # Atualizar pedido local
   ```

2. **Configurar URL no Bling:**
   - URL: `https://seu-dominio.com/api/bling/webhooks/bling`
   - Eventos: `pedido.pago`, `pedido.aprovado`, etc.

3. **Validar segurança:**
   - Verificar assinatura HMAC
   - Validar origem do request
   - Implementar idempotência

## 🔄 Fluxo Recomendado

### Fluxo Automático (Atual)

```
1. Cliente faz pedido no site
   ↓
2. Webhook PagBank confirma pagamento
   ↓ Status local: 'processando_envio'
   ↓
3. Sistema sincroniza pedido com Bling
   ↓ Situação Bling: 'P' (Pendente)
   ↓
4. Admin verifica pedidos pendentes no painel
   ↓
5. Admin aprova: POST /api/bling/pedidos/approve/{venda_id}
   ↓ Situação Bling: 'E' (Em aberto)
   ↓
6. Processamento/envio do pedido
```

### Fluxo com Notificações (Recomendado)

```
1. Cliente faz pedido no site
   ↓
2. Webhook PagBank confirma pagamento
   ↓ Status local: 'processando_envio'
   ↓
3. Sistema sincroniza pedido com Bling
   ↓ Situação Bling: 'P' (Pendente)
   ↓
4. Sistema envia notificação ao admin:
   - Email: "Novo pedido aguardando aprovação"
   - Dashboard: Badge de notificação
   ↓
5. Admin recebe notificação e aprova
   ↓ POST /api/bling/pedidos/approve/{venda_id}
   ↓
6. Processamento/envio do pedido
```

## 📝 Implementação de Notificações (Próximos Passos)

Para implementar notificações quando pedido é pago e precisa aprovação:

### 1. Email de Notificação

```python
def send_order_approval_notification(venda_id: int):
    """Envia email ao admin quando pedido precisa aprovação"""
    # Buscar dados do pedido
    # Enviar email com link para aprovar
    # Incluir resumo do pedido
```

### 2. Dashboard de Notificações

```python
@bling_bp.route('/pedidos/pending-approval', methods=['GET'])
def get_pending_approval_orders():
    """Lista pedidos aguardando aprovação"""
    # Buscar pedidos com situação 'P' no Bling
    # Retornar lista para dashboard
```

### 3. Webhook Handler (Futuro)

```python
@bling_bp.route('/webhooks/bling', methods=['POST'])
def handle_bling_webhook():
    """Processa webhooks do Bling"""
    # Validar assinatura
    # Processar evento: pedido.pago, pedido.aprovado, etc.
    # Atualizar sistema local
```

## 🛠️ Configuração Manual no Bling

### Situações Customizadas

O Bling permite criar situações customizadas:

1. Acesse **Configurações** → **Gerenciador de Transições**
2. Crie situação: **"Aguardando Aprovação"**
3. Configure transições:
   - De: "Pendente" → Para: "Aguardando Aprovação"
   - De: "Aguardando Aprovação" → Para: "Em Aberto" (aprovado)
   - De: "Aguardando Aprovação" → Para: "Cancelado" (rejeitado)

### Notificações no Bling

1. Acesse **Configurações** → **Notificações**
2. Configure alertas para:
   - **Novo pedido criado**
   - **Pagamento confirmado**
   - **Pedido mudou de situação**

## ✅ Checklist de Implementação

- [x] Endpoint para aprovar pedidos (`/pedidos/approve/{venda_id}`)
- [x] Sincronização de status bidirecional
- [x] Mapeamento de situações Bling ↔ Status local
- [ ] Email de notificação quando pedido precisa aprovação
- [ ] Dashboard com lista de pedidos pendentes
- [ ] Webhook handler para receber eventos do Bling (futuro)
- [ ] Sistema de notificações em tempo real (futuro)

## 🔗 Referências

- [Bling API - Pedidos](https://developer.bling.com.br/api/v3/documentacao/pedidos)
- [Bling - Gerenciador de Transições](https://ajuda.bling.com.br/hc/pt-br/articles/360039070654)
- [Bling - Importação Automática](https://ajuda.bling.com.br/hc/pt-br/articles/360036883394)
