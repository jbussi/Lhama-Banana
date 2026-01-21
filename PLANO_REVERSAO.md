# 🔄 Plano de Reversão e Ajuste Arquitetural

## ✅ O Que Já Foi Feito

1. ✅ **Restaurado `preco_promocional` no schema**
   - Campo adicionado de volta à tabela `produtos`
   - SQL de restauração criado

2. ✅ **Ajustado mapeamento de produtos**
   - `map_product_to_bling_format()` usa apenas `preco_venda` (não promocional)
   - Preço promocional gerenciado localmente

3. ✅ **Ajustado endpoints de API**
   - `produto.py`: restaurado suporte a `preco_promocional`
   - `carrinho.py`: usa preço promocional se disponível
   - `loja.py`: calcula preço mínimo com promoção

---

## 🔧 O Que Precisa Ser Feito

### 1. Remover Lógica de Sincronização Reversa (Bling → Local)

**Funções a remover/desabilitar:**
- `extract_unique_values_from_bling_products()` - ❌ Remover
- `sync_categories_and_values_from_bling()` - ❌ Remover  
- `clear_local_categories_and_values()` - ❌ Remover
- `create_local_product_from_bling()` - ❌ Remover
- `fetch_products_from_bling()` com `include_details=True` - ❌ Remover
- `sync_products_from_bling()` - ⚠️ Ajustar para apenas sincronizar estoque/preço

**Endpoints a remover/ajustar:**
- `POST /api/bling/sync-completo` - ❌ Remover
- `GET /api/bling/valores-unicos` - ❌ Remover
- `POST /api/bling/produtos/import` - ❌ Remover ou ajustar para apenas estoque/preço
- `POST /api/bling/categorias/sync` - ❌ Remover
- `GET /api/bling/categorias` - ⚠️ Manter apenas para debug

### 2. Manter Apenas Sincronização Unidirecional

**Fluxo correto:**
```
Local (Strapi) → Criar Produto → Enviar para Bling → Bling armazena SKU/estoque/preço fiscal
```

**Endpoints a manter:**
- `POST /api/bling/produtos/sync/<produto_id>` - ✅ Enviar produto para Bling
- `POST /api/bling/estoque/sync-from-bling` - ✅ Receber estoque do Bling
- `POST /api/bling/estoque/sync-to-bling` - ✅ Enviar estoque para Bling
- `POST /api/bling/estoque/sync/<produto_id>` - ✅ Sincronizar estoque específico

### 3. Ajustar Sincronização de Preço (opcional)

**Se permitir controle de preço pelo Bling:**
- `POST /api/bling/produtos/sync-price-from-bling` - Sincronizar preço de venda do Bling
- **Importante**: NUNCA sobrescrever `preco_promocional` local

---

## 📝 Arquitetura Final

### Criação de Produtos
```
1. Admin cria produto no Strapi/admin
2. Sistema gera SKU único
3. Produto criado localmente com:
   - Categoria (local)
   - Estampa (local)
   - Tamanho (local)
   - Preço venda
   - Preço promocional (opcional, local)
   - NCM
4. Admin aciona: Enviar para Bling
5. Backend envia para Bling:
   - SKU
   - Nome completo (montado)
   - Preço de venda (NÃO promocional)
   - NCM
   - Estoque inicial
6. Bling cria produto e retorna ID
7. Sistema armazena bling_id no bling_produtos
```

### Sincronização de Estoque
```
1. Estoque alterado no Bling
2. Sistema sincroniza: Bling → Local
3. Atualiza apenas campo `estoque` no produto local
```

### Sincronização de Preço (opcional)
```
1. Preço alterado no Bling (se permitido)
2. Sistema sincroniza: Bling → Local
3. Atualiza apenas `preco_venda` (NUNCA `preco_promocional`)
```

---

## 🗑️ Arquivos/Scripts a Remover

- `test_sync_categorias_produtos.ps1` - ❌ Remover
- `test_sync_completo.ps1` - ❌ Remover
- `test_campos_customizados.ps1` - ❌ Remover
- `test_debug_produto_completo.ps1` - ❌ Remover
- `CAMPOS_CUSTOMIZADOS_BLING.md` - ❌ Remover ou arquivar
- `MAPEAMENTO_CATEGORIAS_BLING.md` - ❌ Remover ou arquivar
- `TESTE_CAMPOS_CUSTOMIZADOS.md` - ❌ Remover

---

## 📚 Arquivos a Manter/Atualizar

- ✅ `ARQUITETURA_BLING.md` - Documentação da arquitetura correta
- ✅ `ETAPA_3_PRODUTOS_FISCAL.md` - Manter, atualizar se necessário
- ✅ Scripts de teste de envio para Bling

---

## 🔄 Próximos Passos

1. Executar SQL para restaurar `preco_promocional`
2. Remover funções de sincronização reversa
3. Ajustar endpoints
4. Testar criação de produto Local → Bling
5. Testar sincronização de estoque Bling → Local
6. Considerar controle de preço pelo Bling (futuro)
