# 🔄 Fluxo de Criação de Produtos

Este documento explica o fluxo completo para criar produtos no sistema LhamaBanana.

---

## 📋 Ordem de Criação

Para criar um produto, você precisa seguir esta ordem (cada item depende dos anteriores):

```
1. Categorias
   ↓
2. Tecidos (opcional, mas recomendado)
   ↓
3. Tamanhos
   ↓
4. Estampas (precisa de categoria, tecido é opcional)
   ↓
5. Nome do Produto (precisa de categoria)
   ↓
6. Produto/Variação (precisa de nome_produto, estampa e tamanho)
```

---

## 🔧 Passo 1: Criar Categorias

**Endpoint**: `POST /api/admin/cadastros/categorias`

**Exemplo:**
```json
{
  "nome": "Infantil",
  "descricao": "Produtos para crianças",
  "ordem_exibicao": 1,
  "ativo": true,
  "imagem_url": "https://exemplo.com/categoria-infantil.jpg"
}
```

**Campos obrigatórios:**
- `nome` (string, único)

**Campos opcionais:**
- `descricao` (text)
- `ordem_exibicao` (integer, default: 0)
- `ativo` (boolean, default: true)
- `imagem_url` (string)

---

## 🔧 Passo 2: Criar Tecidos (Opcional)

**Endpoint**: `POST /api/admin/cadastros/tecidos`

**Exemplo:**
```json
{
  "nome": "Algodão",
  "descricao": "Algodão 100%",
  "ordem_exibicao": 1,
  "ativo": true
}
```

**Campos obrigatórios:**
- `nome` (string, único)

**Campos opcionais:**
- `descricao` (text)
- `ordem_exibicao` (integer, default: 0)
- `ativo` (boolean, default: true)

---

## 🔧 Passo 3: Criar Tamanhos

**Endpoint**: `POST /api/admin/cadastros/tamanhos`

**Exemplo:**
```json
{
  "nome": "M",
  "ordem_exibicao": 2,
  "ativo": true
}
```

**Campos obrigatórios:**
- `nome` (string, único, até 20 caracteres)

**Campos opcionais:**
- `ordem_exibicao` (integer, default: 0)
- `ativo` (boolean, default: true)

**Tamanhos comuns:**
- Para bebês: `RN`, `0-3M`, `3-6M`, `6-12M`, `12-24M`
- Para crianças: `P`, `M`, `G`, `GG`
- Unissex: `Único`

---

## 🔧 Passo 4: Criar Estampas

**Endpoint**: `POST /api/admin/cadastros/estampas`

**Exemplo:**
```json
{
  "nome": "Lhama Básica",
  "descricao": "Estampa de lhama estilizada",
  "imagem_url": "https://exemplo.com/estampa-lhama.jpg",
  "categoria_id": 1,
  "tecido_id": 1,
  "sexo": "u",
  "custo_por_metro": 5.50,
  "ordem_exibicao": 1,
  "ativo": true
}
```

**Campos obrigatórios:**
- `nome` (string, único)
- `categoria_id` (integer, deve existir na tabela `categorias`)
- `imagem_url` (string, URL da imagem da estampa)
- `custo_por_metro` (decimal, >= 0)

**Campos opcionais:**
- `descricao` (text)
- `tecido_id` (integer, deve existir na tabela `tecidos` se informado)
- `sexo` (enum: `'m'`, `'f'`, `'u'`, default: `'u'`)
- `ordem_exibicao` (integer, default: 0)
- `ativo` (boolean, default: true)

**Nota**: A estampa precisa estar vinculada a uma categoria. O tecido é opcional.

---

## 🔧 Passo 5: Criar Nome do Produto

**Endpoint**: (Ainda não existe, criar direto no banco ou via script)

**SQL Exemplo:**
```sql
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
```

**Campos obrigatórios:**
- `nome` (string, único, até 100 caracteres)
- `categoria_id` (integer, FK para `categorias.id`)

**Campos opcionais:**
- `descricao` (text)
- `descricao_curta` (varchar 255)
- `peso_kg` (decimal, default: 0)
- `dimensoes_largura`, `dimensoes_altura`, `dimensoes_comprimento` (decimal, default: 0)
- `ativo` (boolean, default: true)
- `destaque` (boolean, default: false)
- `ordem_exibicao` (integer, default: 0)
- `meta_title`, `meta_description` (SEO)
- `slug` (string, único)

