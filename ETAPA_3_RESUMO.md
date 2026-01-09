# ETAPA 3 - Cadastro e Sincronização de Produtos (RESUMO EXECUTIVO)

## ✅ Status: Implementação Atual Revisada e Documentada

### 📋 Campos Fiscais do Produto (Confirmado)

#### Obrigatórios:
- ✅ **NCM** (8 dígitos) - Obrigatório
- ✅ **SKU** - Obrigatório  
- ✅ **Nome** - Obrigatório
- ✅ **Preço** - Obrigatório (> 0)

#### Opcionais:
- ⚪ **CEST** (7 dígitos) - Apenas para produtos com ST
- ⚪ **Peso** (kg) - Para frete e fiscal
- ⚪ **Dimensões** (cm) - Para frete
- ⚪ **Código de Barras** (GTIN/EAN) - Facilita integração

### ❌ CFOP NÃO é do Produto

**IMPORTANTE**: CFOP (Código Fiscal de Operações e Prestações) é atributo do **pedido/nota fiscal**, não do produto.

**Motivo**: CFOP depende da natureza da transação:
- **Operação dentro do mesmo estado**: CFOP 5102
- **Operação interestadual**: CFOP 6108
- **Compra**: CFOP 1102 (mesmo estado) ou 2102 (interestadual)

**Onde será tratado**:
- **ETAPA 6**: Criação de Pedidos (definir CFOP baseado em origem/destino)
- **ETAPA 7**: Emissão de NF-e (confirmar CFOP conforme operação)

## 🔄 Mapeamento Atual (LhamaBanana → Bling)

| Campo Local | Campo Bling | Status |
|-------------|-------------|--------|
| `ncm` | `ncm` | ✅ Implementado |
| `codigo_sku` | `codigo` | ✅ Implementado |
| `nome` + estampa + tamanho | `nome` | ✅ Implementado |
| `preco_venda/promocional` | `preco` | ✅ Implementado |
| `custo` | `precoCusto` | ✅ Implementado |
| `estoque` | `estoque.atual` | ✅ Implementado |
| `estoque_minimo` | `estoque.minimo` | ✅ Implementado |
| `peso_kg` | `pesoLiq`, `pesoBruto` | ✅ Implementado |
| `dimensoes_*` | `largura`, `altura`, `profundidade` | ✅ Implementado |
| `codigo_barras` | `gtin` | ✅ Implementado |
| `ativo` | `situacao` | ✅ Implementado |
| `cest` | `cest` | ⚪ Comentado (não existe no banco ainda) |

## ✅ Validações Implementadas

1. **NCM**: 8 dígitos obrigatórios, apenas números
2. **SKU**: Obrigatório
3. **Preço**: Obrigatório, > 0
4. **Nome**: Obrigatório

## 📝 Próximas Ações

1. ✅ **Correção aplicada**: Comentários sobre CFOP adicionados no código
2. ✅ **Documentação criada**: `ETAPA_3_PRODUTOS_FISCAL.md` com detalhes completos
3. ⚪ **Opcional**: Adicionar campo `cest` no banco se necessário para produtos com ST

## 🎯 Como Testar

```powershell
# Sincronizar produto específico
POST /api/bling/produtos/sync/{produto_id}

# Sincronizar todos os produtos
POST /api/bling/produtos/sync-all

# Verificar status de sincronização
GET /api/bling/produtos/status/{produto_id}
```

**Validações esperadas**:
- Produtos sem NCM serão rejeitados
- Produtos sem SKU serão rejeitados
- Produtos com preço inválido serão rejeitados

## ⚠️ Armadilhas Evitadas

1. ✅ **CFOP no produto**: Corrigido - CFOP é do pedido/NF
2. ✅ **NCM inválido**: Validação implementada (8 dígitos)
3. ✅ **SKU duplicado**: Verificação antes de criar (idempotência)
4. ✅ **Situação obrigatória**: Mapeamento `ativo` → `situacao` implementado

