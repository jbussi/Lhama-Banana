# ETAPA 6 - Pedidos de Venda com CFOP

## ✅ O Que Foi Implementado

### 1. **Criação de Pedidos no Bling**

#### Mapeamento Completo
- Dados do cliente (nome, CPF/CNPJ, endereço)
- Itens do pedido (produtos, quantidades, preços)
- Parcelas (pagamento)
- Descontos e frete
- Observações

#### Idempotência
- Verifica se pedido já existe no Bling antes de criar
- Atualiza pedido existente se necessário
- Evita duplicação usando `bling_pedidos` (tabela de referência)

### 2. **CFOP - Código Fiscal de Operações e Prestações**

#### ⚠️ IMPORTANTE: CFOP é do Pedido, não do Produto

CFOP depende da **natureza da transação**:
- **Estado de origem** (loja/emitente)
- **Estado de destino** (cliente/destinatário)
- **Tipo de operação** (venda, compra, etc.)

#### Cálculo Automático de CFOP

```python
# Mesmo estado (loja e cliente no mesmo estado)
CFOP 5102 - Venda dentro do estado

# Interestadual (loja e cliente em estados diferentes)
CFOP 6108 - Venda interestadual
```

#### Configuração
- Estado da loja configurável via `BLING_EMITENTE_ESTADO` (default: 'SP')
- Estado do cliente obtido do endereço de entrega
- CFOP calculado automaticamente para cada item

### 3. **Integração com Clientes**

#### Sincronização Automática
- Cliente sincronizado antes de criar pedido
- Garante que cliente existe no Bling
- Não bloqueia criação se cliente falhar (mas loga aviso)

### 4. **Produtos no Pedido**

#### Mapeamento de Itens
- Busca ID do produto no Bling (se sincronizado)
- Usa código SKU como fallback
- Inclui descrição, quantidade, preço
- **CFOP aplicado a cada item**

#### Validação
- Verifica se produto está sincronizado
- Loga aviso se produto não encontrado no Bling
- Tenta criar pedido mesmo assim (Bling pode encontrar por código)

### 5. **Status do Pedido**

#### Mapeamento Local ↔ Bling
- `pendente_pagamento` → `P` (Pendente)
- `processando_envio` → `E` (Em aberto)
- `enviado` → `E` (Em aberto)
- `entregue` → `B` (Baixado)
- `cancelado_*` → `C` (Cancelado)

## 🔄 Fluxos de Pedido

### Fluxo 1: Criação Automática (Pagamento Confirmado)

```
1. Pagamento confirmado (webhook PagBank)
   ↓
2. sync_order_to_bling() é chamado
   ↓
3. Cliente sincronizado no Bling (se necessário)
   ↓
4. CFOP calculado (baseado em estados)
   ↓
5. Pedido criado no Bling com todos os dados
   ↓
6. Referência salva (bling_pedidos)
   ✅ Pedido disponível no Bling
```

### Fluxo 2: Atualização de Pedido

```
1. Pedido já existe no Bling (bling_pedidos)
   ↓
2. sync_order_to_bling() detecta existência
   ↓
3. Pedido atualizado no Bling (PUT)
   ✅ Dados atualizados
```

### Fluxo 3: Sincronização Manual

```
1. Admin solicita sincronização manual
   ↓
2. POST /api/bling/pedidos/sync/{venda_id}
   ↓
3. Mesmo fluxo de criação/atualização
   ✅ Pedido sincronizado
```

## 📋 Estrutura de Dados

### Formato de Pedido no Bling:

```json
{
  "cliente": {
    "nome": "João Silva",
    "tipoPessoa": "F",
    "cpf_cnpj": "12345678901",
    "ie": "",
    "endereco": "Rua das Flores, 123",
    "numero": "123",
    "complemento": "Apto 45",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "uf": "SP",
    "cep": "01234567",
    "email": "joao@example.com",
    "celular": "11999999999"
  },
  "itens": [
    {
      "idProduto": 123456,
      "codigo": "CAM-X-M",
      "descricao": "Camiseta - Estampa X - Tamanho M",
      "quantidade": 2,
      "valor": 49.90,
      "desconto": 0,
      "cfop": "5102"
    }
  ],
  "parcelas": [
    {
      "dias": 0,
      "data": "2026-01-10",
      "valor": 149.80,
      "observacoes": ""
    }
  ],
  "situacao": "E",
  "desconto": 10.00,
  "descontoUnidade": "REAL",
  "transporte": {
    "frete": 15.00,
    "fretePorConta": "E"
  },
  "observacoes": "Pedido originado do site LhamaBanana. Código: LB-20260110-ABCD"
}
```

