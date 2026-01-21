# 🏗️ Arquitetura: Integração Bling - Fonte da Verdade

## 📋 Princípios Fundamentais

### ✅ Strapi + Banco Próprio = Fonte da Verdade do Catálogo
- **Produtos conceituais**: nome, descrição, categoria, variações
- **Estampas**: imagens, nomes, categorias
- **Atributos visuais**: imagens de produtos, SEO
- **Variações lógicas**: tamanhos, estampas, combinações
- **Preços promocionais**: gerenciados localmente

### ⚠️ Bling = Apenas ERP Operacional/Fiscal
- **Estoque**: quantidades disponíveis
- **SKUs**: códigos únicos (recebidos do sistema)
- **Preços fiscais**: apenas `preco_venda` (NÃO preço promocional)
- **Pedidos**: recebimento e processamento
- **Notas fiscais**: emissão e controle
- **Financeiro**: contas a receber, pagamentos

---

## 🔄 Fluxo de Dados

### 1. Criação de Produtos
```
Strapi/Admin → Banco Local → Envia SKU para Bling
```
- Produtos são criados **somente** no sistema local (Strapi/admin)
- Cada produto/variação gera SKU único
- Backend envia SKU + dados fiscais para o Bling via API
- **Bling NÃO cria nem altera estrutura de produto**

### 2. Sincronização de Estoque e Preços
```
Bling → Backend → Banco Local → Site
```
- Estoque no Bling é sincronizado para o banco local
- Preço de venda do Bling é sincronizado (opcional)
- **Preço promocional permanece apenas local**

### 3. Pedidos
```
Site → Backend → Cria Pedido no Bling → Atualiza Estoque
```
- Pedidos criados localmente são enviados para o Bling
- Bling processa pagamento e atualiza estoque
- Estoque atualizado é sincronizado de volta

---

## 📊 Campos de Produto

### Campos Gerenciados Localmente (Strapi)
- `nome` (nome_produto)
- `categoria_id`
- `estampa_id`
- `tamanho_id`
- `preco_promocional` ✅ **Restaurado**
- `custo`
- `descricao`, `descricao_curta`
- `imagens`
- `SEO` (meta_title, meta_description, slug)

### Campos Sincronizados com Bling
- `codigo_sku` → Bling `codigo` (enviado)
- `preco_venda` → Bling `preco` (bidirecional)
- `ncm` → Bling `ncm` (enviado)
- `estoque` ← Bling `estoque.atual` (recebido)
- `codigo_barras` → Bling `gtin` (enviado)

### Campos Apenas no Bling
- Preço fiscal de venda (não inclui promoções)
- Dados fiscais adicionais (CEST, CFOP por produto)

---

## 🔒 Regras Arquiteturais

### ❌ NÃO Fazer
1. **NÃO criar produtos no Bling** e importar
2. **NÃO criar categorias/estampas/tamanhos** baseado no Bling
3. **NÃO usar campos customizados do Bling** para estrutura do catálogo
4. **NÃO enviar preço promocional** para o Bling
5. **NÃO modificar estrutura de produto** baseado no Bling

### ✅ Fazer
1. **Produtos criados no Strapi/admin** localmente
2. **SKUs enviados para o Bling** após criação
3. **Estoque sincronizado** do Bling para local
4. **Preço de venda sincronizado** (se necessário)
5. **Pedidos enviados** para o Bling
6. **NF-e emitida** via Bling

---

## 🔄 Endpoints de Integração

### Enviar Produto para Bling
```
POST /api/bling/produtos/sync/<produto_id>
```
- Cria/atualiza produto no Bling
- Usa apenas `preco_venda` (não promocional)
- Envia SKU, NCM, preço fiscal

### Sincronizar Estoque do Bling
```
POST /api/bling/estoque/sync-from-bling
```
- Busca estoque atual do Bling
- Atualiza `estoque` no banco local
- Não altera outros campos

### Sincronizar Preço do Bling (opcional)
```
POST /api/bling/produtos/sync-price-from-bling
```
- Busca preço de venda do Bling
- Atualiza `preco_venda` local
- **NÃO altera** `preco_promocional`

---

## 💰 Gerenciamento de Preços

### Preço Promocional (Local)
- Gerenciado **somente** no Strapi/admin
- Usado para exibição no site
- **NÃO** enviado para o Bling
- Aplicado no cálculo do carrinho/pedido

### Preço de Venda (Bling)
- Enviado para o Bling como "preço fiscal"
- Pode ser sincronizado de volta (se alterado no Bling)
- Usado para emissão de NF-e
- Base para cálculos fiscais

### Preço no Pedido
- Pedido usa `preco_promocional` se disponível
- Se não, usa `preco_venda`
- Desconto calculado e aplicado como item no Bling
- NF-e emitida com preço fiscal correto

---

## 🎯 Próximos Passos

1. ✅ Restaurar `preco_promocional` no schema
2. ✅ Remover lógica de criar categorias/valores do Bling
3. ✅ Ajustar mapeamento: Local → Bling (unidirecional)
4. ✅ Manter sincronização: Bling → Local (estoque/preço)
5. ⏳ Implementar controle de preço pelo Bling (opcional)
