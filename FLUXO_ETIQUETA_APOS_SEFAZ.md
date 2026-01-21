# 📦 Fluxo de Emissão de Etiqueta - Após Aprovação do SEFAZ

## ✅ Alterações Implementadas

### O que foi removido:
1. ❌ **Criação automática de etiqueta no checkout**
   - Removida do webhook do PagBank quando status muda para `processando_envio`
   - Removida do painel admin quando status muda para `processando_envio`

2. ❌ **Criação de etiqueta antes da aprovação do SEFAZ**
   - Etiqueta não é mais criada automaticamente após pagamento

### O que foi mantido:
1. ✅ **Cálculo de frete no checkout**
   - Continua funcionando normalmente
   - Cliente escolhe transportadora e serviço
   - Dados são salvos na tabela `vendas`

2. ✅ **Criação de etiqueta após aprovação do SEFAZ**
   - Etiqueta é criada automaticamente quando NFC-e é autorizada
   - Usa o serviço escolhido no checkout
   - Acontece no webhook de NFC-e quando `situacao = 1` (Autorizada)

## 🔄 Novo Fluxo Completo

```
1. Cliente faz checkout
   ↓
2. Sistema calcula frete (Melhor Envio)
   ↓
3. Cliente escolhe transportadora e serviço
   ↓
4. Dados da transportadora e serviço são salvos na tabela vendas
   ↓
5. Pedido criado com status: pendente_pagamento
   ↓
6. Pagamento aprovado (PagBank webhook)
   ↓
7. Status muda para: processando_envio
   ↓
8. Pedido sincronizado com Bling → Situação: "Em aberto"
   ↓
9. Admin aprova manualmente no Bling → Situação: "Em andamento"
   ↓
10. Webhook detecta "Em andamento" → Sistema emite NFC-e
    Status local: nfe_aguardando_aprovacao
    ↓
11. SEFAZ autoriza NFC-e → Webhook detecta aprovação (situação = 1)
    Status local: nfe_autorizada
    ↓
12. Sistema cria etiqueta de frete automaticamente
    Usa serviço escolhido no checkout
    ↓
13. Sistema muda pedido no Bling para "Logística"
    Status local: pronto_envio
    ↓
14. Bling gerencia automaticamente: decremento de estoque, etc.
```

## 📋 Mudanças no Código

### 1. `blueprints/api/webhook.py`
- **Removido**: Criação de etiqueta quando status muda para `processando_envio`
- **Adicionado**: Criação de etiqueta quando NFC-e é autorizada pelo SEFAZ

### 2. `blueprints/admin/api/routes.py`
- **Removido**: Criação automática de etiqueta quando status muda para `processando_envio`

### 3. `blueprints/api/labels.py`
- **Atualizado**: `create_label_automatically()` agora usa o serviço escolhido no checkout
- **Documentação**: Atualizada para refletir que é chamada após aprovação do SEFAZ

## ✅ Benefícios

1. **Conformidade fiscal**: Etiqueta só é criada após aprovação do SEFAZ
2. **Evita desperdício**: Não cria etiqueta se NFC-e for rejeitada
3. **Fluxo correto**: Segue a ordem: NFC-e → Aprovação → Etiqueta
4. **Serviço correto**: Usa o serviço escolhido pelo cliente no checkout

## 📝 Logs Informativos

O sistema registra:
- `📦 Criando etiqueta de frete para venda {id} após aprovação do SEFAZ`
- `✅ Etiqueta {id} criada automaticamente para venda {id} após aprovação do SEFAZ`
- `📦 Usando serviço escolhido no checkout: {nome} (ID: {id})`

---

**Data:** 2026-01-21
**Status:** ✅ Implementado