### Mapeamento de Campos:

| Campo Local | Campo Bling | Observações |
|-------------|-------------|-------------|
| `codigo_pedido` | `observacoes` | Código incluído nas observações |
| `fiscal_cpf_cnpj` | `cliente.cpf_cnpj` | Sem formatação |
| `nome_recebedor` | `cliente.nome` | Nome do cliente |
| `estado_entrega` | `cliente.uf` | UF do cliente |
| `itens_venda` | `itens[]` | Array de itens |
| `valor_total` | `parcelas[0].valor` | Valor total na parcela |
| `valor_desconto` | `desconto` | Desconto em reais |
| `valor_frete` | `transporte.frete` | Valor do frete |
| `status_pedido` | `situacao` | Mapeado conforme regras |
| - | `itens[].cfop` | **Calculado automaticamente** |

## 🔧 Configuração

### Estado da Loja (Emitente)

```bash
# .env ou variáveis de ambiente
BLING_EMITENTE_ESTADO=SP
```

**Default**: `SP` (se não configurado)

**Como obter**: Use a UF do estado onde sua loja está registrada.

### CFOPs Suportados

| Situação | CFOP | Descrição |
|----------|------|-----------|
| Venda mesmo estado | 5102 | Venda de produção do estabelecimento |
| Venda interestadual | 6108 | Venda para outro estado |
| Compra mesmo estado | 1102 | Compra para industrialização |
| Compra interestadual | 2102 | Compra para industrialização |

**Nota**: Atualmente implementado apenas CFOPs de venda (5102 e 6108).

## ✅ Validações

### Antes de Criar Pedido:
- ✅ Cliente existe no Bling (ou sincronizado)
- ✅ Produtos sincronizados (preferencialmente)
- ✅ Dados fiscais completos
- ✅ CFOP calculado corretamente

### Dados Obrigatórios:
- ✅ CPF/CNPJ do cliente
- ✅ Endereço completo
- ✅ Itens do pedido
- ✅ Valor total

## 🎯 Como Testar

### Teste 1: Criar Pedido (Mesmo Estado)

```powershell
# Configurar estado da loja como SP
# Criar pedido para cliente em SP
# Verificar CFOP: deve ser 5102

# Verificar no Bling: pedido criado com CFOP 5102 nos itens
```

### Teste 2: Criar Pedido (Interestadual)

```powershell
# Cliente em RJ (loja em SP)
# Verificar CFOP: deve ser 6108

# Verificar no Bling: pedido criado com CFOP 6108 nos itens
```

### Teste 3: Sincronização Manual

```powershell
POST /api/bling/pedidos/sync/{venda_id}

# Verificar resposta: success: true, bling_pedido_id
# Verificar no Bling: pedido criado
```

### Teste 4: Atualização de Pedido

```powershell
# Pedido já existe no Bling
# Chamar sync novamente
# Verificar: pedido atualizado (não duplicado)
```

## ⚠️ Armadilhas Evitadas

1. **CFOP no Produto**
   - ✅ Corrigido: CFOP é do pedido/item, não do produto
   - ✅ Calculado dinamicamente baseado em estados

2. **CFOP Fixo**
   - ✅ Calculado automaticamente por pedido
   - ✅ Diferente para mesmo estado vs interestadual

3. **Duplicação de Pedidos**
   - ✅ Verifica se já existe antes de criar
   - ✅ Usa tabela `bling_pedidos` para referência
   - ✅ Atualiza em vez de criar duplicado

4. **Cliente Não Existe**
   - ✅ Sincroniza cliente antes de criar pedido
   - ✅ Não bloqueia criação se falhar (mas loga)

5. **Produtos Não Sincronizados**
   - ✅ Tenta usar ID do produto se disponível
   - ✅ Fallback para código SKU
   - ✅ Loga aviso mas não bloqueia

## 📝 Próximos Passos

Após validar criação de pedidos:
- **ETAPA 7**: NF-e (emissão automática com CFOP correto)
- **ETAPA 8**: Logística
- **ETAPA 9**: Financeiro
- **ETAPA 10**: Dashboards

## 🔗 Integração com Outras Etapas

- **ETAPA 3 (Produtos)**: Produtos devem estar sincronizados
- **ETAPA 4 (Estoque)**: Estoque atualizado após venda
- **ETAPA 5 (Clientes)**: Cliente criado automaticamente
- **ETAPA 7 (NF-e)**: CFOP será usado na emissão de nota fiscal


