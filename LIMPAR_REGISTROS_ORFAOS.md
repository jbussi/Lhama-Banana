# 🧹 Limpeza de Registros Órfãos do Strapi

## Problema

Alguns registros aparecem no admin do Strapi mas não podem ser deletados, gerando o erro:
```
You're trying to delete a document without an id, this is likely a bug with Strapi.
```

Isso acontece quando:
- O registro foi deletado do banco de dados mas ainda existe no cache/índice do Strapi
- Há inconsistência entre o banco de dados e o índice do Strapi
- Registros específicos: **categorias 31, 32** e **nome_produto 9**

## Solução

### Passo 1: Limpar Referências e Registros do Banco

Execute o script SQL para limpar referências e deletar os registros se ainda existirem:

**Windows PowerShell:**
```powershell
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < sql/limpar-registros-orfaos.sql
```

**Linux/Mac:**
```bash
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < sql/limpar-registros-orfaos.sql
```

Este script irá:
1. ✅ Verificar se os registros existem no banco
2. ✅ Limpar todas as referências (tabelas de link)
3. ✅ Deletar os registros se ainda existirem
4. ✅ Mostrar um resumo do que foi feito

### Passo 2: Limpar Cache do Strapi

Após limpar o banco, limpe o cache do Strapi para remover os registros do índice:

**Windows PowerShell:**
```powershell
.\scripts\limpar-cache-strapi.ps1
```

**Linux/Mac:**
```bash
chmod +x scripts/limpar-cache-strapi.sh
./scripts/limpar-cache-strapi.sh
```

Ou manualmente:
```bash
# Parar o Strapi
docker compose stop strapi

# Limpar cache
docker compose exec strapi sh -c "rm -rf .cache .tmp dist build"

# Reiniciar o Strapi
docker compose up -d strapi
```

### Passo 3: Verificar

1. Aguarde alguns minutos para o Strapi reconstruir o índice
2. Acesse o admin do Strapi
3. Verifique se os registros órfãos desapareceram

## O que o Script SQL Faz

O script `limpar-registros-orfaos.sql` executa:

1. **Verificação**: Verifica se os registros existem no banco
2. **Limpeza de Referências**:
   - Remove entradas das tabelas de link (`estampa_categoria_lnk`, `nome_produto_categoria_lnk`, etc.)
   - Atualiza colunas diretas para `NULL` onde necessário
3. **Deleção**: Remove os registros das tabelas principais se ainda existirem
4. **Relatório**: Mostra o que foi feito

## Registros Afetados

- **Categorias**: IDs 31 e 32
- **Nome Produto**: ID 9

## Prevenção

Para evitar que isso aconteça novamente:

1. ✅ Use sempre o admin do Strapi para deletar registros
2. ✅ Não delete registros diretamente do banco sem atualizar o Strapi
3. ✅ Se deletar do banco, sempre limpe o cache do Strapi depois
4. ✅ Os hooks de lifecycle agora verificam se o registro existe antes de limpar referências

## Troubleshooting

### Se os registros ainda aparecerem após limpar:

1. **Reconstruir o índice do Strapi**:
   ```bash
   docker compose restart strapi
   # Aguarde 2-3 minutos
   ```

2. **Verificar logs do Strapi**:
   ```bash
   docker compose logs strapi --tail 100
   ```

3. **Limpar cache manualmente** (dentro do container):
   ```bash
   docker compose exec strapi sh -c "rm -rf .cache .tmp dist build .strapi"
   docker compose restart strapi
   ```

### Se houver erro ao executar o script SQL:

- Verifique se o container do PostgreSQL está rodando: `docker compose ps`
- Verifique se o nome do banco está correto (padrão: `sistema_usuarios`)
- Verifique os logs: `docker compose logs postgres`

## Notas Técnicas

- O Strapi 5 usa um sistema de `documentId` (UUID) que mapeia para `id` (inteiro)
- Quando há inconsistência, o Strapi pode mostrar registros que não existem mais
- Limpar o cache força o Strapi a reconstruir o índice do zero
- Os hooks de lifecycle agora tratam registros órfãos corretamente

---

**Última atualização**: 2026-01-20
