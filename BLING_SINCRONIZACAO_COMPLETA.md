# 🔄 Sincronização Completa Bling - LhamaBanana

## ✅ Funcionalidades Implementadas

### 1. Sincronização de Produtos (Local → Bling)
- ✅ Criar produtos no Bling
- ✅ Atualizar produtos existentes no Bling
- ✅ Mapeamento completo de campos
- ✅ Validações antes de sincronizar

### 2. Importação de Produtos (Bling → Local)
- ✅ Buscar produtos do Bling
- ✅ Criar produtos no banco local
- ✅ Atualizar produtos existentes
- ✅ Manter referência bidirecional

### 3. Sincronização de Estoque
- ✅ **Do Bling para o banco local** (atualizar estoque local)
- ✅ **Do banco local para o Bling** (atualizar estoque no Bling)
- ✅ **Bidirecional** (ambas as direções)

## 📡 Endpoints Disponíveis

### Sincronização Local → Bling

#### 1. Sincronizar Produto Específico
```
POST /api/bling/produtos/sync/<produto_id>
```

**Exemplo:**
```powershell
$uri = "$ngrokUrl/api/bling/produtos/sync/6"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"
```

#### 2. Sincronizar Todos os Produtos
```
POST /api/bling/produtos/sync-all
Body: {"limit": 10, "only_active": true}
```

### Importação Bling → Local

#### 3. Importar Produtos do Bling
```
POST /api/bling/produtos/import
Body: {"limit": 50}
```

**Exemplo:**
```powershell
$uri = "$ngrokUrl/api/bling/produtos/import"
$body = @{ limit = 10 } | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method POST -Body $body -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"
```

**O que faz:**
- Busca produtos do Bling
- Cria produtos no banco local (se não existirem)
- Atualiza produtos existentes (se já existirem pelo SKU)
- Salva referência bidirecional (`bling_produtos`)

### Sincronização de Estoque

#### 4. Sincronizar Estoque do Bling para Local
```
POST /api/bling/estoque/sync-from-bling
Body: {"produto_id": 6}  # Opcional: sem produto_id sincroniza todos
```

**Exemplo:**
```powershell
# Sincronizar estoque de um produto específico
$uri = "$ngrokUrl/api/bling/estoque/sync-from-bling"
$body = @{ produto_id = 6 } | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method POST -Body $body -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"

# Sincronizar estoque de todos os produtos
$body = @{} | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method POST -Body $body -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"
```

**O que faz:**
- Busca estoque atual do produto no Bling
- Atualiza estoque no banco local
- Registra log de sincronização

#### 5. Sincronizar Estoque do Local para Bling
```
POST /api/bling/estoque/sync-to-bling
Body: {"produto_id": 6}  # Opcional: sem produto_id sincroniza todos
```

**Exemplo:**
```powershell
# Atualizar estoque no Bling com valor do banco local
$uri = "$ngrokUrl/api/bling/estoque/sync-to-bling"
$body = @{ produto_id = 6 } | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method POST -Body $body -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"
```

**O que faz:**
- Busca estoque atual no banco local
- Atualiza estoque no Bling
- Mantém estoque mínimo e máximo no Bling

#### 6. Sincronização Bidirecional de Estoque
```
POST /api/bling/estoque/sync/<produto_id>
Body: {"direction": "both"}  # "both", "from", "to"
```

**Exemplo:**
```powershell
# Sincronização bidirecional (do Bling para local E do local para Bling)
$uri = "$ngrokUrl/api/bling/estoque/sync/6"
$body = @{ direction = "both" } | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method POST -Body $body -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json"

# Apenas do Bling para local
$body = @{ direction = "from" } | ConvertTo-Json

# Apenas do local para Bling
$body = @{ direction = "to" } | ConvertTo-Json
```

## 🔧 Configuração do ngrok

### Variável de Ambiente

Configure a URL do ngrok no `.env`:
```bash
NGROK_URL=https://seu-dominio.ngrok-free.dev
```

Ou no PowerShell:
```powershell
$env:NGROK_URL = "https://seu-dominio.ngrok-free.dev"
```

### Script de Teste Atualizado

O script `COMANDO_TESTE_SYNC.ps1` já está configurado para usar ngrok automaticamente.

## 📋 Fluxos de Uso

### Fluxo 1: Criar Produtos no Bling (Local → Bling)

```
1. Criar produto no banco local
   ↓
2. POST /api/bling/produtos/sync/<id>
   ↓
3. Produto criado no Bling
   ↓
4. Referência salva em bling_produtos
```

### Fluxo 2: Importar Produtos do Bling (Bling → Local)

```
1. POST /api/bling/produtos/import
   ↓
2. Busca produtos do Bling
   ↓
3. Para cada produto:
   - Se existe no local (por SKU) → Atualiza
   - Se não existe → Cria novo
   ↓
4. Salva referência bidirecional
```

