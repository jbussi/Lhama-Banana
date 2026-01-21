# 🚚 Integração: Transportadora do Bling na NFC-e

## ✅ Implementação

### O que foi implementado:

1. **Busca automática do contato da transportadora no Bling**
   - Quando a NFC-e é emitida, o sistema busca o contato completo da transportadora no Bling usando o CNPJ
   - Se encontrado, usa os dados completos do contato do Bling (nome, CNPJ, IE, endereço completo)
   - Se não encontrado, usa os dados salvos na tabela `vendas` como fallback

2. **Dados completos da transportadora na NFC-e**
   - Nome da transportadora
   - CNPJ (limpo, sem formatação)
   - Inscrição Estadual (IE)
   - Endereço completo (rua, número, complemento, bairro, município, UF, CEP)

## 🔄 Fluxo de Busca

```
1. Cliente escolhe transportadora no checkout
   ↓
2. Dados da transportadora são salvos na tabela vendas
   ↓
3. Pedido é aprovado e NFC-e é emitida
   ↓
4. Sistema busca contato da transportadora no Bling (por CNPJ)
   ↓
5a. Se encontrado no Bling:
    → Usa dados completos do contato do Bling
    → Garante dados atualizados e corretos
   ↓
5b. Se não encontrado:
    → Usa dados da tabela vendas (fallback)
   ↓
6. Dados da transportadora são incluídos na NFC-e
```

## 📋 Campos Preenchidos na NFC-e

### Seção `transporte.transportador`:

```json
{
  "transporte": {
    "transportador": {
      "nome": "Nome da Transportadora",
      "numeroDocumento": "CNPJ sem formatação",
      "ie": "Inscrição Estadual",
      "endereco": {
        "endereco": "Rua/Logradouro",
        "numero": "Número",
        "complemento": "Complemento (opcional)",
        "bairro": "Bairro",
        "municipio": "Município",
        "uf": "UF",
        "cep": "CEP sem formatação"
      }
    },
    "frete": 14.89,
    "fretePorConta": 0
  }
}
```

## 🔍 Como Funciona a Busca

### 1. Busca no Bling
- Usa a função `find_contact_in_bling(cnpj)` do serviço `bling_contact_service`
- Busca por CNPJ (sem formatação)
- Retorna contato completo com todos os dados cadastrados

### 2. Fallback para Tabela Vendas
- Se não encontrar no Bling, usa dados salvos na tabela `vendas`
- Garante que a NFC-e sempre terá dados da transportadora, mesmo se não estiver cadastrada no Bling

## 📝 Logs Informativos

O sistema registra:
- `✅ Contato da transportadora encontrado no Bling: {nome} (ID: {id})`
- `⚠️ Transportadora não encontrada no Bling (CNPJ: {cnpj}). Usando dados da tabela vendas.`
- `⚠️ Erro ao buscar transportadora no Bling: {erro}. Usando dados da tabela vendas.`
- `🚚 Transportadora adicionada ao transporte: {nome} (CNPJ: {cnpj}, IE: {ie}, UF: {uf})`

## ✅ Benefícios

1. **Dados sempre atualizados**: Usa dados do Bling que podem ser atualizados a qualquer momento
2. **Dados completos**: Garante que todos os campos necessários estão preenchidos
3. **Conformidade fiscal**: Dados corretos da transportadora na NFC-e
4. **Fallback seguro**: Se não encontrar no Bling, ainda usa dados salvos no pedido

## 🔧 Manutenção

- **Atualizar transportadoras no Bling**: Basta atualizar o contato no Bling, e os dados serão usados automaticamente nas próximas NFC-e
- **Adicionar novas transportadoras**: Crie o contato no Bling com todos os dados, e o sistema encontrará automaticamente pelo CNPJ

---

**Data:** 2026-01-21
**Status:** ✅ Implementado
