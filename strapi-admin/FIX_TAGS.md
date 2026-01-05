# Correção do Campo Tags

## Problema

O Strapi estava tentando sincronizar o campo `tags` da tabela `nome_produto`, mas havia um conflito de tipos:

- **Banco de dados**: `tags TEXT[]` (array de texto do PostgreSQL)
- **Strapi**: tentava usar `json` (que mapeia para JSONB)

O PostgreSQL não consegue fazer cast direto de `TEXT[]` para `JSONB`, causando o erro:
```
cannot cast type text[] to jsonb
```

## Solução Aplicada

O campo `tags` foi **removido do schema do Strapi** (`src/api/nome-produto/content-types/nome-produto/schema.json`).

### Por quê?

1. O Strapi 5 não tem suporte nativo para arrays de strings em Content Types simples
2. O campo `tags` não é essencial para o funcionamento do painel administrativo
3. O campo continua existindo no banco de dados e pode ser usado pelo Flask/backend
4. Evita conflitos de sincronização

### Alternativas (se necessário no futuro)

Se precisar editar tags pelo Strapi no futuro, você pode:

1. **Opção 1**: Converter o tipo no banco de dados para JSONB
   ```sql
   ALTER TABLE nome_produto ALTER COLUMN tags TYPE jsonb USING tags::text::jsonb;
   ```
   E então usar `"type": "json"` no schema do Strapi.

2. **Opção 2**: Usar um campo de texto simples separado por vírgulas
   ```json
   "tags": {
     "type": "text"
   }
   ```
   E converter no backend quando necessário.

3. **Opção 3**: Criar uma tabela separada de tags (normalização)

## Status

✅ **Corrigido**: O campo `tags` foi removido do schema do Strapi
✅ **Banco de dados**: O campo continua existindo e funcionando no backend Flask
✅ **Strapi**: Agora deve iniciar sem erros de sincronização

## Próximos Passos

1. Reiniciar o Strapi:
   ```bash
   docker compose restart strapi
   ```

2. Verificar se o erro foi resolvido:
   ```bash
   docker compose logs strapi --tail 50
   ```

3. Se o erro persistir, verificar outros campos que possam ter problemas similares.


