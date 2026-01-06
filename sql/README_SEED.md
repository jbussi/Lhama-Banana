# Scripts SQL para Popular Dados de Exemplo

Este diretório contém scripts SQL para configurar e popular dados de exemplo no banco de dados.

## Scripts Disponíveis

### 1. `add-tecido-field.sql`
Adiciona o campo `tecido` na tabela `estampa` para suportar filtros por tipo de tecido.

**Como executar:**
```bash
docker compose exec postgres psql -U postgres -d sistema_usuarios -f /path/to/add-tecido-field.sql
```

Ou via psql direto:
```bash
psql -U postgres -d sistema_usuarios -f sql/add-tecido-field.sql
```

### 2. `seed-example-data.sql`
Popula o banco de dados com dados de exemplo:
- 4 categorias (Camisetas, Regatas, Moletom, Acessórios)
- 5 tamanhos (P, M, G, GG, XG)
- 8 estampas diferentes com tecidos e sexos variados
- 3 produtos base (Camiseta, Regata, Moletom)
- Múltiplas variações de produtos com estoque

**Como executar:**
```bash
docker compose exec postgres psql -U postgres -d sistema_usuarios -f /path/to/seed-example-data.sql
```

Ou via psql direto:
```bash
psql -U postgres -d sistema_usuarios -f sql/seed-example-data.sql
```

## Ordem de Execução

1. Primeiro execute `add-tecido-field.sql` para adicionar o campo de tecido
2. Depois execute `seed-example-data.sql` para popular os dados

## Dados de Exemplo Incluídos

### Categorias
- Camisetas
- Regatas
- Moletom
- Acessórios

### Estampas (com tecido e sexo)
- Lhama Feliz (Algodão 100%, Unissex)
- Lhama Espacial (Algodão 100%, Masculino)
- Lhama Princesa (Algodão 100%, Feminino)
- Lhama Surfista (Poliéster, Unissex)
- Lhama Rockstar (Algodão 100%, Masculino)
- Lhama Floral (Algodão 100%, Feminino)
- Lhama Minimalista (Algodão com Poliéster, Unissex)
- Lhama Tropical (Poliéster, Unissex)

### Produtos
- Camiseta Básica Lhama (com 5 estampas diferentes)
- Regata Esportiva Lhama (com 2 estampas)
- Moletom Lhama (com 1 estampa)

### Estoque
Cada variação de produto tem estoque configurado (20-50 unidades dependendo do produto).

## Nota sobre Imagens

As imagens das estampas estão configuradas com paths placeholder (`/static/img/estampas/...`). 
Você precisará adicionar as imagens reais nesses caminhos ou atualizar os paths no banco de dados.



