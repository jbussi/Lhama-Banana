# 🔍 Como Descobrir os IDs Reais das Situações do Bling

## ⚠️ Situação Atual

Temos 9 situações com IDs temporários no banco de dados. Como o rate limiting está bloqueando a API, vamos descobrir os IDs manualmente.

## 📋 Método 1: Via Painel do Bling (Recomendado)

### Passo 1: Acessar o Bling
1. Acesse: https://www.bling.com.br
2. Faça login na sua conta

### Passo 2: Navegar até Situações
1. Vá em **Configurações** (ícone de engrenagem)
2. Procure por **"Situações de Vendas"** ou **"Status de Pedidos"**
3. Ou acesse diretamente: https://www.bling.com.br/configuracoes/situacoes-vendas

### Passo 3: Anotar os IDs
Para cada situação, anote:
- **ID** (número)
- **Nome** (exatamente como aparece)
- **Cor** (se disponível)

### Passo 4: Atualizar no Banco
Use o script `atualizar_ids_manuais.py`:

```python
# Edite o arquivo e preencha:
MAPEAMENTO_IDS = {
    "Em aberto": 1,  # Substitua pelo ID real
    "Atendido": 2,
    "Cancelado": 3,
    "Em andamento": 4,
    # ... etc
}
```

Depois execute:
```bash
docker-compose exec -T flask python atualizar_ids_manuais.py
```

## 📋 Método 2: Via API (Quando Rate Limiting Passar)

Após aguardar 15-20 minutos, execute:

```bash
docker-compose exec -T flask python renovar_token_e_sincronizar.py
```

Ou use o endpoint:
```bash
Invoke-WebRequest -Uri "http://localhost:5000/api/bling/situacoes/sync" -Method POST
```

## 📋 Método 3: Via SQL Direto

Se você descobrir os IDs, pode atualizar diretamente:

```sql
-- Exemplo: Atualizar "Em andamento" para ID 15
UPDATE bling_situacoes
SET bling_situacao_id = 15,
    atualizado_em = NOW()
WHERE nome = 'Em andamento';

-- Verificar
SELECT bling_situacao_id, nome FROM bling_situacoes WHERE nome = 'Em andamento';
```

## 🎯 Situações que Precisamos Mapear

1. Em aberto
2. Atendido
3. Cancelado
4. Em andamento ⭐ (mais importante)
5. Venda Agenciada
6. Em digitação
7. Verificado
8. Venda Atendimento Humano
9. Logística

## 💡 Dica

O ID mais importante é **"Em andamento"**, pois é o que dispara o fluxo automático de NF-e e etiquetas.

## ✅ Após Descobrir os IDs

1. Atualize usando `atualizar_ids_manuais.py`
2. Ou atualize diretamente via SQL
3. Execute: `docker-compose exec -T flask python atualizar_ids_manuais.py` para verificar
