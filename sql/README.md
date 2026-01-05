# 📁 Scripts SQL - LhamaBanana

Este diretório contém scripts SQL para migrações, correções e atualizações do banco de dados.

## 📋 Arquivos Disponíveis

### `create-metabase-db.sql`
**Propósito**: Criar o banco de dados interno do Metabase.

**Quando usar**: 
- Se o banco `metabase` não existir
- Para configuração inicial do Metabase

**Como executar**:
```bash
docker compose exec -T postgres psql -U postgres < sql/create-metabase-db.sql
```

---

### `fix-strapi-indexes.sql`
**Propósito**: Criar índices faltantes do Strapi para eliminar avisos nos logs.

**Quando usar**: 
- Se você ver erros de índices do Strapi nos logs do PostgreSQL
- ⚠️ **Nota**: Esses erros não são críticos e podem ser ignorados

**Como executar**:
```bash
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < sql/fix-strapi-indexes.sql
```

---

### `atualizar-checkout-pagamentos.sql`
**Propósito**: Atualizar o schema para suportar checkout com PagBank (PIX, Boleto, Cartão).

**Quando usar**: 
- Migração de versão antiga do sistema
- Se campos de frete/desconto não existirem na tabela `vendas`
- Para adicionar suporte completo ao PagBank

**Como executar**:
```bash
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < sql/atualizar-checkout-pagamentos.sql
```

---

### `tabela_etiquetas.sql`
**Propósito**: Criar a tabela `etiquetas_frete` para gerenciar etiquetas do Melhor Envio.

**Quando usar**: 
- Se a tabela `etiquetas_frete` não existir
- Para adicionar suporte completo ao Melhor Envio

**Como executar**:
```bash
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < sql/tabela_etiquetas.sql
```

---

## ⚠️ Importante

- **Sempre faça backup** antes de executar scripts de migração
- **Teste em ambiente de desenvolvimento** primeiro
- **Verifique se o script é idempotente** (pode ser executado múltiplas vezes sem problemas)

## 📚 Schema Principal

O schema completo do banco de dados está em:
- `db/schema.sql` - Schema completo e atualizado

---

**Última atualização**: 2024

