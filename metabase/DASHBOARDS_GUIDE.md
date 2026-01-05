# 📊 Guia Completo de Criação de Dashboards no Metabase

Este guia fornece instruções passo a passo para criar todos os dashboards solicitados no Metabase.

## 🔧 Configuração Inicial

### 1. Adicionar Conexão com PostgreSQL

1. Acesse o Metabase: `http://localhost:5000/analytics`
2. Faça login como administrador
3. Vá em **Settings** → **Admin** → **Databases**
4. Clique em **Add database**
5. Selecione **PostgreSQL**
6. Preencha os dados:
   - **Name**: `LhamaBanana DB`
   - **Host**: `postgres` (nome do serviço Docker)
   - **Port**: `5432`
   - **Database name**: `sistema_usuarios`
   - **Username**: `postgres` (ou valor de `DB_USER`)
   - **Password**: `far111111` (ou valor de `DB_PASSWORD`)
   - **Use a secure connection (SSL)**: ❌ Desabilitado (conexão interna)
7. Clique em **Save**

### 2. Configurar Sincronização

1. Após criar a conexão, clique no banco de dados
2. Vá em **Synchronization schedule**
3. Configure para sincronizar automaticamente (recomendado: a cada hora)
4. Clique em **Save**

---

## 📈 Dashboard 1: Vendas

### Métricas a Criar:

#### 1.1. Total de Vendas (Contador)
- **Tipo**: Number
- **Query**: Use a query `1.1. Total de Vendas` do arquivo `queries.sql`
- **Formatação**: Número inteiro

#### 1.2. Receita Total (Contador)
- **Tipo**: Number
- **Query**: Use a query `1.2. Receita Total`
- **Formatação**: Moeda (BRL)

#### 1.3. Ticket Médio (Contador)
- **Tipo**: Number
- **Query**: Use a query `1.3. Ticket Médio`
- **Formatação**: Moeda (BRL)

#### 1.4. Vendas por Dia (Gráfico de Linha)
- **Tipo**: Line Chart
- **Query**: Use a query `1.4. Vendas por Período (Dia)`
- **Eixo X**: `dia`
- **Eixo Y**: `total_vendas` e `receita_dia`

#### 1.5. Vendas por Semana (Gráfico de Linha)
- **Tipo**: Line Chart
- **Query**: Use a query `1.5. Vendas por Período (Semana)`
- **Eixo X**: `semana`
- **Eixo Y**: `total_vendas`

#### 1.6. Vendas por Mês (Gráfico de Linha)
- **Tipo**: Line Chart
- **Query**: Use a query `1.6. Vendas por Período (Mês)`
- **Eixo X**: `mes`
- **Eixo Y**: `receita_mes`

#### 1.7. Status dos Pedidos (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `1.7. Status dos Pedidos`
- **Categoria**: `status_pedido`
- **Valor**: `quantidade`

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `📊 Dashboard de Vendas`
3. Adicione todas as métricas criadas acima
4. Organize os cards de forma visual
5. Configure atualização automática (opcional)

---

## 📦 Dashboard 2: Produtos

### Métricas a Criar:

#### 2.1. Produtos Mais Vendidos (Tabela)
- **Tipo**: Table
- **Query**: Use a query `2.1. Produtos Mais Vendidos`
- **Colunas**: Nome, Total Vendido, Quantidade Total, Receita Total

#### 2.2. Estoque Atual vs Mínimo (Gráfico de Barras)
- **Tipo**: Bar Chart
- **Query**: Use a query `2.3. Estoque Atual vs Estoque Mínimo`
- **Eixo X**: `nome_produto`
- **Eixo Y**: `estoque` e `estoque_minimo`

#### 2.3. Produtos com Estoque Baixo (Alerta - Tabela)
- **Tipo**: Table
- **Query**: Use a query `2.4. Produtos com Estoque Baixo`
- **Formatação**: Destaque linhas com `status_estoque = 'Estoque Baixo'`

#### 2.4. Total de Produtos por Categoria (Gráfico de Barras)
- **Tipo**: Bar Chart
- **Query**: Use a query `2.6. Total de Produtos por Categoria`
- **Eixo X**: `categoria`
- **Eixo Y**: `total_produtos`

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `📦 Dashboard de Produtos`
3. Adicione todas as métricas
4. Configure alertas para estoque baixo (opcional)

