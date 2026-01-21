# ETAPA 3 - Cadastro e Sincronização de Produtos (Dados Fiscais)

## 📋 Modelo Fiscal de Produto

### Campos Fiscais do Produto (LhamaBanana → Bling)

#### **Campos Obrigatórios:**
1. **NCM (Nomenclatura Comum do Mercosul)**
   - 8 dígitos obrigatórios
   - Identifica a classificação fiscal do produto
   - Exemplo: `61091000` (Camisetas de algodão)
   - **Validação**: Deve ter exatamente 8 dígitos numéricos

2. **SKU (Código do Produto)**
   - Identificador único do produto no sistema
   - Usado para sincronização e rastreamento

3. **Nome do Produto**
   - Descrição comercial do produto

4. **Preço de Venda**
   - Valor deve ser maior que zero

#### **Campos Opcionais (Fiscais):**

1. **CEST (Código Especificador da Substituição Tributária)**
   - 7 dígitos
   - Obrigatório apenas para produtos com substituição tributária
   - Exemplo: `0300600` (Roupas íntimas)
   - **Quando usar**: Produtos sujeitos a ST (Substituição Tributária)
   - **Nota**: Não está no banco atual, será adicionado se necessário

2. **Peso (kg)**
   - Peso líquido e bruto
   - Usado para cálculo de frete e fiscal

3. **Dimensões (cm)**
   - Largura, Altura, Comprimento
   - Usado para cálculo de frete

4. **Código de Barras (GTIN)**
   - EAN/UPC
   - Facilita integração com outros sistemas

5. **Preço de Custo**
   - Usado para cálculo de margem

### ❌ Campos que NÃO são do Produto (mas do Pedido/NF):

1. **CFOP (Código Fiscal de Operações e Prestações)**
   - **Não é atributo do produto**
   - **É atributo do pedido/nota fiscal**
   - Depende da natureza da transação:
     - Operação **dentro do mesmo estado**: CFOP 5102 (Venda dentro do estado)
     - Operação **interestadual**: CFOP 6108 (Venda interestadual)
     - **Entrada**: CFOP 1102 (Compra dentro do estado), 2102 (Compra interestadual)
   - **Será tratado na ETAPA 6/7** (Criação de Pedidos e Emissão de NF-e)

## 🔄 Mapeamento de Campos

### LhamaBanana → Bling

| Campo LhamaBanana | Campo Bling | Obrigatório | Tipo | Observações |
|-------------------|-------------|-------------|------|-------------|
| `ncm` | `ncm` | ✅ Sim | String (8) | Validação: 8 dígitos |
| `codigo_sku` | `codigo` | ✅ Sim | String | SKU único |
| `nome` + estampa + tamanho | `nome` | ✅ Sim | String | Nome completo montado |
| `preco_venda` ou `preco_promocional` | `preco` | ✅ Sim | Decimal | Prioridade: promocional > venda |
| `custo` | `precoCusto` | ❌ Não | Decimal | Opcional |
| `estoque` | `estoque.atual` | ❌ Não | Integer | Sincronização bidirecional |
| `estoque_minimo` | `estoque.minimo` | ❌ Não | Integer | Alerta de estoque |
| `peso_kg` | `pesoLiq`, `pesoBruto` | ❌ Não | Decimal | Mesmo valor se não tiver separado |
| `dimensoes_largura` | `largura` | ❌ Não | Decimal | em cm |
| `dimensoes_altura` | `altura` | ❌ Não | Decimal | em cm |
| `dimensoes_comprimento` | `profundidade` | ❌ Não | Decimal | em cm |
| `codigo_barras` | `gtin` | ❌ Não | String | EAN/UPC |
| `descricao_curta` | `descricaoCurta` | ❌ Não | String | Até 255 caracteres |
| `descricao` | `descricaoComplementar` | ❌ Não | Text | Descrição completa |
| `ativo` | `situacao` | ✅ Sim | Enum | "A"=Ativo, "I"=Inativo |
| - | `tipo` | ✅ Sim | Enum | "P"=Produto (fixo) |
| - | `formato` | ✅ Sim | Enum | "S"=Simples (fixo) |
| - | `unidade` | ✅ Sim | String | "UN"=Unidade (fixo) |

### Bling → LhamaBanana (Importação)

| Campo Bling | Campo LhamaBanana | Observações |
|-------------|-------------------|-------------|
| `id` | `bling_id` (tabela `bling_produtos`) | ID no Bling |
| `codigo` | `codigo_sku` | SKU |
| `nome` | Criar novo `nome_produto` ou mapear | Pode precisar parsing |
| `preco` | `preco_venda` | Preço atual no Bling |
| `precoCusto` | `custo` | Se disponível |
| `estoque.atual` | `estoque` | Atualizar estoque |
| `ncm` | `ncm` | NCM do produto |
| `situacao` | `ativo` | "A"=True, "I"=False |

## ✅ Validações Fiscais

