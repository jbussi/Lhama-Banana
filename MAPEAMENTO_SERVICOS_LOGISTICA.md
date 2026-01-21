# 📦 Mapeamento de Serviços de Logística - Bling

## ✅ Serviços Encontrados no Bling

### Melhor Envio - LhamaBanana (ID: 899551)

| Código | Nome | Alias | ID Bling |
|--------|------|-------|----------|
| 1 | PAC | ME_PAC_1 | 899551 |
| 2 | SEDEX | ME_SEDEX_2 | 899551 |
| 3 | Package | - | 899551 |
| 4 | Com | - | 899551 |
| 12 | éFácil | ME_éFácil_12 | 899551 |
| 15 | Expresso | ME_Expresso_15 | 899551 |
| 16 | e-commerce | ME_e-commerce_16 | 899551 |
| 17 | Mini Envios | ME_Mini Envios_17 | 899551 |
| 22 | Rodoviário | ME_Rodoviário_22 | 899551 |
| 27 | Package Centralizado | ME_.Package Centralizado_27 | 899551 |
| 31 | Express | ME_Express_31 | 899551 |
| 32 | Coleta | ME_Coleta_32 | 899551 |
| 33 | Standard | ME_Standard_33 | 899551 |
| 34 | Loggi Ponto | ME_Loggi Ponto_34 | 899551 |

### Melhor Envio - Genérico (ID: 899546)

| Código | Nome | Alias | ID Bling |
|--------|------|-------|----------|
| 3 | Package | ME_.Package_3 | 899546 |
| 4 | Com | ME_.Com_4 | 899546 |

## 🔄 Como Funciona o Mapeamento

### 1. Na Tabela `etiquetas_frete`
- `melhor_envio_service_id`: ID do serviço no Melhor Envio (1, 2, 3, etc.)
- `melhor_envio_service_name`: Nome do serviço (PAC, SEDEX, etc.)

### 2. Na Emissão da NFC-e
1. Sistema busca a etiqueta de frete do pedido
2. Extrai o `melhor_envio_service_id` (ex: 1 para PAC)
3. Busca no Bling o serviço com `codigo` correspondente e `tipoIntegracao = 'MelhorEnvio'`
4. Prefere serviços específicos da loja (que contêm "LhamaBanana" na descrição)
5. Usa o `id` do serviço do Bling (ex: 899551) no campo `transporte.volumes[0].servico`

### 3. Estrutura no Payload da NFC-e

```json
{
  "transporte": {
    "fretePorConta": 0,
    "frete": 20.00,
    "volumes": [
      {
        "servico": 899551  // ID do serviço no Bling (não o código do Melhor Envio)
      }
    ]
  }
}
```

## 📝 Observações Importantes

1. **ID vs Código**: 
   - O Bling usa `id` (ex: 899551) para identificar o serviço
   - O Melhor Envio usa `codigo` (ex: 1, 2, 3) para identificar o serviço
   - O mapeamento é feito buscando o serviço do Bling com `codigo` igual ao `melhor_envio_service_id`

2. **Preferência por Serviços Específicos**:
   - O sistema prefere serviços específicos da loja ("LhamaBanana")
   - Se não encontrar, usa qualquer serviço com o código correspondente

3. **Fallback**:
   - Se não encontrar o ID do serviço no Bling, usa o nome como fallback
   - Isso pode não funcionar, mas é melhor que não incluir nada

## 🔍 Script de Busca

Use o script `buscar_servicos_logistica_bling.py` para:
- Listar todos os serviços disponíveis
- Verificar IDs e códigos
- Testar mapeamentos

```bash
# Buscar todos os serviços do Melhor Envio
docker exec lhama_banana_flask python buscar_servicos_logistica_bling.py --melhor-envio

# Buscar outros tipos de logística
docker exec lhama_banana_flask python buscar_servicos_logistica_bling.py --tipo Correios
```

---

**Data:** 2026-01-21
**Status:** ✅ Implementado e mapeado