### Fluxo 3: Sincronizar Estoque (Bling → Local)

```
1. Produto vendido no Bling (estoque diminui)
   ↓
2. POST /api/bling/estoque/sync-from-bling
   ↓
3. Busca estoque atual do Bling
   ↓
4. Atualiza estoque no banco local
```

### Fluxo 4: Sincronizar Estoque (Local → Bling)

```
1. Produto vendido na loja (estoque diminui no local)
   ↓
2. POST /api/bling/estoque/sync-to-bling
   ↓
3. Busca estoque atual do banco local
   ↓
4. Atualiza estoque no Bling
```

## 🧪 Testes Completos

### Teste 1: Sincronizar Produto Local → Bling

```powershell
# Configurar URL do ngrok
$ngrokUrl = "https://seu-dominio.ngrok-free.dev"

# Sincronizar produto ID 6
$uri = "$ngrokUrl/api/bling/produtos/sync/6"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json" | ConvertTo-Json -Depth 10
```

### Teste 2: Importar Produtos do Bling

```powershell
# Importar 10 produtos do Bling
$uri = "$ngrokUrl/api/bling/produtos/import"
$body = @{ limit = 10 } | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method POST -Body $body -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json" | ConvertTo-Json -Depth 10
```

### Teste 3: Sincronizar Estoque do Bling

```powershell
# Sincronizar estoque de todos os produtos
$uri = "$ngrokUrl/api/bling/estoque/sync-from-bling"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json" | ConvertTo-Json -Depth 10
```

### Teste 4: Sincronizar Estoque para Bling

```powershell
# Atualizar estoque no Bling com valores do banco local
$uri = "$ngrokUrl/api/bling/estoque/sync-to-bling"
Invoke-RestMethod -Uri $uri -Method POST -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json" | ConvertTo-Json -Depth 10
```

### Teste 5: Sincronização Bidirecional

```powershell
# Sincronização completa (ambas as direções)
$uri = "$ngrokUrl/api/bling/estoque/sync/6"
$body = @{ direction = "both" } | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method POST -Body $body -Headers @{"ngrok-skip-browser-warning"="true"} -ContentType "application/json" | ConvertTo-Json -Depth 10
```

## 📊 Verificar Logs

### Ver logs de sincronização

```sql
-- Últimos logs
SELECT * FROM bling_sync_logs 
ORDER BY created_at DESC 
LIMIT 20;

-- Logs de sincronização de estoque
SELECT * FROM bling_sync_logs 
WHERE action = 'sync' 
AND response_data->>'action' LIKE '%stock%'
ORDER BY created_at DESC;
```

### Ver produtos sincronizados

```sql
SELECT 
    p.id,
    p.codigo_sku,
    p.estoque as estoque_local,
    bp.bling_id,
    bp.bling_codigo,
    bp.status_sincronizacao
FROM produtos p
JOIN bling_produtos bp ON p.id = bp.produto_id
ORDER BY bp.ultima_sincronizacao DESC;
```

## ⚙️ Automação Futura

### Workers/Cron Jobs Sugeridos

1. **Sincronização de Estoque Diária**
   ```python
   # Executar diariamente às 2h da manhã
   sync_stock_from_bling()
   ```

2. **Importação de Novos Produtos**
   ```python
   # Executar semanalmente
   sync_products_from_bling(limit=100)
   ```

3. **Sincronização de Produtos Alterados**
   ```python
   # Executar a cada hora
   sync_all_products(only_active=True)
   ```

## 🎯 Casos de Uso

### Caso 1: Produto criado no Bling
**Solução:** Use `/api/bling/produtos/import` para importar

### Caso 2: Venda feita no Bling (estoque diminuiu)
**Solução:** Use `/api/bling/estoque/sync-from-bling` para atualizar local

### Caso 3: Venda feita na loja (estoque diminuiu local)
**Solução:** Use `/api/bling/estoque/sync-to-bling` para atualizar Bling

### Caso 4: Produto alterado no local
**Solução:** Use `/api/bling/produtos/sync/<id>` para atualizar Bling

## 📝 Próximos Passos

1. ✅ Sincronização de produtos (local → Bling)
2. ✅ Importação de produtos (Bling → local)
3. ✅ Sincronização de estoque bidirecional
4. ⏳ Automação via workers/cron
5. ⏳ Webhooks do Bling (quando disponível)
6. ⏳ Sincronização de pedidos

## 🔗 Links Úteis

- [Documentação API Bling - Produtos](https://developer.bling.com.br/referencia/produtos)
- Teste da API: `GET /api/bling/test`
- Status: `GET /api/bling/status`
- Tokens: `GET /api/bling/tokens`

