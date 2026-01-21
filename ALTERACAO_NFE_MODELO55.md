# 📄 Alteração: NFC-e → NF-e (Modelo 55)

## ✅ Mudanças Implementadas

### Tipo de Nota Fiscal
- **Antes:** NFC-e (Nota Fiscal de Consumidor Eletrônica) - `tipo: 1`
- **Agora:** NF-e (Nota Fiscal Eletrônica - Modelo 55) - `tipo: 0`

### Arquivos Modificados:

#### 1. `blueprints/services/bling_nfe_service.py`
- ✅ Função renomeada: `emit_nfce_consumidor()` → `emit_nfe()`
- ✅ Tipo alterado: `"tipo": 1` → `"tipo": 0`
- ✅ Comentários atualizados para NF-e (Modelo 55)
- ✅ Logs atualizados para NF-e

#### 2. `blueprints/api/webhook.py`
- ✅ Chamada atualizada: `emit_nfce_consumidor()` → `emit_nfe()`
- ✅ Logs atualizados: "NFC-e" → "NF-e"
- ✅ Comentários atualizados

#### 3. `blueprints/api/bling.py`
- ✅ Endpoint `emit_nfe()` renomeado para `emit_nfe_endpoint()` (evitar conflito)

## 📋 Diferenças entre NFC-e e NF-e

### NFC-e (Modelo 65)
- Tipo na API: `tipo: 1`
- Uso: Vendas para consumidor final (pessoa física)
- Regime simplificado

### NF-e (Modelo 55)
- Tipo na API: `tipo: 0`
- Uso: Vendas para pessoa jurídica ou quando requer NF-e completa
- Regime completo
- **SEMPRE SERÁ EMITIDA AGORA**

## 🔄 Fluxo Atualizado

```
1. Pedido muda para "Em andamento" no Bling
   ↓
2. Webhook detecta mudança
   ↓
3. Sistema emite NF-e (Modelo 55) - tipo 0
   ↓
4. Status: nfe_aguardando_aprovacao
   ↓
5. SEFAZ autoriza NF-e
   ↓
6. Webhook detecta aprovação
   ↓
7. Sistema cria etiqueta de frete
   ↓
8. Sistema muda para "Logística" no Bling
   ↓
9. Status: pronto_envio
```

## ✅ Payload da NF-e

```json
{
  "tipo": 0,  // NF-e (Modelo 55)
  "dataOperacao": "2026-01-21 22:00:00",
  "contato": {...},
  "finalidade": 1,
  "itens": [...],
  "parcelas": [...],
  "desconto": 0,
  "transporte": {
    "fretePorConta": 0,
    "frete": 14.89,
    "transportador": {
      "nome": "...",
      "numeroDocumento": "...",
      "ie": "...",
      "endereco": {...}
    },
    "volumes": [...]
  },
  "observacoes": "..."
}
```

## 📝 Notas Importantes

1. **Sempre NF-e**: Sistema sempre emitirá NF-e (Modelo 55), nunca NFC-e
2. **Compatibilidade**: NF-e funciona tanto para pessoa física quanto jurídica
3. **Dados da transportadora**: Continuam sendo buscados no Bling automaticamente
4. **Webhook**: Continua funcionando da mesma forma (apenas tipo mudou)

---

**Data:** 2026-01-21
**Status:** ✅ Implementado
