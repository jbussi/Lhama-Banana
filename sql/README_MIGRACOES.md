# 📋 Guia de Migrações do Banco de Dados

Este diretório contém os scripts SQL para criar e atualizar o banco de dados do sistema.

## 📁 Arquivos de Scripts

### 1. `criar-banco-de-dados.sql`
Script principal para criar o banco de dados completo do zero.
- Cria todas as tabelas principais (usuários, produtos, carrinho, etc.)
- Cria tabelas de vendas e pagamentos
- Inclui todas as constraints e índices básicos

**Uso:** Execute este script apenas se estiver criando o banco pela primeira vez.

### 2. `tabela_etiquetas.sql`
Script para criar a tabela de etiquetas de frete (Melhor Envio).
- Tabela `etiquetas_frete` para rastrear etiquetas de envio

**Uso:** Execute se precisar de funcionalidade de etiquetas de frete.

### 3. `atualizar-checkout-pagamentos.sql` ⭐ **NOVO**
Script de atualização para adicionar suporte completo ao checkout com PagBank.
- Adiciona campos `valor_frete` e `valor_desconto` na tabela `vendas`
- Cria/atualiza tabela `pagamentos` com todos os campos necessários
- Adiciona campo `role` na tabela `usuarios` (para sistema admin)
- Cria índices para melhor performance
- Atualiza constraints de status

**Uso:** Execute este script se já tem um banco de dados existente e quer adicionar suporte ao checkout.

## 🚀 Como Executar as Migrações

### Opção 1: PostgreSQL via psql (linha de comando)

```bash
# Conecte ao PostgreSQL
psql -U postgres -d sistema_usuarios

# Execute o script de atualização
\i sql/atualizar-checkout-pagamentos.sql
```

### Opção 2: PostgreSQL via pgAdmin

1. Abra o pgAdmin
2. Conecte ao servidor PostgreSQL
3. Selecione o banco de dados `sistema_usuarios`
4. Clique com botão direito → Query Tool
5. Abra o arquivo `sql/atualizar-checkout-pagamentos.sql`
6. Execute (F5)

### Opção 3: Python Script (recomendado)

```python
import psycopg2
from config import Config

# Conecte ao banco
conn = psycopg2.connect(
    host=Config.DATABASE_CONFIG['host'],
    dbname=Config.DATABASE_CONFIG['dbname'],
    user=Config.DATABASE_CONFIG['user'],
    password=Config.DATABASE_CONFIG['password']
)

# Leia e execute o script
with open('sql/atualizar-checkout-pagamentos.sql', 'r', encoding='utf-8') as f:
    script = f.read()
    
cur = conn.cursor()
cur.execute(script)
conn.commit()
cur.close()
conn.close()

print("✅ Migração executada com sucesso!")
```

## ⚠️ Importante

1. **Backup antes de executar:** Sempre faça backup do banco antes de executar scripts de atualização
2. **Teste em ambiente de desenvolvimento primeiro**
3. **Verifique os logs:** O script usa `RAISE NOTICE` para informar o que foi feito
4. **Idempotente:** O script é seguro para executar múltiplas vezes (verifica se campos já existem)

## 📊 Estrutura das Tabelas Principais

### `vendas` (Pedidos)
- Armazena informações de cada pedido
- Campos principais: `codigo_pedido`, `usuario_id`, `valor_total`, `valor_frete`, `valor_desconto`
- Status: `pendente`, `pendente_pagamento`, `processando_envio`, `enviado`, `entregue`, etc.

### `pagamentos` (Transações de Pagamento)
- Armazena informações de pagamentos (PagBank)
- Campos principais: `pagbank_transaction_id`, `forma_pagamento_tipo`, `status_pagamento`
- Suporta: PIX, Boleto, Cartão de Crédito
- Links de QR Code, boleto, etc.

### `itens_venda` (Itens do Pedido)
- Armazena os produtos de cada pedido
- Snapshot dos dados do produto no momento da compra

### `etiquetas_frete` (Etiquetas de Envio)
- Armazena informações de etiquetas geradas pelo Melhor Envio
- Tracking de envios

## 🔄 Ordem Recomendada de Execução

1. Se banco novo: Execute `criar-banco-de-dados.sql`
2. Se banco existente: Execute `atualizar-checkout-pagamentos.sql`
3. Se usar Melhor Envio: Execute `tabela_etiquetas.sql`

## 📝 Notas

- Todos os scripts usam `CREATE TABLE IF NOT EXISTS` ou verificam existência antes de criar/alterar
- Os scripts são seguros para execução múltipla (idempotentes)
- Sempre verifique os logs após execução para garantir que tudo foi aplicado

