# ETAPA 9 - Integração Financeira com Bling

## ✅ O Que Foi Implementado

### 1. **Contas a Receber no Bling**

#### Criação Automática
- ✅ Conta a receber criada quando pagamento é confirmado (webhook PagBank)
- ✅ Vinculada ao pedido e cliente no Bling
- ✅ Suporta diferentes formas de pagamento (PIX, Cartão, Boleto)

#### Tratamento de Parcelas
- ✅ **PIX**: Uma conta a receber com vencimento no dia do pagamento
- ✅ **Cartão Parcelado**: Múltiplas contas a receber (uma por parcela)
- ✅ **Boleto/Cartão à Vista**: Uma conta a receber

### 2. **Integração com Pagamentos**

#### Sincronização Automática
- Quando pagamento é confirmado (PAID/AUTHORIZED) → Cria conta a receber
- Vincula ao pedido já existente no Bling
- Usa dados do cliente já sincronizado

#### Dados Sincronizados
- Valor total ou valor da parcela
- Data de vencimento
- Número do documento (PED-{codigo_pedido})
- Observações com informações do pagamento
- Vinculação ao pedido (origem)

### 3. **Armazenamento de Referências**

#### Tabela `bling_contas_receber`
- Armazena referência entre venda local e conta a receber no Bling
- Evita duplicação (verifica antes de criar)
- Permite rastreabilidade

### 4. **Configurações**

#### Variáveis de Ambiente
- `BLING_CATEGORIA_VENDAS_ID`: ID da categoria de vendas no Bling
- `BLING_VENDEDOR_ID`: ID do vendedor padrão (opcional)

## 🔄 Fluxos Financeiros

### Fluxo 1: Pagamento Confirmado → Conta a Receber

```
1. Pagamento confirmado (webhook PagBank)
   ↓
2. Pedido já sincronizado com Bling
   ↓
3. Cliente já existe no Bling (criado na sincronização do pedido)
   ↓
4. Criar conta(s) a receber no Bling
   ↓
5. Vincular ao pedido e cliente
   ↓
✅ Conta a receber criada e rastreada
```

### Fluxo 2: Cartão Parcelado

```
1. Pagamento confirmado: Cartão 3x R$ 100,00
   ↓
2. Criar 3 contas a receber:
   - Parcela 1: R$ 100,00 - Venc: hoje
   - Parcela 2: R$ 100,00 - Venc: hoje + 30 dias
   - Parcela 3: R$ 100,00 - Venc: hoje + 60 dias
   ↓
✅ Todas vinculadas ao mesmo pedido
```

### Fluxo 3: PIX

```
1. Pagamento confirmado: PIX R$ 500,00
   ↓
2. Criar 1 conta a receber:
   - Valor: R$ 500,00
   - Vencimento: Hoje (já pago)
   - Data pagamento: Hoje
   ↓
✅ Conta criada e já marcada como paga
```

## 📋 Estrutura de Dados

### Conta a Receber no Bling:

```json
{
  "dataEmissao": "2026-01-10",
  "vencimento": "2026-01-10",
  "valor": 500.00,
  "numero": "PED-LB-20260110-ABCD",
  "dataPagamento": "2026-01-10",  // Se PIX
  "competencia": "2026-01-10",
  "historico": "Pagamento PIX - Pedido LB-20260110-ABCD",
  "categoria": {
    "id": 123  // Categoria de vendas
  },
  "cliente": {
    "id": 456  // ID do cliente no Bling
  },
  "origem": {
    "id": 789,  // ID do pedido no Bling
    "tipo": "Venda"
  }
}
```

### Tabela de Referências:

