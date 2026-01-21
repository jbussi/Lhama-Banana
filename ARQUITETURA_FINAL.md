# 🏗️ Arquitetura Final: Integração Bling - LhamaBanana

## ✅ Princípios Fundamentais

### Strapi/Admin Local = Fonte da Verdade
- **Criação**: Produtos são criados APENAS localmente
- **Estrutura**: Categorias, estampas, tamanhos, tecidos são criados localmente
- **Preços**: `preco_venda` e `preco_promocional` gerenciados localmente
- **SEO**: Meta tags, descrições, imagens gerenciadas localmente

### Bling = Apenas ERP Operacional/Fiscal
- **Recebe**: Produtos já criados (via API)
- **Gerencia**: Estoque, SKUs, preço fiscal, pedidos, NF-e, financeiro
- **NÃO cria**: Produtos, categorias, estrutura do catálogo

---

## 🔄 Fluxos de Sincronização

### 1. Criar e Enviar Produto para Bling
```
Admin cria produto → Banco Local → POST /api/bling/produtos/sync/<produto_id> → Bling
```

**O que é enviado:**
- SKU (`codigo_sku`)
- Nome completo (montado)
- Preço de venda (`preco_venda`, NÃO promocional)
- NCM (obrigatório)
- Estoque inicial
- Código de barras (se houver)

**O que NÃO é enviado:**
- Preço promocional (gerenciado apenas localmente)
- Categoria, estampa, tamanho (estrutura não é enviada, apenas no nome)

---

### 2. Sincronizar Estoque do Bling → Local
```
Bling (alterado estoque) → POST /api/bling/estoque/sync-from-bling → Banco Local
```

**O que é atualizado:**
- Campo `estoque` no produto local
- Nenhum outro campo é alterado

**Endpoints:**
- `POST /api/bling/estoque/sync-from-bling` - Sincronizar todos os produtos
- `POST /api/bling/estoque/sync-from-bling` (Body: `{"produto_id": 123}`) - Produto específico
- `POST /api/bling/estoque/sync/<produto_id>` - Bidirecional (produto específico)

---

### 3. Sincronizar Estoque Local → Bling
```
Banco Local (alterado estoque) → POST /api/bling/estoque/sync-to-bling → Bling
```

**O que é atualizado:**
- Campo `estoque.atual` no produto do Bling
- Outros campos do produto no Bling são preservados

**Endpoints:**
- `POST /api/bling/estoque/sync-to-bling` - Sincronizar todos os produtos
- `POST /api/bling/estoque/sync-to-bling` (Body: `{"produto_id": 123}`) - Produto específico

---

### 4. Sincronizar Preço do Bling → Local (Opcional)
```
Bling (alterado preço fiscal) → POST /api/bling/produtos/sync-price-from-bling → Banco Local
```

**O que é atualizado:**
- Campo `preco_venda` no produto local
- **NUNCA** atualiza `preco_promocional` (gerenciado apenas localmente)

**Endpoints:**
- `POST /api/bling/produtos/sync-price-from-bling` - Sincronizar todos os produtos
- `POST /api/bling/produtos/sync-price-from-bling` (Body: `{"produto_id": 123}`) - Produto específico

**Quando usar:**
- Se o preço fiscal for alterado no Bling e precisar refletir no sistema local
- Geralmente não é necessário, pois preço é gerenciado localmente

---

## 📡 Endpoints Disponíveis

### ✅ Endpoints Ativos

#### Enviar Produto para Bling
```
POST /api/bling/produtos/sync/<produto_id>
POST /api/bling/produtos/sync-all
```
- Cria ou atualiza produto no Bling
- Usa apenas `preco_venda` (não promocional)

#### Sincronizar Estoque
```
POST /api/bling/estoque/sync-from-bling
POST /api/bling/estoque/sync-to-bling
POST /api/bling/estoque/sync/<produto_id>
POST /api/bling/estoque/consistency
```

#### Sincronizar Preço (Opcional)
```
POST /api/bling/produtos/sync-price-from-bling
```

#### Status de Sincronização
```
GET /api/bling/produtos/status/<produto_id>
```

---

### ❌ Endpoints Desabilitados

```
POST /api/bling/produtos/import          # 410 Gone
POST /api/bling/categorias/sync          # Removido
POST /api/bling/sync-completo            # Removido
GET  /api/bling/valores-unicos           # Removido
```

---

## 💰 Gerenciamento de Preços

