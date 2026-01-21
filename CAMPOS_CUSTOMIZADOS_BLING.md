# 🔄 Integração com Campos Customizados do Bling

## 📋 Visão Geral

A integração agora suporta campos customizados criados no Bling para mapear categorias, tecidos, estampas e tamanhos automaticamente para o banco de dados local.

---

## 🎯 Campos Customizados Suportados

O sistema reconhece os seguintes campos customizados no Bling (case-insensitive):

| Campo Customizado no Bling | Mapeia Para | Tabela Local |
|---------------------------|-------------|--------------|
| `Categoria` / `Categorias` / `Tipo` / `TipoProduto` | Categoria | `categorias` |
| `Tecido` / `Tecidos` / `Material` / `MateriaPrima` | Tecido | `tecidos` |
| `Estampa` / `Estampas` / `Design` / `Imagem` | Estampa | `estampa` |
| `Tamanho` / `Tamanhos` / `Size` | Tamanho | `tamanho` |
| `Sexo` / `Genero` / `Gender` | Sexo | `estampa.sexo` (futuro) |

---

## 🔧 Como Funciona

### 1. Estrutura de Dados no Bling

Os campos customizados no Bling são retornados na API como:

```json
{
  "id": 123456,
  "nome": "Camiseta Básica",
  "codigo": "CAM-BAS-M",
  "camposCustomizados": [
    {
      "id": 1,
      "nome": "Categoria",
      "valor": "Camisetas"
    },
    {
      "id": 2,
      "nome": "Tecido",
      "valor": "100% Algodão"
    },
    {
      "id": 3,
      "nome": "Estampa",
      "valor": "Lhama Feliz"
    },
    {
      "id": 4,
      "nome": "Tamanho",
      "valor": "M"
    }
  ]
}
```

### 2. Processo de Sincronização

Ao importar um produto do Bling (`POST /api/bling/produtos/import`):

1. **Extrai campos customizados**: A função `extract_custom_fields_from_bling_product()` busca campos customizados no produto
2. **Mapeia para estrutura local**: Os campos são mapeados para categorias, tecidos, estampas e tamanhos
3. **Cria automaticamente**: Se uma categoria/tecido/estampa/tamanho não existir localmente, é criado automaticamente
4. **Vincula ao produto**: O produto é criado com todas as associações corretas

### 3. Prioridade de Extração

A ordem de prioridade para extrair dados é:

1. **Campos customizados** (prioridade máxima)
   - Categoria → `campos_customizados['categoria']`
   - Tecido → `campos_customizados['tecido']`
   - Estampa → `campos_customizados['estampa']`
   - Tamanho → `campos_customizados['tamanho']`

2. **Campo categoria tradicional** (fallback)
   - Campo `categoria` do produto

3. **Extração do nome** (fallback final)
   - Padrão: "Nome - Estampa - Tamanho"

---

## 🔍 Funções Implementadas

### `extract_custom_fields_from_bling_product(bling_product: Dict) -> Dict`

Extrai e normaliza campos customizados do produto do Bling.

**Retorna**:
```python
{
    'categoria': 'Camisetas',
    'tecido': '100% Algodão',
    'estampa': 'Lhama Feliz',
    'tamanho': 'M',
    'sexo': 'U'
}
```

**Variações de nome reconhecidas**:
- Categoria: `categoria`, `categorias`, `tipo`, `tipoproduto`
- Tecido: `tecido`, `tecidos`, `material`, `materiaprima`
- Estampa: `estampa`, `estampas`, `design`, `imagem`
- Tamanho: `tamanho`, `tamanhos`, `size`
- Sexo: `sexo`, `genero`, `gender`

### `get_or_create_local_tecido(nome_tecido: str) -> Optional[int]`

Cria ou busca tecido local baseado no nome do campo customizado.

### `create_local_product_from_bling(bling_product: Dict) -> Dict`

Função principal atualizada para usar campos customizados com prioridade.

---

## 🧪 Testando

