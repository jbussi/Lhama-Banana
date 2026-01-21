# ETAPA 10 - Dashboards e Insights

## ✅ O Que Foi Implementado

### 1. **Dashboard Financeiro**

#### Métricas Principais
- ✅ **Faturamento bruto**: Soma de todas as vendas no período
- ✅ **Ticket médio**: Valor médio por pedido
- ✅ **Total de pedidos**: Quantidade de pedidos no período
- ✅ **Frete total**: Soma de todos os fretes e percentual do faturamento
- ✅ **Descontos total**: Soma de todos os descontos e percentual do faturamento
- ✅ **Contas a receber em aberto**: Total e quantidade de contas a receber

#### Periodo Customizável
- Parâmetros `start_date` e `end_date` (formato: YYYY-MM-DD)
- Se não especificado, usa último mês (30 dias)

### 2. **Vendas por Período**

#### Agrupamento Flexível
- ✅ **Por dia**: Vendas diárias
- ✅ **Por semana**: Vendas semanais
- ✅ **Por mês**: Vendas mensais

#### Dados Retornados
- Data/Período
- Quantidade de vendas
- Faturamento do período

### 3. **Produtos Mais Vendidos**

#### Métricas por Produto
- ✅ Nome do produto
- ✅ Quantidade vendida
- ✅ Faturamento gerado
- ✅ Número de pedidos em que aparece

#### Ordenação
- Ordenado por faturamento (maior para menor)
- Limite configurável (padrão: 10)

### 4. **Contas a Receber**

#### Informações
- ✅ Total em aberto
- ✅ Quantidade de contas
- ✅ Total vencidas
- ✅ Quantidade de contas vencidas

### 5. **Comparação Local vs Bling**

#### Verificação de Consistência
- ✅ Compara faturamento local vs Bling
- ✅ Compara quantidade de pedidos
- ✅ Calcula divergência em valor e percentual
- ✅ Compara frete e descontos

#### Útil Para
- Detectar divergências entre sistemas
- Validar sincronização
- Auditoria financeira

## 🔧 Endpoints Disponíveis

### Dashboard Financeiro
```http
GET /api/bling/analytics/dashboard?start_date=2026-01-01&end_date=2026-01-31
```

**Resposta:**
```json
{
  "success": true,
  "periodo": {
    "inicio": "2026-01-01",
    "fim": "2026-01-31"
  },
  "faturamento": {
    "bruto": 50000.00,
    "ticket_medio": 250.00,
    "total_pedidos": 200
  },
  "frete": {
    "total": 3000.00,
    "percentual_faturamento": 6.0
  },
  "descontos": {
    "total": 1000.00,
    "percentual_faturamento": 2.0
  },
  "contas_receber": {
    "total_aberto": 15000.00,
    "quantidade": 45,
    "total_vencidas": 2000.00,
    "quantidade_vencidas": 5
  }
}
```

### Vendas por Período
```http
GET /api/bling/analytics/vendas/periodo?start_date=2026-01-01&end_date=2026-01-31&group_by=day
```

**Parâmetros:**
- `start_date`: Data inicial (YYYY-MM-DD)
- `end_date`: Data final (YYYY-MM-DD)
- `group_by`: `day`, `week` ou `month`

**Resposta:**
```json
{
  "success": true,
  "periodo": {
    "inicio": "2026-01-01",
    "fim": "2026-01-31",
    "agrupamento": "day"
  },
  "vendas": [
    {
      "data": "2026-01-01",
      "quantidade": 10,
      "faturamento": 2500.00
    },
    {
      "data": "2026-01-02",
      "quantidade": 15,
      "faturamento": 3750.00
    }
  ],
  "total": 31
}
```

### Produtos Mais Vendidos
```http
GET /api/bling/analytics/produtos/top?start_date=2026-01-01&end_date=2026-01-31&limit=10
```

**Resposta:**
```json
{
  "success": true,
  "periodo": {
    "inicio": "2026-01-01",
    "fim": "2026-01-31"
  },
  "produtos": [
    {
      "produto_id": 123,
      "nome": "Produto A",
      "quantidade_vendida": 150,
      "faturamento": 15000.00,
      "pedidos": 120
    }
  ],
  "total": 10
}
```

### Comparação Local vs Bling
```http
GET /api/bling/analytics/comparacao?start_date=2026-01-01&end_date=2026-01-31
```

**Resposta:**
```json
{
  "success": true,
  "periodo": {
    "inicio": "2026-01-01",
    "fim": "2026-01-31"
  },
  "local": {
    "total_pedidos": 200,
    "faturamento": 50000.00,
    "frete_total": 3000.00,
    "desconto_total": 1000.00
  },
  "bling": {
    "total_pedidos": 198,
    "faturamento": 49500.00,
    "frete_total": 2900.00,
    "desconto_total": 950.00
  },
  "divergencia": {
    "faturamento": 500.00,
    "percentual": 1.0,
    "total_pedidos": 2
  }
}
```