---

## 💳 Dashboard 3: Pagamentos

### Métricas a Criar:

#### 3.1. Status de Pagamentos (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `3.1. Status de Pagamentos`
- **Categoria**: `status_pagamento`
- **Valor**: `quantidade`

#### 3.2. Métodos de Pagamento (Gráfico de Barras)
- **Tipo**: Bar Chart
- **Query**: Use a query `3.2. Métodos de Pagamento`
- **Eixo X**: `forma_pagamento_tipo`
- **Eixo Y**: `valor_total`

#### 3.3. Taxa de Conversão (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `3.3. Taxa de Conversão`
- **Categoria**: `status_grupo`
- **Valor**: `percentual`

#### 3.4. Performance por Método (Tabela)
- **Tipo**: Table
- **Query**: Use a query `3.4. Performance por Método de Pagamento`
- **Colunas**: Método, Total, Pagos, Taxa de Sucesso, Receita

#### 3.5. Pedidos Pagos vs Abandonados (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `3.6. Pedidos Pagos vs Abandonados`
- **Categoria**: `status_grupo`
- **Valor**: `quantidade_pedidos`

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `💳 Dashboard de Pagamentos`
3. Adicione todas as métricas
4. Configure cores para status (verde=pago, amarelo=pendente, vermelho=cancelado)

---

## 🚚 Dashboard 4: Frete e Envios

### Métricas a Criar:

#### 4.1. Total de Etiquetas (Contador)
- **Tipo**: Number
- **Query**: Use a query `4.1. Total de Etiquetas Geradas`

#### 4.2. Status de Etiquetas (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `4.2. Status de Etiquetas`
- **Categoria**: `status_etiqueta`
- **Valor**: `quantidade`

#### 4.3. Etiquetas por Transportadora (Gráfico de Barras)
- **Tipo**: Bar Chart
- **Query**: Use a query `4.3. Etiquetas por Transportadora`
- **Eixo X**: `transportadora_nome`
- **Eixo Y**: `total_etiquetas`

#### 4.4. Etiquetas Enviadas vs Pendentes (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `4.4. Etiquetas Enviadas vs Pendentes`
- **Categoria**: `status_grupo`
- **Valor**: `quantidade`

#### 4.5. Etiquetas por Período (Gráfico de Linha)
- **Tipo**: Line Chart
- **Query**: Use a query `4.6. Etiquetas por Período`
- **Eixo X**: `dia`
- **Eixo Y**: `total_etiquetas` e `entregues`

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `🚚 Dashboard de Frete`
3. Adicione todas as métricas
4. Configure alertas para etiquetas pendentes (opcional)

---

## 🎟️ Dashboard 5: Cupons

### Métricas a Criar:

#### 5.1. Total de Cupons Utilizados (Contador)
- **Tipo**: Number
- **Query**: Use a query `5.1. Cupons Utilizados (Total)`

#### 5.2. Cupons Mais Utilizados (Tabela)
- **Tipo**: Table
- **Query**: Use a query `5.2. Cupons Mais Utilizados`
- **Colunas**: Código, Tipo, Valor, Vezes Usado, Desconto Total

#### 5.3. Cupons por Status (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `5.3. Cupons por Status`
- **Categoria**: `status`
- **Valor**: `total_cupons`

#### 5.4. Cupons Utilizados por Período (Gráfico de Linha)
- **Tipo**: Line Chart
- **Query**: Use a query `5.4. Cupons Utilizados por Período`
- **Eixo X**: `dia`
- **Eixo Y**: `vezes_usado` e `desconto_total`

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `🎟️ Dashboard de Cupons`
3. Adicione todas as métricas

---

## 👥 Dashboard 6: Usuários e Clientes

### Métricas a Criar:

#### 6.1. Total de Usuários (Contador)
- **Tipo**: Number
- **Query**: Use a query `6.1. Total de Usuários`

#### 6.2. Novos Usuários por Período (Gráfico de Linha)
- **Tipo**: Line Chart
- **Query**: Use a query `6.2. Novos Usuários por Período`
- **Eixo X**: `dia`
- **Eixo Y**: `novos_usuarios`

#### 6.3. Usuários por Role (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `6.3. Usuários por Role`
- **Categoria**: `role`
- **Valor**: `quantidade`