---

## 🔧 Passo 6: Criar Produto/Variação

**Endpoint**: (Ainda não existe, criar direto no banco ou importar do Bling)

**SQL Exemplo:**
```sql
INSERT INTO produtos (
    nome_produto_id,
    estampa_id,
    tamanho_id,
    codigo_sku,
    ncm,
    preco_venda,
    custo,
    estoque,
    codigo_barras,
    estoque_minimo,
    ativo
) VALUES (
    1,               -- nome_produto_id (do passo 5)
    1,               -- estampa_id (do passo 4)
    1,               -- tamanho_id (do passo 3)
    'CAM-BAS-M',
    '61091000',      -- NCM obrigatório (8 dígitos)
    100.00,          -- preco_venda obrigatório
    50.00,           -- custo obrigatório
    10,              -- estoque obrigatório
    '7891234567890', -- opcional
    5,               -- estoque_minimo opcional
    TRUE
);
```

**Campos obrigatórios:**
- `nome_produto_id` (integer, FK)
- `estampa_id` (integer, FK)
- `tamanho_id` (integer, FK)
- `codigo_sku` (string, único)
- `ncm` (string, 8 dígitos) - **obrigatório para Bling**
- `preco_venda` (decimal, > 0)
- `custo` (decimal)
- `estoque` (integer)

**Campos opcionais:**
- `codigo_barras` (string)
- `estoque_minimo` (integer, default: 0)
- `ativo` (boolean, default: true)

---

## 🚀 Script Rápido: Criar Dados Base

Execute o script para criar dados básicos:

```bash
python scripts/criar_dados_base.py
```

Este script cria:
- 3 categorias básicas (Bebê, Infantil, Adulto)
- 3 tecidos básicos (Algodão, Malha, Misto)
- 10 tamanhos básicos (RN, P, M, G, GG, 0-3M, 3-6M, 6-12M, 12-24M, Único)
- 2 estampas básicas (Sem Estampa, Lhama Básica)

---

## 📡 Endpoints Disponíveis

### Listar dados:

- `GET /api/admin/cadastros/categorias` - Lista todas as categorias
- `GET /api/admin/cadastros/tecidos` - Lista todos os tecidos
- `GET /api/admin/cadastros/tamanhos` - Lista todos os tamanhos
- `GET /api/admin/cadastros/estampas` - Lista todas as estampas

### Criar dados:

- `POST /api/admin/cadastros/categorias` - Cria categoria
- `POST /api/admin/cadastros/tecidos` - Cria tecido
- `POST /api/admin/cadastros/tamanhos` - Cria tamanho
- `POST /api/admin/cadastros/estampas` - Cria estampa

---

## 🔄 Fluxo Completo de Exemplo

```bash
# 1. Criar categoria
curl -X POST http://localhost:5000/api/admin/cadastros/categorias \
  -H "Content-Type: application/json" \
  -d '{"nome": "Infantil", "descricao": "Produtos para crianças"}'

# 2. Criar tecido
curl -X POST http://localhost:5000/api/admin/cadastros/tecidos \
  -H "Content-Type: application/json" \
  -d '{"nome": "Algodão", "descricao": "Algodão 100%"}'

# 3. Criar tamanho
curl -X POST http://localhost:5000/api/admin/cadastros/tamanhos \
  -H "Content-Type: application/json" \
  -d '{"nome": "M", "ordem_exibicao": 2}'

# 4. Criar estampa
curl -X POST http://localhost:5000/api/admin/cadastros/estampas \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Lhama Básica",
    "imagem_url": "https://exemplo.com/estampa.jpg",
    "categoria_id": 1,
    "tecido_id": 1,
    "custo_por_metro": 5.50
  }'

# 5. Criar nome_produto (via SQL ou script)
# 6. Criar produto (via SQL, script ou importar do Bling)
# 7. Sincronizar com Bling (POST /api/bling/produtos/sync/<produto_id>)
```

---

## 📚 Referências

- **CAMPOS_OBRIGATORIOS_PRODUTO.md**: Campos obrigatórios detalhados
- **BLING_SINCRONIZACAO_PRODUTOS.md**: Como sincronizar com Bling
- **scripts/criar_dados_base.py**: Script para criar dados iniciais
