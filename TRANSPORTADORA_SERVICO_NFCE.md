# 🚚 Transportadora e Serviço na NFC-e

## ✅ Implementação

### O que foi adicionado:

1. **Transportadora escolhida**
   - Nome da transportadora (ex: "Correios", "Jadlog", etc.)
   - Código da transportadora (se disponível)
   - Incluído no campo `transporte.transportador`

2. **Serviço de integração Melhor Envio**
   - ID do serviço no Bling (ex: 899551)
   - Código do serviço no Melhor Envio (ex: 1=PAC, 2=SEDEX)
   - Nome do serviço (ex: "PAC", "SEDEX")
   - Incluído no campo `transporte.volumes[0].servico`

3. **Código de rastreamento** (se disponível)
   - Incluído em `transporte.volumes[0].codigoRastreamento`

## 📋 Estrutura do Payload

```json
{
  "transporte": {
    "fretePorConta": 0,
    "frete": 20.00,
    "transportador": {
      "nome": "Correios",
      "numeroDocumento": "34028316000103"
    },
    "volumes": [
      {
        "servico": 899551,
        "codigoRastreamento": "BR123456789BR"
      }
    ]
  }
}
```

## 🔍 Como Funciona

### 1. Busca de Dados
- Sistema busca a etiqueta de frete do pedido na tabela `etiquetas_frete`
- Extrai:
  - `transportadora_nome`: Nome da transportadora
  - `transportadora_codigo`: Código da transportadora
  - `melhor_envio_service_id`: ID do serviço no Melhor Envio (1, 2, 3, etc.)
  - `melhor_envio_service_name`: Nome do serviço (PAC, SEDEX, etc.)
  - `codigo_rastreamento`: Código de rastreamento (se disponível)

### 2. Mapeamento do Serviço
- Sistema busca no Bling o serviço com `codigo` correspondente ao `melhor_envio_service_id`
- Prefere serviços específicos da loja ("LhamaBanana")
- Usa o `id` do serviço do Bling (ex: 899551) no campo `servico`

### 3. Inclusão no Payload
- **Transportadora**: Adicionada em `transporte.transportador`
- **Serviço**: Adicionado em `transporte.volumes[0].servico` (ID do Bling)
- **Rastreamento**: Adicionado em `transporte.volumes[0].codigoRastreamento` (se disponível)

## 📝 Logs Informativos

O sistema registra:
- `🚚 Transportadora adicionada ao transporte: {nome}`
- `📦 Serviço de postagem encontrado: {nome} (Melhor Envio ID: {id}, Bling ID: {id})`
- `✅ Serviço de logística Melhor Envio adicionado: ID Bling {id} (Melhor Envio: {id} - {nome})`

## 🔄 Fallback

Se o ID do serviço não for encontrado no Bling:
- Usa o nome do serviço como fallback
- Registra warning no log
- Pode não funcionar corretamente na API do Bling

## ✅ Benefícios

1. **Rastreabilidade completa**: Transportadora e serviço identificados na nota
2. **Integração correta**: Usa IDs do Bling para garantir compatibilidade
3. **Informações completas**: Inclui código de rastreamento quando disponível
4. **Logs detalhados**: Facilita depuração e auditoria

---

**Data:** 2026-01-21
**Status:** ✅ Implementado
