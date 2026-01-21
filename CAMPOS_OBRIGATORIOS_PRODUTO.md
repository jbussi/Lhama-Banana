# 📋 Campos Obrigatórios para Criar um Produto

Este documento descreve todos os campos **obrigatórios** e **opcionais** para criar um produto no sistema LhamaBanana.

---

## 🔴 Campos Obrigatórios

### 1. **Nome do Produto** (`nome_produto.nome`)
- **Tipo**: VARCHAR(100)
- **Descrição**: Nome comercial do produto
- **Validação**: Não pode ser vazio
- **Exemplo**: `"Camiseta Básica"`

### 2. **Categoria** (`nome_produto.categoria_id`)
- **Tipo**: INTEGER (FK para `categorias.id`)
- **Descrição**: Categoria à qual o produto pertence
- **Validação**: Deve existir na tabela `categorias`
- **Nota**: O produto precisa estar vinculado a uma categoria existente

### 3. **SKU - Código do Produto** (`produtos.codigo_sku`)
- **Tipo**: VARCHAR(50)
- **Descrição**: Identificador único do produto (Stock Keeping Unit)
- **Validação**: 
  - Não pode ser vazio
  - Deve ser único (UNIQUE constraint)
  - Usado para sincronização com Bling
- **Exemplo**: `"CAM-BAS-M"`

### 4. **NCM - Nomenclatura Comum do Mercosul** (`produtos.ncm`)
- **Tipo**: VARCHAR(8)
- **Descrição**: Classificação fiscal obrigatória para emissão de NF-e
- **Validação**: 
  - **OBRIGATÓRIO** para sincronização com Bling
  - Deve ter **exatamente 8 dígitos**
  - Apenas números
- **Exemplo**: `"61091000"` (Camisetas de algodão)
- **Nota**: Sem NCM, o produto não pode ser sincronizado com Bling

### 5. **Preço de Venda** (`produtos.preco_venda`)
- **Tipo**: DECIMAL(10, 2)
- **Descrição**: Valor de venda do produto
- **Validação**: 
  - Deve ser maior que zero
  - Obrigatório no banco de dados (NOT NULL)
- **Exemplo**: `100.00`

### 6. **Custo** (`produtos.custo`)
- **Tipo**: DECIMAL(10, 2)
- **Descrição**: Custo de aquisição/fabricação do produto
- **Validação**: 
  - Obrigatório no banco (NOT NULL)
  - Pode ser zero, mas é recomendado preencher
- **Exemplo**: `50.00`

### 7. **Estoque** (`produtos.estoque`)
- **Tipo**: INTEGER
- **Descrição**: Quantidade disponível em estoque
- **Validação**: 
  - Obrigatório no banco (NOT NULL)
  - Default: 0
- **Exemplo**: `10`

### 8. **Relacionamentos Obrigatórios**

#### `produtos.nome_produto_id`
- **Tipo**: INTEGER (FK para `nome_produto.id`)
- **Descrição**: Referência ao nome base do produto
- **Validação**: Deve existir na tabela `nome_produto`

#### `produtos.estampa_id`
- **Tipo**: INTEGER (FK para `estampa.id`)
- **Descrição**: Estampa aplicada ao produto
- **Validação**: Deve existir na tabela `estampa`

#### `produtos.tamanho_id`
- **Tipo**: INTEGER (FK para `tamanho.id`)
- **Descrição**: Tamanho do produto
- **Validação**: Deve existir na tabela `tamanho`

**Nota**: A combinação `(nome_produto_id, estampa_id, tamanho_id)` deve ser única.

---

## 🟢 Campos Opcionais (mas Recomendados)

### Da Tabela `nome_produto`:

1. **Descrição** (`descricao`)
   - Tipo: TEXT
   - Descrição completa do produto

2. **Descrição Curta** (`descricao_curta`)
   - Tipo: VARCHAR(255)
   - Descrição resumida para cards e listagens

3. **Peso** (`peso_kg`)
   - Tipo: DECIMAL(8, 3)
   - Peso em quilogramas (para frete)

