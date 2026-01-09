# 🧪 Como Testar a Sincronização de Produtos

## Pré-requisitos

1. ✅ Banco de dados com tabelas criadas (`bling_produtos`, `bling_sync_logs`)
2. ✅ OAuth do Bling configurado e autorizado (`/api/bling/authorize`)
3. ✅ Produto com NCM válido cadastrado
4. ✅ Flask rodando e acessível

## 📋 Verificar Preparação

### 1. Verificar se produto tem NCM válido

```sql
SELECT id, codigo_sku, ncm, preco_venda 
FROM produtos 
WHERE id = 6 AND ncm IS NOT NULL AND LENGTH(ncm) = 8;
```

Se não tiver, adicione:
```sql
UPDATE produtos SET ncm = '61091000' WHERE id = 6;
```

### 2. Verificar se Bling está autorizado

Acesse:
```
GET https://seu-dominio.ngrok-free.dev/api/bling/tokens
```

Deve retornar:
```json
{
  "authorized": true,
  "expires_at": "2026-01-09T..."
}
```

### 3. Verificar status do produto

```sql
SELECT * FROM bling_produtos WHERE produto_id = 6;
```

## 🚀 Testar Sincronização

### Opção 1: Via API (Recomendado)

#### Iniciar Flask
```bash
# Na raiz do projeto Lhama-Banana
python -m flask run
# Ou
python app.py
```

#### Testar sincronização
```bash
# PowerShell
$uri = "http://localhost:5000/api/bling/produtos/sync/6"
Invoke-RestMethod -Uri $uri -Method POST -ContentType "application/json" | ConvertTo-Json -Depth 10

# Ou usando curl (se disponível)
curl -X POST http://localhost:5000/api/bling/produtos/sync/6 \
  -H "Content-Type: application/json"
```

#### Verificar status após sincronização
```bash
# PowerShell
$uri = "http://localhost:5000/api/bling/produtos/status/6"
Invoke-RestMethod -Uri $uri -Method GET | ConvertTo-Json -Depth 10
```

### Opção 2: Via SQL (Verificar logs)

Após sincronizar, verifique os logs:

```sql
-- Ver últimos logs de sincronização
SELECT * FROM bling_sync_logs 
WHERE entity_type = 'produto' 
ORDER BY created_at DESC 
LIMIT 5;

-- Ver produto sincronizado
SELECT 
    p.id,
    p.codigo_sku,
    bp.bling_id,
    bp.bling_codigo,
    bp.status_sincronizacao,
    bp.ultima_sincronizacao
FROM produtos p
JOIN bling_produtos bp ON p.id = bp.produto_id
WHERE p.id = 6;
```

### Opção 3: Python Interativo

```python
from app import create_app
from blueprints.services.bling_product_service import sync_product_to_bling

app = create_app()
with app.app_context():
    result = sync_product_to_bling(6)
    print(result)
```

## ✅ Resposta Esperada

### Sucesso
```json
{
  "success": true,
  "action": "create",
  "bling_id": 12345,
  "message": "Produto sincronizado com sucesso (create)"
}
```

### Erro de Validação
```json
{
  "success": false,
  "error": "Validação falhou",
  "details": [
    "NCM obrigatório e deve ter 8 dígitos"
  ]
}
```

### Erro de API
```json
{
  "success": false,
  "error": "Erro na requisição à API Bling",
  "details": "Status 400: Bad Request"
}
```

## 🔍 Verificar no Bling

Após sincronização bem-sucedida:

1. Acesse o painel do Bling: https://www.bling.com.br
2. Vá em **Produtos** → **Lista de Produtos**
3. Procure pelo SKU do produto (`CAM-LHAMA-ESPACIAL-G`)
4. O produto deve aparecer com:
   - Nome: "Camiseta Básica Lhama - Lhama Espacial - Tamanho G"
   - SKU: "CAM-LHAMA-ESPACIAL-G"
   - NCM: "61091000"
   - Preço: R$ 64,90

## 🐛 Troubleshooting

### Erro: "Bling não autorizado"

**Solução:**
1. Acesse `/api/bling/authorize` para autorizar
2. Ou verifique se tokens estão no banco:
   ```sql
   SELECT * FROM bling_tokens;
   ```

### Erro: "NCM obrigatório"

**Solução:**
```sql
UPDATE produtos SET ncm = '61091000' WHERE id = 6;
```

### Erro: "Erro na requisição à API Bling: 401"

**Solução:**
- Token expirado, renove via `/api/bling/tokens` ou reautorize

### Erro: "Erro na requisição à API Bling: 400"

**Solução:**
- Verifique os logs em `bling_sync_logs`:
  ```sql
  SELECT error_message, response_data 
  FROM bling_sync_logs 
  WHERE entity_type = 'produto' 
  ORDER BY created_at DESC 
  LIMIT 1;
  ```

## 📊 Sincronizar Todos os Produtos

```bash
# PowerShell
$uri = "http://localhost:5000/api/bling/produtos/sync-all"
$body = @{
    limit = 5
    only_active = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri $uri -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 10
```

Isso vai sincronizar apenas 5 produtos ativos por vez (para não sobrecarregar a API).

## 📝 Próximos Passos

Após testar com sucesso:

1. ✅ Verificar produtos no Bling
2. ✅ Testar atualização (alterar produto e sincronizar novamente)
3. ✅ Sincronizar mais produtos
4. ✅ Implementar sincronização automática (workers/triggers)

