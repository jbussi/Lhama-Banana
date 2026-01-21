# 🔍 Debug: Transição para "Verificado"

## ✅ O que foi feito:

1. **Adicionado mapeamento explícito** no banco de dados:
   - Situação "Verificado" (ID 24) agora tem `status_site = 'em_processamento'`

2. **Adicionados logs detalhados** em:
   - `map_bling_situacao_id_to_status()`: Loga cada etapa do mapeamento
   - `update_pedido_situacao()`: Loga todo o processo de atualização
   - `process_order_webhook()`: Loga quando o nome da situação não vem no webhook

## 📋 Como verificar os logs:

Quando um pedido mudar para "Verificado" no Bling, você verá logs como:

```
================================================================================
🔄 [UPDATE_PEDIDO_SITUACAO] Iniciando atualização de situação
   Venda ID: <venda_id>
   Situação Bling ID: 24
   Situação Bling Nome: Verificado
================================================================================
🔍 [MAP_BLING_SITUACAO] Mapeando situação ID 24 para status do site
📋 [MAP_BLING_SITUACAO] Mapeamento encontrado: {...}
✅ [MAP_BLING_SITUACAO] Status encontrado via mapeamento explícito: em_processamento
✅ [UPDATE_PEDIDO_SITUACAO] Pedido <venda_id> atualizado com sucesso!
   Status Site: <status_anterior> → em_processamento
================================================================================
```

## 🔍 Verificar logs em tempo real:

```bash
# Ver logs do Flask
docker-compose logs -f flask | grep -E "UPDATE_PEDIDO_SITUACAO|MAP_BLING_SITUACAO|WEBHOOK"

# Ou ver todos os logs
docker-compose logs -f flask
```

## ⚠️ Possíveis problemas:

1. **Nome não vem no webhook**: Se o webhook não enviar o nome da situação, o sistema busca no banco
2. **ID não encontrado**: Se o ID 24 não estiver no banco `bling_situacoes`, o mapeamento falha
3. **Status não atualizado**: Verifique se o pedido existe na tabela `vendas`

## 🧪 Testar manualmente:

Para testar se o mapeamento está funcionando:

```python
from blueprints.services.bling_situacao_service import map_bling_situacao_id_to_status

# Deve retornar 'em_processamento'
status = map_bling_situacao_id_to_status(24)
print(f"Status mapeado: {status}")
```

## 📊 Status atual das situações:

- ✅ Em aberto: ID 6 → `sincronizado_bling`
- ✅ Em andamento: ID 15 → `em_processamento`
- ✅ Atendido: ID 9 → `entregue`
- ✅ Cancelado: ID 12 → `cancelado_pelo_vendedor`
- ✅ Em digitação: ID 21 → `pendente_pagamento`
- ✅ Venda Agenciada: ID 18 → `em_processamento`
- ✅ **Verificado: ID 24 → `em_processamento`** (MAPEADO)
- ✅ Logística: ID 716906 → `pronto_envio`
- ✅ Venda Atendimento Humano: ID 716890 → `em_processamento`