### 1. Ver estrutura de produto com campos customizados:

```bash
GET http://localhost:5000/api/bling/produtos/debug?limit=1
```

**Resposta**:
```json
{
  "success": true,
  "total_products": 1,
  "sample_product": { ... },
  "custom_fields_extracted": {
    "categoria": "Camisetas",
    "tecido": "100% Algodão",
    "estampa": "Lhama Feliz",
    "tamanho": "M"
  },
  "custom_fields_raw": [
    {
      "id": 1,
      "nome": "Categoria",
      "valor": "Camisetas"
    },
    ...
  ]
}
```

### 2. Importar produtos:

```bash
POST http://localhost:5000/api/bling/produtos/import
Body: {"limit": 10}
```

**Resposta**:
```json
{
  "success": true,
  "message": "Importação concluída",
  "total": 10,
  "success_count": 10,
  "results": [
    {
      "success": true,
      "produto_id": 1,
      "bling_id": 123456,
      "action": "create",
      "categoria_id": 1,
      "tecido_id": 1,
      "estampa_id": 1,
      "tamanho_id": 1,
      "campos_customizados_usados": {
        "categoria": "Camisetas",
        "tecido": "100% Algodão",
        "estampa": "Lhama Feliz",
        "tamanho": "M"
      }
    }
  ]
}
```

---

## ⚙️ Configuração no Bling

### Passo a Passo para Criar Campos Customizados:

1. Acesse o Bling: **Configurações** > **Sistema** > **Campos Customizados**
2. Selecione **Produtos** como entidade
3. Crie os seguintes campos (recomendado):

   | Nome do Campo | Tipo | Opções (se lista) |
   |--------------|------|-------------------|
   | Categoria | Lista ou Texto | Camisetas, Regatas, Calças, etc. |
   | Tecido | Lista ou Texto | 100% Algodão, UltraSoft, Soft, etc. |
   | Estampa | Lista ou Texto | Lhama Feliz, Dinossauro Verde, etc. |
   | Tamanho | Lista ou Texto | PP, P, M, G, GG, etc. |

4. Ao criar produtos no Bling, preencha esses campos customizados
5. Execute a sincronização via API

---

## 📝 Observações Importantes

1. **Case-Insensitive**: O sistema reconhece variações de nome (ex: "Categoria", "CATEGORIA", "categoria")

2. **Criação Automática**: Se uma categoria/tecido/estampa/tamanho não existir localmente, será criado automaticamente

3. **Fallback**: Se campos customizados não estiverem preenchidos, o sistema usa:
   - Campo `categoria` tradicional do Bling
   - Extração do nome do produto

4. **Tecidos**: A tabela `tecidos` é opcional. Se não existir, o sistema continua funcionando normalmente (apenas não cria tecidos)

5. **Validação**: Valores vazios, `null`, `None`, `true`, `false` são ignorados

---

## 🔄 Fluxo Completo

```
Bling Produto (com campos customizados)
    ↓
extract_custom_fields_from_bling_product()
    ↓
Mapeamento para estrutura local
    ↓
get_or_create_local_category_from_bling()
get_or_create_local_tecido()
get_or_create_local_estampa()
get_or_create_local_tamanho()
    ↓
Criação/Atualização do produto local
    ↓
Produto sincronizado com todas as associações
```

---

## 🐛 Troubleshooting

### Campos customizados não são reconhecidos

1. Verifique o nome do campo no Bling (deve ser similar aos nomes reconhecidos)
2. Use o endpoint `/api/bling/produtos/debug` para ver os campos brutos retornados
3. Verifique se o campo está preenchido no produto do Bling

### Tecidos não são criados

- Verifique se a tabela `tecidos` existe no banco
- A função retorna `None` silenciosamente se a tabela não existir (comportamento esperado)

### Categoria/Tecido/Estampa/Tamanho duplicado

- O sistema verifica se já existe antes de criar
- Se houver duplicatas, pode ser diferença de maiúsculas/minúsculas ou espaços
