# Backup do Banco de Dados PostgreSQL

## Arquivos de Backup

Este diretório contém os seguintes arquivos de backup:

1. **`backup_completo.sql`** (3.18 MB)
   - Backup completo do banco de dados `sistema_usuarios`
   - Inclui: schema completo + todos os dados
   - Formato: SQL texto (restaurável com `psql`)
   - Opções usadas: `--clean --if-exists --no-owner --no-acl`

2. **`backup_schema_completo.sql`** (490 KB)
   - Apenas o schema (estrutura) do banco de dados
   - Inclui: tabelas, sequências, índices, triggers, funções, constraints
   - Não inclui dados

3. **`backup_schema.sql`** (490 KB)
   - Versão anterior do schema

## Como Restaurar o Backup Completo

### Opção 1: Restaurar em um banco de dados existente (vai limpar tudo)

```bash
# Conectar ao container PostgreSQL
docker compose exec postgres psql -U postgres -d sistema_usuarios < backup_completo.sql
```

### Opção 2: Criar um novo banco de dados e restaurar

```bash
# 1. Criar novo banco de dados
docker compose exec postgres psql -U postgres -c "CREATE DATABASE sistema_usuarios_restaurado;"

# 2. Restaurar o backup
docker compose exec -T postgres psql -U postgres -d sistema_usuarios_restaurado < backup_completo.sql
```

### Opção 3: Restaurar apenas o schema (sem dados)

```bash
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < backup_schema_completo.sql
```

## Informações do Backup

- **Data do Backup**: 29/01/2026 18:10:26
- **Banco de Dados**: `sistema_usuarios`
- **Usuário**: `postgres`
- **Formato**: SQL texto (compatível com qualquer versão do PostgreSQL)

## Conteúdo do Backup

O backup completo inclui:

- ✅ Todas as tabelas (incluindo tabelas do Strapi)
- ✅ Todas as sequências (auto-increment)
- ✅ Todos os índices
- ✅ Todas as constraints (chaves primárias, estrangeiras, checks)
- ✅ Todas as funções e triggers
- ✅ Todos os dados de todas as tabelas
- ✅ Comandos `DROP` antes de criar (--clean)
- ✅ Comandos `IF EXISTS` para evitar erros (--if-exists)

## Verificação do Backup

Para verificar se o backup está completo, você pode:

```bash
# Verificar o tamanho do arquivo
ls -lh backup_completo.sql

# Verificar as primeiras linhas (deve começar com comandos DROP)
head -20 backup_completo.sql

# Verificar as últimas linhas (deve terminar com comandos de restauração)
tail -20 backup_completo.sql

# Contar quantas tabelas foram incluídas
grep -c "CREATE TABLE" backup_completo.sql
```

## Importante

⚠️ **ATENÇÃO**: O backup usa `--clean --if-exists`, o que significa que ao restaurar:
- Todas as tabelas existentes serão **DROPADAS** (removidas)
- Todas as sequências serão **DROPADAS**
- Todos os objetos serão recriados do zero

Certifique-se de fazer um backup adicional antes de restaurar em produção!

## Restauração em Produção

Para restaurar em produção:

1. **Pare os serviços** que usam o banco de dados:
   ```bash
   docker compose stop flask strapi
   ```

2. **Faça um backup de segurança** do banco atual:
   ```bash
   docker compose exec postgres pg_dump -U postgres -d sistema_usuarios > backup_seguranca_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Restaure o backup**:
   ```bash
   docker compose exec -T postgres psql -U postgres -d sistema_usuarios < backup_completo.sql
   ```

4. **Verifique a restauração**:
   ```bash
   docker compose exec postgres psql -U postgres -d sistema_usuarios -c "\dt"
   ```

5. **Inicie os serviços novamente**:
   ```bash
   docker compose start flask strapi
   ```

## Estrutura do Banco de Dados

O banco de dados contém as seguintes categorias principais de tabelas:

- **Strapi**: Tabelas do CMS (admin_users, strapi_*, files, upload_folders, etc.)
- **Produtos**: produtos, nome_produto, estampa, tamanho, tecidos, categorias, imagens_produto
- **Usuários**: usuarios, enderecos, dados_fiscais
- **Vendas**: vendas, itens_venda, pagamentos, orders
- **Carrinho**: carrinhos, carrinho_itens
- **Cupons**: cupom, cupom_usado
- **Bling**: bling_tokens, bling_produtos, bling_pedidos, bling_situacoes, bling_sync_logs
- **NF-e**: notas_fiscais
- **Avaliações**: avaliacoes
- **Conteúdo do Site**: site_conteudo_*, site_informacoes_empresa, site_politica_*
- **Conteúdo Strapi**: conteudo_*, informacoes_empresa, politica_*

## Suporte

Em caso de problemas na restauração, verifique:

1. Permissões do usuário PostgreSQL
2. Espaço em disco disponível
3. Logs do PostgreSQL: `docker compose logs postgres`
4. Versão do PostgreSQL (deve ser compatível)