## 🎯 Métricas Extraídas

### Financeiras
- Faturamento bruto
- Ticket médio
- Contas a receber em aberto
- Contas vencidas
- Impacto de frete (% do faturamento)
- Impacto de descontos (% do faturamento)

### Vendas
- Vendas por período (dia/semana/mês)
- Produtos mais vendidos
- Quantidade de pedidos
- Faturamento por período

### Operacionais
- Consistência entre sistemas (local vs Bling)
- Divergências de faturamento
- Divergências de quantidade de pedidos

## 📊 Dashboards Nativos do Bling

### Métricas Disponíveis no Bling
O Bling oferece dashboards nativos que complementam estas APIs:

1. **Dashboard Financeiro**
   - Fluxo de caixa
   - Contas a receber vs a pagar
   - DRE simplificado

2. **Dashboard de Vendas**
   - Vendas por vendedor
   - Vendas por categoria
   - Evolução de vendas

3. **Dashboard de Produtos**
   - Estoque por produto
   - Rotatividade de estoque
   - Produtos mais vendidos

### Limitações do Bling
- Dashboards são limitados aos dados sincronizados
- Personalização limitada
- Exportação de dados pode ser restrita

### Solução Implementada
- APIs extraem dados específicos do Bling
- Permite integração com ferramentas externas
- Comparação com dados locais para validação

## 🎯 Como Usar

### Exemplo 1: Dashboard do Mês Atual

```powershell
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

# Buscar dashboard financeiro
$startDate = (Get-Date).AddMonths(-1).ToString("yyyy-MM-dd")
$endDate = (Get-Date).ToString("yyyy-MM-dd")

Invoke-RestMethod -Uri "$ngrokUrl/api/bling/analytics/dashboard?start_date=$startDate&end_date=$endDate" `
    -Method GET -Headers @{"ngrok-skip-browser-warning"="true"}
```

### Exemplo 2: Produtos Mais Vendidos (Últimos 7 dias)

```powershell
$startDate = (Get-Date).AddDays(-7).ToString("yyyy-MM-dd")
$endDate = (Get-Date).ToString("yyyy-MM-dd")

Invoke-RestMethod -Uri "$ngrokUrl/api/bling/analytics/produtos/top?start_date=$startDate&end_date=$endDate&limit=5" `
    -Method GET -Headers @{"ngrok-skip-browser-warning"="true"}
```

### Exemplo 3: Comparação Local vs Bling

```powershell
$startDate = (Get-Date).AddMonths(-1).ToString("yyyy-MM-dd")
$endDate = (Get-Date).ToString("yyyy-MM-dd")

Invoke-RestMethod -Uri "$ngrokUrl/api/bling/analytics/comparacao?start_date=$startDate&end_date=$endDate" `
    -Method GET -Headers @{"ngrok-skip-browser-warning"="true"}
```

## ⚠️ Armadilhas e Limitações

### 1. **Dados do Bling**
- APIs do Bling podem ter rate limiting
- Alguns dados podem não estar disponíveis via API
- Sincronização pode ter delay

### 2. **Comparação Local vs Bling**
- Pequenas divergências são normais (timing, cancelamentos)
- Divergências grandes podem indicar problema de sincronização
- Validar manualmente se divergência > 5%

### 3. **Performance**
- Queries podem ser lentas para períodos longos
- Usar períodos menores (< 3 meses) para melhor performance
- Cache pode ser implementado para otimizar

### 4. **Dados Faltantes**
- Bling pode não ter todos os pedidos se sincronização falhou
- Verificar logs de sincronização se dados divergirem muito

## 🔗 Integração com Outras Etapas

- **ETAPA 6 (Pedidos)**: Dados de vendas vêm dos pedidos sincronizados
- **ETAPA 9 (Financeiro)**: Contas a receber são contabilizadas
- **ETAPA 3 (Produtos)**: Produtos mais vendidos usam dados do Bling

## 📝 Próximos Passos (Opcional)

Após validar dashboards:
- Implementar cache para melhorar performance
- Criar dashboard visual (frontend)
- Exportar dados para Excel/CSV
- Alertas automáticos para divergências grandes

## 💡 Benefícios dos Dashboards

1. **Visibilidade Financeira**
   - Faturamento em tempo real
   - Contas a receber monitoradas
   - Impacto de frete e descontos

2. **Análise de Vendas**
   - Tendências por período
   - Produtos mais vendidos
   - Identificação de oportunidades

3. **Validação de Integração**
   - Comparação local vs Bling
   - Detecção de problemas de sincronização
   - Auditoria financeira

4. **Tomada de Decisão**
   - Dados para planejamento
   - Identificação de gargalos
   - Ajustes estratégicos