### Antes de Enviar para Bling:

```python
# Validação de NCM
ncm = produto.get('ncm')
if not ncm or len(str(ncm)) != 8:
    errors.append("NCM obrigatório e deve ter 8 dígitos")

# Validação de Preço
preco = produto.get('preco_venda') or produto.get('preco_promocional')
if not preco or float(preco) <= 0:
    errors.append("Preço de venda deve ser maior que zero")

# Validação de SKU
if not produto.get('codigo_sku'):
    errors.append("SKU obrigatório")
```

### Validações Adicionais (Futuras):

- **CEST**: Se produto sujeito a ST, validar 7 dígitos
- **NCM válido**: Consultar tabela NCM da Receita Federal
- **Peso**: Se informado, deve ser > 0
- **Dimensões**: Se informadas, devem ser > 0

## 🔧 Estrutura de Dados

### Formato de Envio para Bling API:

```json
{
  "nome": "Camiseta Básica - Estampa X - Tamanho M",
  "codigo": "CAM-X-M",
  "preco": 49.90,
  "precoCusto": 25.00,
  "tipo": "P",
  "formato": "S",
  "unidade": "UN",
  "ncm": "61091000",
  "situacao": "A",
  "estoque": {
    "minimo": 10,
    "maximo": 0,
    "atual": 50
  },
  "pesoLiq": 0.200,
  "pesoBruto": 0.250,
  "largura": 30.0,
  "altura": 40.0,
  "profundidade": 5.0,
  "gtin": "7891234567890",
  "descricaoCurta": "Camiseta básica algodão",
  "descricaoComplementar": "Camiseta de algodão 100%..."
}
```

## 📊 Tabela de Sincronização

A tabela `bling_produtos` armazena o vínculo entre produto local e Bling:

```sql
CREATE TABLE bling_produtos (
    id SERIAL PRIMARY KEY,
    produto_id INTEGER REFERENCES produtos(id) UNIQUE NOT NULL,
    bling_id BIGINT NOT NULL,
    bling_codigo VARCHAR(50) NOT NULL,  -- SKU no Bling
    ultima_sincronizacao TIMESTAMP DEFAULT NOW(),
    status_sincronizacao VARCHAR(20) DEFAULT 'sync',
    erro_ultima_sync TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🎯 Fluxo de Sincronização

### LhamaBanana → Bling:

1. **Buscar produto** do banco local
2. **Validar dados fiscais** (NCM, preço, SKU)
3. **Verificar se já sincronizado** (tabela `bling_produtos`)
   - Se SIM: Atualizar produto no Bling (PUT)
   - Se NÃO: Criar produto no Bling (POST)
4. **Salvar referência** (ID do Bling) na tabela `bling_produtos`
5. **Logar sincronização** (sucesso/erro)

### Bling → LhamaBanana (Importação):

1. **Buscar produtos** do Bling (paginação)
2. **Para cada produto**:
   - Se já existe (`bling_produtos` com `bling_id`): Atualizar
   - Se não existe: Criar novo produto local
3. **Atualizar estoque** se necessário
4. **Logar importação**

## ⚠️ Armadilhas Comuns

### 1. **NCM Inválido**
- **Problema**: NCM com menos/mais de 8 dígitos
- **Solução**: Validação obrigatória antes de enviar
- **Impacto**: Bling rejeita produto

### 2. **SKU Duplicado**
- **Problema**: Produto com mesmo SKU já existe no Bling
- **Solução**: Verificar antes de criar, usar PUT para atualizar
- **Idempotência**: Usar SKU como chave única

### 3. **Variantes (Estampa/Tamanho)**
- **Problema**: Mesmo produto com diferentes variações
- **Solução**: SKU único para cada variação (ex: `CAM-X-M`, `CAM-X-G`)
- **Nome completo**: Incluir estampa e tamanho no nome

### 4. **Situação (Ativo/Inativo)**
- **Problema**: Campo obrigatório no Bling, mas formato diferente
- **Solução**: Mapear `ativo=True` → `situacao="A"`, `ativo=False` → `situacao="I"`

### 5. **CEST para ST**
- **Problema**: Produtos com substituição tributária precisam de CEST
- **Solução**: Validar CEST apenas se produto sujeito a ST
- **Nota**: CEST não está no banco atual (adicionar se necessário)

## 🔐 Idempotência

- **Chave única**: SKU (`codigo`)
- **Criação**: Verificar se SKU existe antes de POST
- **Atualização**: Usar PUT com ID do Bling
- **Logs**: Registrar todas as operações para auditoria

## 📝 Próximos Passos

Após validar sincronização de produtos:
- **ETAPA 4**: Estoque (sincronização bidirecional)
- **ETAPA 5**: Clientes (criação automática)
- **ETAPA 6**: Pedidos (com CFOP no momento da criação)
- **ETAPA 7**: NF-e (com CFOP baseado na natureza da operação)