### Preço de Venda (`preco_venda`)
- **Enviado para Bling**: ✅ Sim (preço fiscal)
- **Sincronizado do Bling**: ⚠️ Opcional (se permitido)
- **Usado para**: Cálculo fiscal, NF-e

### Preço Promocional (`preco_promocional`)
- **Enviado para Bling**: ❌ Não (gerenciado apenas localmente)
- **Sincronizado do Bling**: ❌ Não
- **Usado para**: Exibição no site, cálculo do carrinho
- **No pedido**: Desconto é aplicado como item no Bling

---

## 🔒 Regras de Negócio

### Criação de Produtos
1. ✅ Produto criado no Strapi/admin
2. ✅ SKU gerado automaticamente
3. ✅ Categoria, estampa, tamanho vinculados localmente
4. ✅ Preço promocional definido (se houver)
5. ✅ Admin aciona: Enviar para Bling
6. ✅ Sistema envia para Bling (apenas `preco_venda`)
7. ✅ Bling retorna `bling_id`
8. ✅ Sistema armazena referência em `bling_produtos`

### Alteração de Estoque
1. ✅ Estoque alterado no Bling → Sincronizar para Local
2. ✅ Estoque alterado localmente → Sincronizar para Bling
3. ✅ Após venda → Estoque atualizado automaticamente

### Alteração de Preço
1. ✅ Preço alterado localmente → Enviar produto novamente para Bling
2. ⚠️ Preço alterado no Bling → Opcional sincronizar para Local (apenas `preco_venda`)

---

## 📊 Estrutura de Dados

### Tabela `produtos` (Local)
```sql
- id
- nome_produto_id (FK)
- estampa_id (FK)
- tamanho_id (FK)
- codigo_sku (UNIQUE)
- preco_venda          ✅ Sincronizado com Bling
- preco_promocional    ❌ NUNCA sincronizado
- estoque              ✅ Sincronizado bidirecional
- ncm
- custo
- ativo
```

### Tabela `bling_produtos` (Referência)
```sql
- produto_id (FK para produtos)
- bling_id (ID do produto no Bling)
- bling_codigo (SKU)
- status_sincronizacao ('sync', 'error', 'pending')
- ultima_sincronizacao
- erro_ultima_sync
```

---

## 🎯 Workflow Completo

### Cenário 1: Novo Produto
1. Admin cria produto no Strapi/admin
2. Preenche: categoria, estampa, tamanho, preços, NCM, SKU
3. Clica "Enviar para Bling"
4. Sistema valida (NCM, SKU obrigatórios)
5. Sistema envia para Bling (apenas `preco_venda`)
6. Bling cria produto e retorna ID
7. Sistema salva referência em `bling_produtos`

### Cenário 2: Venda Realizada
1. Cliente faz pedido no site
2. Estoque local é reduzido
3. Pedido é enviado para Bling
4. Estoque no Bling é atualizado automaticamente
5. (Opcional) Sincronizar estoque de volta para garantir consistência

### Cenário 3: Estoque Alterado no Bling
1. Estoque alterado manualmente no Bling
2. Admin ou sistema aciona sincronização
3. `POST /api/bling/estoque/sync-from-bling`
4. Estoque local é atualizado

---

## ⚙️ Configuração

### Permissões Necessárias no Bling
- Leitura de produtos
- Criação de produtos
- Atualização de produtos
- Leitura de pedidos
- Criação de pedidos
- Emissão de NF-e

### Variáveis de Ambiente
```env
BLING_CLIENT_ID=...
BLING_CLIENT_SECRET=...
BLING_REDIRECT_URI=...
```

---

## 🧪 Testando

### 1. Criar produto localmente e enviar para Bling:
```bash
POST /api/bling/produtos/sync/1
```

### 2. Sincronizar estoque do Bling:
```bash
POST /api/bling/estoque/sync-from-bling
```

### 3. Verificar status:
```bash
GET /api/bling/produtos/status/1
```

---

## ✅ Checklist de Implementação

- [x] Restaurar `preco_promocional` no schema
- [x] Ajustar queries para incluir `preco_promocional`
- [x] Ajustar mapeamento: Local → Bling (usa apenas `preco_venda`)
- [x] Desabilitar importação de produtos do Bling
- [x] Manter sincronização de estoque (bidirecional)
- [x] Adicionar sincronização de preço (opcional, Bling → Local)
- [x] Atualizar endpoints
- [x] Documentar arquitetura

---

## 📝 Próximos Passos

1. Testar criação de produto local → Bling
2. Testar sincronização de estoque
3. Considerar sincronização automática de estoque após vendas
4. Avaliar necessidade de sincronização de preço do Bling
