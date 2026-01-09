# 🔄 Sincronização de Produtos com Bling

## ✅ Implementação Completa

A sincronização de produtos do LhamaBanana para o Bling foi implementada e está pronta para uso.

## 📋 Setup Inicial

### 1. Criar Tabelas no Banco de Dados

Execute o script SQL para criar as tabelas necessárias:

```sql
-- Arquivo: sql/create-bling-tables.sql
-- Execute no PostgreSQL
```

Ou execute diretamente:

```sql
CREATE TABLE IF NOT EXISTS bling_produtos (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER REFERENCES produtos(id) ON DELETE CASCADE UNIQUE NOT NULL,
    bling_id INTEGER NOT NULL,
    bling_codigo VARCHAR(50) NOT NULL,
    ultima_sincronizacao TIMESTAMP DEFAULT NOW(),
    status_sincronizacao VARCHAR(20) DEFAULT 'sync' CHECK (status_sincronizacao IN ('sync', 'error', 'pending')),
    erro_ultima_sync TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bling_sync_logs (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('produto', 'pedido', 'nfe', 'cliente')),
    entity_id INTEGER,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'sync', 'delete')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error', 'pending')),
    response_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bling_produtos_produto_id ON bling_produtos(produto_id);
CREATE INDEX IF NOT EXISTS idx_bling_produtos_bling_id ON bling_produtos(bling_id);
CREATE INDEX IF NOT EXISTS idx_bling_produtos_bling_codigo ON bling_produtos(bling_codigo);
CREATE INDEX IF NOT EXISTS idx_bling_sync_logs_entity ON bling_sync_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_bling_sync_logs_created_at ON bling_sync_logs(created_at DESC);
```

## 📡 Endpoints Disponíveis

### 1. Sincronizar Produto Específico

```
POST /api/bling/produtos/sync/<produto_id>
```

**Exemplo:**
```bash
POST https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/produtos/sync/1
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "action": "create",
  "bling_id": 12345,
  "message": "Produto sincronizado com sucesso (create)"
}
```

**Resposta de Erro:**
```json
{
  "success": false,
  "error": "Validação falhou",
  "details": ["NCM obrigatório e deve ter 8 dígitos"]
}
```

### 2. Sincronizar Todos os Produtos

```
POST /api/bling/produtos/sync-all
```

**Parâmetros (opcionais, via JSON body):**
```json
{
  "limit": 10,        // Limitar quantidade de produtos
  "only_active": true // Apenas produtos ativos
}
```

**Exemplo:**
```bash
POST https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/produtos/sync-all
Content-Type: application/json

{
  "limit": 5,
  "only_active": true
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Sincronização concluída",
  "total": 5,
  "success": 4,
  "errors": 1,
  "results": [
    {"produto_id": 1, "success": true},
    {"produto_id": 2, "success": false, "error": "NCM obrigatório"}
  ]
}
```

### 3. Verificar Status de Sincronização

```
GET /api/bling/produtos/status/<produto_id>
```

**Exemplo:**
```bash
GET https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/produtos/status/1
```

**Resposta (Sincronizado):**
```json
{
  "synced": true,
  "bling_id": 12345,
  "bling_codigo": "SKU-001",
  "status": "sync",
  "ultima_sincronizacao": "2026-01-09T18:00:00",
  "erro": null
}
```

**Resposta (Não Sincronizado):**
```json
{
  "synced": false,
  "message": "Produto não sincronizado com Bling"
}
```

## ⚙️ Como Funciona

### Mapeamento de Campos

| LhamaBanana | Bling | Observações |
|-------------|-------|-------------|
| `codigo_sku` | `codigo` | **Obrigatório** - SKU único |
| `ncm` | `ncm` | **Obrigatório** - 8 dígitos |
| `preco_venda` / `preco_promocional` | `preco` | Usa promocional se existir |
| `custo` | `precoCusto` | Opcional |
| `estoque` | `estoque.atual` | Quantidade disponível |
| `estoque_minimo` | `estoque.minimo` | Alerta de estoque baixo |
| `nome` (nome_produto) | `nome` | Nome do produto |
| `descricao` | `descricaoComplementar` | Descrição completa |
| `descricao_curta` | `descricaoCurta` | Descrição curta |
| `peso_kg` | `pesoLiq`, `pesoBruto` | Peso em kg |
| `dimensoes_*` | `largura`, `altura`, `profundidade` | Dimensões em cm |
| `codigo_barras` | `gtin` | Código de barras EAN |

### Validações Implementadas