#### 6.4. Top Clientes (Tabela)
- **Tipo**: Table
- **Query**: Use a query `6.4. Top Clientes`
- **Colunas**: Nome, Email, Total Pedidos, Total Gasto, Ticket Médio

#### 6.5. Clientes por Estado (Gráfico de Barras)
- **Tipo**: Bar Chart
- **Query**: Use a query `6.5. Clientes por Estado`
- **Eixo X**: `estado`
- **Eixo Y**: `total_clientes`

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `👥 Dashboard de Usuários`
3. Adicione todas as métricas

---

## ⚙️ Dashboard 7: Métricas Operacionais

### Métricas a Criar:

#### 7.1. Pedidos por Prioridade (Gráfico de Barras)
- **Tipo**: Bar Chart
- **Query**: Use a query `7.1. Pedidos por Prioridade`
- **Eixo X**: `prioridade`
- **Eixo Y**: `quantidade`

#### 7.2. Tempo Médio de Processamento (Contador)
- **Tipo**: Number
- **Query**: Use a query `7.2. Tempo Médio de Processamento`
- **Formatação**: Número com 2 casas decimais + "horas"

#### 7.3. Pedidos Atrasados (Tabela)
- **Tipo**: Table
- **Query**: Use a query `7.3. Pedidos Atrasados`
- **Colunas**: Código Pedido, Data Venda, Status, Dias em Aberto, Valor

#### 7.4. Taxa de Cancelamento (Contador)
- **Tipo**: Number
- **Query**: Use a query `7.4. Taxa de Cancelamento`
- **Formatação**: Percentual

#### 7.5. Receita por Origem (Gráfico de Pizza)
- **Tipo**: Pie Chart
- **Query**: Use a query `7.5. Receita por Origem`
- **Categoria**: `origem`
- **Valor**: `receita_total`

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `⚙️ Métricas Operacionais`
3. Adicione todas as métricas
4. Configure alertas para pedidos atrasados (opcional)

---

## 🎯 Dashboard 8: Visão Geral (Overview)

### Métricas a Criar:

#### 8.1. Métricas Principais (Cards)
- **Tipo**: Multiple Cards
- **Query**: Use a query `8.1. Métricas Principais`
- Crie cards separados para cada métrica:
  - Total de Vendas
  - Receita Total
  - Ticket Médio
  - Clientes Únicos
  - Produtos Vendidos
  - Etiquetas Geradas

#### 8.2. Comparativo Mensal (Gráfico de Linha)
- **Tipo**: Line Chart
- **Query**: Use a query `8.2. Comparativo Mensal`
- **Eixo X**: `mes`
- **Eixo Y**: `receita` e `total_vendas`

#### 8.3. Top 5 Produtos do Mês (Tabela)
- **Tipo**: Table
- **Query**: Use a query `8.3. Top 5 Produtos do Mês`
- **Colunas**: Produto, Quantidade Vendida, Receita

### Criar o Dashboard:

1. Clique em **+ New** → **Dashboard**
2. Nome: `🎯 Visão Geral`
3. Adicione todas as métricas
4. Configure como dashboard principal (pinned)

---

## 🎨 Dicas de Customização

### Cores Recomendadas:

- **Sucesso/Pago**: Verde (#4CAF50)
- **Pendente**: Amarelo (#FFC107)
- **Cancelado/Erro**: Vermelho (#F44336)
- **Informação**: Azul (#2196F3)

### Filtros Úteis:

Adicione filtros de data aos dashboards:
- Últimos 7 dias
- Últimos 30 dias
- Últimos 3 meses
- Período customizado

### Atualização Automática:

Configure atualização automática para dashboards importantes:
1. Abra o dashboard
2. Clique em **Auto-refresh**
3. Configure intervalo (ex: a cada 5 minutos)

---

## 📝 Próximos Passos

1. ✅ Criar todos os dashboards acima
2. ⏳ Configurar alertas (estoque baixo, pedidos atrasados)
3. ⏳ Criar relatórios agendados (email semanal)
4. ⏳ Compartilhar dashboards com equipe (se necessário)
5. ⏳ Documentar queries customizadas específicas do projeto

---

**Arquivo de Referência**: `metabase/queries.sql` contém todas as queries prontas para uso.


