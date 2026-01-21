# 🔄 Mapeamento de Categorias e Atributos - Bling → Sistema Local

## 📋 Estrutura de Dados

### No Bling:
- **Categorias**: Criadas via interface do Bling (Cadastros > Categorias de Produtos)
  - Categorias podem ter subcategorias
  - Cada produto pode ter uma categoria principal
- **Produtos**: Têm campos `nome`, `codigo`, `categoria`, etc.

### No Sistema Local:
- **categorias**: Tipo de produto (ex: "Camisetas", "Regatas")
- **tecidos**: Material (ex: "Algodão", "Malha")
- **estampas**: Design (ex: "Lhama Básica", "Lhama Feliz")
- **tamanhos**: Tamanho (ex: "P", "M", "G")
- **sexo**: Gênero (m/f/u) - vem da estampa

---

## 🔄 Como Funciona a Sincronização

### 1. Sincronização de Categorias

**Endpoint**: `POST /api/bling/categorias/sync`

**O que faz**:
- Busca produtos do Bling
- Extrai categorias únicas dos produtos
- Cria categorias locais automaticamente se não existirem
- Mapeia nome da categoria do Bling → categoria local

**Nota**: O Bling não tem endpoint específico para listar categorias de produtos. As categorias são extraídas dos próprios produtos.

### 2. Sincronização de Produtos

**Endpoint**: `POST /api/bling/produtos/import`

**O que faz**:
1. Busca produtos do Bling
2. Para cada produto:
   - Extrai categoria do campo `categoria` do produto
   - Cria/mapea categoria local
   - Extrai estampa e tamanho do nome do produto (se possível)
   - Cria/mapea estampa e tamanho local
   - Cria `nome_produto` vinculado à categoria
   - Cria produto (variação) com estampa e tamanho

### 3. Estrutura do Produto no Bling

O produto do Bling pode ter:

```json
{
  "id": 123456,
  "nome": "Camiseta Básica - Lhama - M",
  "codigo": "CAM-BAS-M",
  "categoria": {
    "id": 1,
    "descricao": "Camisetas"
  },
  "preco": 100.00,
  "ncm": "61091000",
  "estoque": {
    "atual": 10,
    "minimo": 5
  }
}
```

Ou:

```json
{
  "id": 123456,
  "nome": "Camiseta Básica",
  "codigo": "CAM-BAS-M",
  "categoria": "Camisetas",
  "preco": 100.00,
  "ncm": "61091000"
}
```

---

## 🔍 Extração de Atributos

### Extração de Categoria

A função `extract_category_from_bling_product()` tenta extrair categoria em ordem:

1. Campo `categoria` (objeto com `id` e `descricao`)
2. Campo `categoriaProduto` (objeto alternativo)
3. Campo `categoria` (string)
4. Extração do nome do produto (primeira parte antes de " - ")

### Extração de Estampa e Tamanho

A função `extract_attributes_from_product_name()` extrai do nome:

**Padrão esperado**: `"Nome - Estampa - Tamanho"` ou `"Categoria - Nome - Estampa - Tamanho"`

**Lógica**:
- Última parte: Tamanho (se curto ≤5 chars ou tem números)
- Penúltima parte: Estampa (se houver 3+ partes)
- Primeiras partes: Nome base

**Exemplos**:
- `"Camiseta - Lhama - M"` → Nome: "Camiseta", Estampa: "Lhama", Tamanho: "M"
- `"Camisetas - Básica - Lhama - P"` → Nome: "Camisetas - Básica", Estampa: "Lhama", Tamanho: "P"
- `"Camiseta - 0-3M"` → Nome: "Camiseta", Estampa: null, Tamanho: "0-3M"

---

## 📝 Campos Criados Automaticamente

Quando sincroniza do Bling:

### Categorias:
- Nome vem do campo `categoria` do produto
- Cria automaticamente se não existir
- Ordem padrão: 0

### Estampas:
- Nome extraído do nome do produto
- Categoria vinculada à categoria do produto
- Imagem URL: placeholder automático
- Custo por metro: 0.00 (pode ser atualizado depois)

### Tamanhos:
- Nome extraído do nome do produto
- Cria automaticamente se não existir
- Ordem padrão: 0

---

## 🧪 Testando

### 1. Ver estrutura de um produto do Bling:
```bash
GET /api/bling/produtos/debug?limit=1
```

### 2. Sincronizar categorias:
```bash
POST /api/bling/categorias/sync
```

### 3. Importar produtos:
```bash
POST /api/bling/produtos/import
Body: {"limit": 10}
```

### 4. Ver categorias locais:
```bash
GET /api/admin/cadastros/categorias
```

---

## ⚠️ Observações Importantes

1. **Categoria obrigatória**: Todo produto precisa de categoria. Se não conseguir extrair, cria categoria "Geral".

2. **Estampa e Tamanho obrigatórios**: Se não conseguir extrair do nome, usa padrões (primeira estampa e primeiro tamanho do banco).

3. **Nomes padronizados**: Para melhor sincronização, use nomes padronizados no Bling:
   ```
   [Nome Base] - [Estampa] - [Tamanho]
   ```

4. **Subcategorias do Bling**: Atualmente, subcategorias são tratadas como categorias separadas. Se você tem "Camisetas > Infantil", serão duas categorias: "Camisetas" e "Infantil".

---

## 🔧 Próximos Passos

1. Criar produtos no Bling com categorias vinculadas
2. Executar sincronização de categorias
3. Executar importação de produtos
4. Verificar produtos criados localmente
5. Ajustar mapeamento se necessário