Antes de sincronizar, o sistema valida:
- ✅ NCM obrigatório e com 8 dígitos
- ✅ SKU obrigatório e não vazio
- ✅ Preço maior que zero
- ✅ Nome do produto obrigatório

Se alguma validação falhar, o produto **não será sincronizado** e retornará erro.

### Fluxo de Sincronização

```
1. Buscar produto do banco local
   ↓
2. Validar dados (NCM, SKU, preço, etc.)
   ↓
3. Verificar se já existe no Bling
   ↓
4. Mapear campos para formato Bling
   ↓
5. POST /produtos (criar) OU PUT /produtos/{id} (atualizar)
   ↓
6. Salvar ID do Bling no banco
   ↓
7. Registrar log de sincronização
```

### Rate Limiting

- Delay de 500ms entre requisições (evita limite do Bling)
- A sincronização em lote respeita esse delay automaticamente

## 🔍 Verificações e Logs

### Verificar Logs de Sincronização

```sql
-- Ver últimos logs
SELECT * FROM bling_sync_logs 
WHERE entity_type = 'produto' 
ORDER BY created_at DESC 
LIMIT 20;

-- Ver produtos com erro
SELECT bp.*, p.codigo_sku, p.ncm
FROM bling_produtos bp
JOIN produtos p ON bp.produto_id = p.id
WHERE bp.status_sincronizacao = 'error';
```

### Verificar Produtos Sincronizados

```sql
-- Todos os produtos sincronizados
SELECT 
    p.id,
    p.codigo_sku,
    bp.bling_id,
    bp.status_sincronizacao,
    bp.ultima_sincronizacao
FROM produtos p
JOIN bling_produtos bp ON p.id = bp.produto_id
ORDER BY bp.ultima_sincronizacao DESC;
```

## 🧪 Como Testar

### Teste 1: Sincronizar um produto

1. Certifique-se de que o produto tem:
   - ✅ NCM válido (8 dígitos)
   - ✅ SKU único
   - ✅ Preço > 0

2. Sincronize:
```bash
POST /api/bling/produtos/sync/1
```

3. Verifique status:
```bash
GET /api/bling/produtos/status/1
```

### Teste 2: Sincronizar todos os produtos

```bash
POST /api/bling/produtos/sync-all
Body: {"limit": 5, "only_active": true}
```

### Teste 3: Verificar no Bling

Após sincronizar, verifique no painel do Bling:
- Produtos → Lista de produtos
- O produto deve aparecer com o SKU e NCM configurados

## ⚠️ Importante

### Antes de Sincronizar em Produção

1. **Verificar NCM de todos os produtos**
   - Produtos sem NCM não podem emitir NF-e
   - Execute: `SELECT id, codigo_sku, ncm FROM produtos WHERE ncm IS NULL OR LENGTH(ncm) != 8`

2. **Testar com poucos produtos primeiro**
   - Use `limit` no sync-all para testar

3. **Monitorar logs**
   - Verifique `bling_sync_logs` para erros

4. **Valores monetários**
   - Bling espera valores em reais (não centavos)
   - O sistema já faz a conversão correta

## 🐛 Troubleshooting

### Erro: "NCM obrigatório e deve ter 8 dígitos"

**Solução:**
- Adicione NCM válido ao produto no banco
- NCM deve ter exatamente 8 dígitos (ex: "61091000")

### Erro: "SKU obrigatório"

**Solução:**
- Verifique se o produto tem `codigo_sku` preenchido
- SKU deve ser único

### Erro: "Preço deve ser maior que zero"

**Solução:**
- Verifique `preco_venda` ou `preco_promocional`
- Pelo menos um deve ser > 0

### Erro: Rate Limit (429)

**Solução:**
- O sistema já tem delay de 500ms entre requisições
- Se ainda ocorrer, aumente o delay ou reduza quantidade

### Produto duplicado no Bling

**Solução:**
- Bling pode criar duplicatas se SKU não for único
- Verifique SKUs duplicados no banco local
- Use o endpoint para atualizar produto existente

## 📝 Próximos Passos

Após sincronizar produtos com sucesso:

1. ✅ Testar criação de pedidos no Bling
2. ✅ Implementar emissão de NF-e
3. ✅ Sincronizar estoque
4. ✅ Automação de sincronização (workers)

## 🔗 Links Úteis

- [Documentação API Bling - Produtos](https://developer.bling.com.br/referencia/produtos)
- Teste da API: `GET /api/bling/test`
- Status: `GET /api/bling/status`
- Tokens: `GET /api/bling/tokens`

