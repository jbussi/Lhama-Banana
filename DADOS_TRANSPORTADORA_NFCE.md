# 🚚 Dados Completos da Transportadora na NFC-e

## ✅ Implementação

### O que foi implementado:

1. **Armazenamento dos dados da transportadora no checkout**
   - Quando o cliente escolhe uma transportadora, os dados completos são salvos na tabela `vendas`
   - Dados armazenados: nome, CNPJ, IE, UF, município, endereço completo
   - ID e nome do serviço do Melhor Envio também são salvos

2. **Uso na emissão da NFC-e**
   - Dados da transportadora são obtidos diretamente da tabela `vendas`
   - Não depende da criação da etiqueta (que acontece depois)
   - Todos os dados completos são incluídos no campo `transporte.transportador`

## 📋 Campos Adicionados na Tabela `vendas`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `transportadora_nome` | VARCHAR(255) | Nome da transportadora |
| `transportadora_cnpj` | VARCHAR(18) | CNPJ da transportadora |
| `transportadora_ie` | VARCHAR(20) | Inscrição Estadual |
| `transportadora_uf` | CHAR(2) | UF da transportadora |
| `transportadora_municipio` | VARCHAR(255) | Município |
| `transportadora_endereco` | VARCHAR(255) | Endereço (rua) |
| `transportadora_numero` | VARCHAR(50) | Número |
| `transportadora_complemento` | VARCHAR(255) | Complemento |
| `transportadora_bairro` | VARCHAR(255) | Bairro |
| `transportadora_cep` | VARCHAR(10) | CEP |
| `melhor_envio_service_id` | INTEGER | ID do serviço (1=PAC, 2=SEDEX, etc) |
| `melhor_envio_service_name` | VARCHAR(100) | Nome do serviço |

## 🔄 Fluxo Completo

### 1. No Checkout
- Cliente escolhe opção de frete
- Sistema busca opções do Melhor Envio via `shipping_service.py`
- Melhor Envio retorna dados completos da transportadora em `company`
- Dados são incluídos no `shipping_option` enviado ao backend

### 2. Na Criação do Pedido
- `checkout_service.py` recebe `shipping_option` com dados da transportadora
- `create_order_and_items()` salva todos os dados na tabela `vendas`
- Dados ficam disponíveis para uso posterior

### 3. Na Emissão da NFC-e
- `emit_nfce_consumidor()` busca dados da transportadora da tabela `vendas`
- Monta objeto `transportador` completo com todos os dados
- Busca ID do serviço no Bling baseado no `melhor_envio_service_id`
- Inclui tudo no payload da NFC-e

## 📋 Estrutura do Payload da NFC-e

```json
{
  "transporte": {
    "fretePorConta": 0,
    "frete": 20.00,
    "transportador": {
      "nome": "Correios",
      "numeroDocumento": "34028316000103",
      "ie": "123456789012",
      "endereco": {
        "endereco": "Rua da Transportadora",
        "numero": "123",
        "complemento": "Sala 101",
        "bairro": "Centro",
        "municipio": "São Paulo",
        "uf": "SP",
        "cep": "01000000"
      }
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

## 📝 Logs Informativos

O sistema registra:
- `🚚 Transportadora adicionada ao transporte: {nome} (CNPJ: {cnpj}, IE: {ie}, UF: {uf})`
- `📦 Serviço de postagem encontrado: {nome} (Melhor Envio ID: {id}, Bling ID: {id})`

## ✅ Benefícios

1. **Dados completos**: CNPJ, IE, endereço completo da transportadora
2. **Disponibilidade imediata**: Dados salvos no checkout, antes da criação da etiqueta
3. **Conformidade fiscal**: Todos os dados necessários para a NFC-e
4. **Rastreabilidade**: Vinculação clara entre pedido, transportadora e serviço

---

**Data:** 2026-01-21
**Status:** ✅ Implementado