4. **Dimensões** (`dimensoes_largura`, `dimensoes_altura`, `dimensoes_comprimento`)
   - Tipo: DECIMAL(8, 2)
   - Dimensões em centímetros (para frete)

5. **SEO** (`meta_title`, `meta_description`, `slug`)
   - Para otimização de busca e URLs amigáveis

6. **Destaque** (`destaque`)
   - Tipo: BOOLEAN
   - Marcar produtos em destaque

7. **Ordem de Exibição** (`ordem_exibicao`)
   - Tipo: INTEGER
   - Controla a ordem na listagem

### Da Tabela `produtos`:

1. **Código de Barras** (`codigo_barras`)
   - Tipo: VARCHAR(50)
   - GTIN/EAN para integração com outros sistemas

2. **Estoque Mínimo** (`estoque_minimo`)
   - Tipo: INTEGER
   - Alerta quando estoque está baixo

3. **Ativo** (`ativo`)
   - Tipo: BOOLEAN
   - Default: TRUE
   - Controla se produto está disponível para venda

---

## ❌ Campos Removidos

Os seguintes campos foram **removidos** do sistema:

1. **`preco_promocional`**
   - **Motivo**: Promoções são tratadas como desconto no pedido, não no produto
   - **Alternativa**: Aplicar desconto ao criar o pedido

2. **`estoque_reservado`**
   - **Motivo**: Não utilizado no fluxo atual
   - **Alternativa**: Se necessário, implementar lógica de reserva no futuro

3. **`tags`** (da tabela `nome_produto`)
   - **Motivo**: Não utilizado e não sincronizado com Bling
   - **Alternativa**: Usar categorias ou criar tabela de tags separada se necessário

---

## 📊 Validação para Sincronização com Bling

Para que um produto possa ser sincronizado com o Bling, ele **DEVE** ter:

1. ✅ **NCM válido** (8 dígitos)
2. ✅ **SKU preenchido**
3. ✅ **Preço de venda > 0**
4. ✅ **Nome do produto preenchido**

Se qualquer um desses campos estiver faltando ou inválido, a sincronização **falhará** com erro de validação.

---

## 📝 Exemplo de Produto Completo

```sql
-- 1. Criar nome_produto (se não existir)
INSERT INTO nome_produto (
    nome,
    categoria_id,
    descricao_curta,
    descricao,
    peso_kg,
    dimensoes_largura,
    dimensoes_altura,
    dimensoes_comprimento
) VALUES (
    'Camiseta Básica',
    1,  -- categoria_id (deve existir)
    'Camiseta de algodão 100%',
    'Camiseta básica confortável de algodão 100%...',
    0.200,
    30.0,
    40.0,
    5.0
);

-- 2. Criar produto (variação)
INSERT INTO produtos (
    nome_produto_id,
    estampa_id,      -- deve existir
    tamanho_id,      -- deve existir
    codigo_sku,
    ncm,
    preco_venda,
    custo,
    estoque,
    codigo_barras,
    estoque_minimo,
    ativo
) VALUES (
    1,               -- nome_produto_id (do INSERT acima)
    1,               -- estampa_id (deve existir)
    1,               -- tamanho_id (deve existir)
    'CAM-BAS-M',
    '61091000',      -- NCM obrigatório
    100.00,          -- preco_venda obrigatório
    50.00,           -- custo obrigatório
    10,              -- estoque obrigatório
    '7891234567890', -- opcional
    5,               -- estoque_minimo opcional
    TRUE             -- ativo (default: TRUE)
);
```

---

## 🔄 Sincronização com Bling

Após criar o produto no banco local, você pode sincronizá-lo com o Bling:

```bash
POST /api/bling/produtos/sync/<produto_id>
```

**Pré-requisitos:**
- Produto deve ter NCM válido
- Produto deve ter SKU único
- Produto deve ter preço de venda > 0
- Produto deve ter nome preenchido

---

## 📚 Referências

- **ETAPA_3_PRODUTOS_FISCAL.md**: Documentação completa sobre dados fiscais
- **BLING_SINCRONIZACAO_PRODUTOS.md**: Guia de sincronização com Bling
- **db/schema.sql**: Schema completo do banco de dados