```sql
bling_contas_receber (
  id SERIAL PRIMARY KEY,
  venda_id INTEGER REFERENCES vendas(id),
  bling_conta_receber_id BIGINT,
  numero_documento VARCHAR(100),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

## 🔧 Endpoints Disponíveis

### Criar Conta a Receber Manualmente
```http
POST /api/bling/financeiro/conta-receber/{venda_id}
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "action": "created",
  "contas_criadas": [
    {
      "bling_id": 123456,
      "numero_documento": "PED-LB-20260110-ABCD",
      "valor": 500.00
    }
  ],
  "message": "1 conta(s) a receber criada(s) no Bling"
}
```

## ✅ Validações Implementadas

### Antes de Criar:
- ✅ Pagamento confirmado existe
- ✅ Pedido existe no Bling
- ✅ Cliente existe no Bling (cria se necessário)
- ✅ Verifica se conta já existe (evita duplicação)

### Dados Obrigatórios:
- ✅ Valor do pagamento
- ✅ Cliente (vinculado ao pedido)
- ✅ Pedido no Bling
- ✅ Categoria de vendas (opcional, busca padrão)

## 🎯 Como Testar

### Teste 1: Criação Automática (Pagamento Confirmado)

```powershell
# 1. Confirmar pagamento (webhook PagBank)
# 2. Verificar logs: conta a receber criada automaticamente
# 3. Verificar no Bling: conta a receber vinculada ao pedido
```

### Teste 2: Criação Manual

```powershell
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

# Criar conta a receber para venda específica
Invoke-RestMethod -Uri "$ngrokUrl/api/bling/financeiro/conta-receber/1" `
    -Method POST -Headers @{"ngrok-skip-browser-warning"="true"}
```

### Teste 3: Cartão Parcelado

```powershell
# 1. Criar venda com cartão parcelado (ex: 3x)
# 2. Confirmar pagamento
# 3. Verificar no Bling: 3 contas a receber criadas
```

## ⚠️ Armadilhas Evitadas

1. **Duplicação de Contas**
   - ✅ Verifica se conta já existe antes de criar
   - ✅ Usa número de documento único

2. **Cliente Não Existente**
   - ✅ Cria cliente automaticamente se não existir
   - ✅ Usa dados fiscais da venda

3. **Pedido Não Sincronizado**
   - ✅ Verifica se pedido existe no Bling
   - ✅ Sugere sincronização se não encontrado

4. **Categoria Não Configurada**
   - ✅ Busca categoria padrão se não configurada
   - ✅ Pode usar primeira categoria disponível

5. **Parcerias Incorretas**
   - ✅ Calcula valor correto por parcela
   - ✅ Última parcela ajusta diferença se houver

## 📝 Configuração Necessária

### Variáveis de Ambiente (Opcional):

```env
# ID da categoria de vendas no Bling (opcional, busca automaticamente se não configurado)
BLING_CATEGORIA_VENDAS_ID=123

# ID do vendedor padrão no Bling (opcional)
BLING_VENDEDOR_ID=456
```

### Como Obter IDs:

1. **Categoria**: Acesse Bling → Configurações → Categorias de Receitas
2. **Vendedor**: Acesse Bling → Configurações → Vendedores

## 🔗 Integração com Outras Etapas

- **ETAPA 5 (Clientes)**: Cliente deve existir no Bling
- **ETAPA 6 (Pedidos)**: Pedido deve existir no Bling
- **ETAPA 7 (NF-e)**: NF-e pode ser vinculada à conta a receber
- **PagBank**: Webhook de pagamento confirma criação de conta

## 📝 Próximos Passos

Após validar integração financeira:
- **ETAPA 10**: Dashboards e insights (métricas financeiras)

---

## 💡 Benefícios da Integração Financeira

1. **Rastreabilidade Completa**
   - Todas as vendas refletidas nas contas a receber do Bling
   - Fácil identificação de pagamentos pendentes

2. **Relatórios Financeiros**
   - Usar dashboards nativos do Bling
   - Faturamento por período
   - Contas a receber em aberto

3. **Gestão de Parcelas**
   - Cartão parcelado gerencia múltiplas contas
   - Seguimento de cada parcela

4. **Reconciliação Automática**
   - Pagamentos confirmados automaticamente criam contas
   - Reduz trabalho manual de lançamento

