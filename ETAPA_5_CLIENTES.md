# ETAPA 5 - Gerenciamento de Clientes/Contatos

## ✅ O Que Foi Implementado

### 1. **Criação Automática de Clientes no Bling**

#### Validação de Dados Fiscais
- **CPF/CNPJ**: Validação completa (dígitos verificadores)
- **Nome/Razão Social**: Obrigatório
- **Endereço Completo**: Rua, número, bairro, cidade, UF, CEP
- **Inscrição Estadual**: Obrigatória para CNPJ
- **CEP**: Validação (8 dígitos)

#### Mapeamento de Dados
- **Tipo de Pessoa**: Automático baseado em CPF (11 dígitos) ou CNPJ (14 dígitos)
- **Contribuinte ICMS**: 
  - CNPJ: `1` (Contribuinte)
  - CPF: `9` (Não contribuinte)
- **Tipo de Contato**: `C` (Cliente)

### 2. **Reutilização de Clientes Existentes**

#### Busca Inteligente
- Busca cliente no Bling por CPF/CNPJ antes de criar
- Se encontrar: **Atualiza** dados do cliente existente
- Se não encontrar: **Cria** novo cliente
- Evita duplicação de clientes

### 3. **Integração Automática**

#### Sincronização com Pedidos
- Quando pedido é sincronizado com Bling, cliente é sincronizado automaticamente
- Garante que cliente existe antes de criar pedido
- Não bloqueia criação do pedido se falhar (mas loga aviso)

### 4. **Suporte CPF e CNPJ**

#### Validação Completa
- **CPF**: 11 dígitos com validação de dígitos verificadores
- **CNPJ**: 14 dígitos com validação de dígitos verificadores
- Detecção automática do tipo
- Formatação automática removida antes de enviar

## 🔄 Fluxos de Cliente

### Fluxo 1: Primeira Compra (Cliente Novo)

```
1. Cliente faz pedido no site
   ↓
2. Dados fiscais salvos na venda (snapshot)
   ↓
3. Pedido sincronizado com Bling (webhook ou manual)
   ↓
4. sync_client_for_order() verifica se cliente existe
   ↓
5. Cliente NÃO encontrado no Bling
   ↓
6. Cliente criado no Bling com dados da venda
   ✅ Cliente disponível no Bling
```

### Fluxo 2: Cliente Existente (Compra Subsequente)

```
1. Cliente faz novo pedido
   ↓
2. Pedido sincronizado com Bling
   ↓
3. sync_client_for_order() busca cliente por CPF/CNPJ
   ↓
4. Cliente ENCONTRADO no Bling
   ↓
5. Dados do cliente atualizados no Bling
   ✅ Cliente atualizado, evita duplicação
```

### Fluxo 3: Atualização Manual de Dados Fiscais

```
1. Cliente atualiza dados fiscais no perfil
   ↓
2. Dados salvos em dados_fiscais
   ↓
3. Na próxima compra, dados atualizados são usados
   ↓
4. Cliente no Bling é atualizado automaticamente
   ✅ Dados sempre atualizados
```

## 📋 Estrutura de Dados

### Formato de Envio para Bling API:

```json
{
  "nome": "João Silva",
  "tipoPessoa": "F",
  "cpf_cnpj": "12345678901",
  "ie": "",
  "contribuinte": 9,
  "endereco": "Rua das Flores",
  "numero": "123",
  "complemento": "Apto 45",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "uf": "SP",
  "cep": "01234567",
  "email": "joao@example.com",
  "celular": "11999999999",
  "tipo": "C"
}
```

### Mapeamento de Campos:

| Campo Local | Campo Bling | Observações |
|-------------|-------------|-------------|
| `fiscal_nome_razao_social` | `nome` | Nome ou Razão Social |
| `fiscal_cpf_cnpj` | `cpf_cnpj` | Sem formatação (apenas dígitos) |
| `fiscal_inscricao_estadual` | `ie` | Obrigatória para CNPJ |
| - | `tipoPessoa` | "F" (CPF) ou "J" (CNPJ) - automático |
| - | `contribuinte` | 1 (CNPJ) ou 9 (CPF) - automático |
| `rua_entrega` | `endereco` | Rua |
| `numero_entrega` | `numero` | Número |
| `complemento_entrega` | `complemento` | Opcional |
| `bairro_entrega` | `bairro` | Bairro |
| `cidade_entrega` | `cidade` | Cidade |
| `estado_entrega` | `uf` | UF (2 letras) |
| `cep_entrega` | `cep` | Sem formatação (8 dígitos) |
| `email_entrega` | `email` | Email |
| `telefone_entrega` | `celular` | Telefone/Celular |
| - | `tipo` | "C" (Cliente) - fixo |

## ✅ Validações Implementadas

### CPF/CNPJ:
- ✅ Formato correto (11 ou 14 dígitos)
- ✅ Validação de dígitos verificadores
- ✅ Remoção de formatação automática

### Endereço:
- ✅ Rua obrigatória
- ✅ Número obrigatório
- ✅ Bairro obrigatório
- ✅ Cidade obrigatória
- ✅ UF obrigatória (2 letras)
- ✅ CEP obrigatório (8 dígitos)

### CNPJ Específico:
- ✅ Inscrição Estadual obrigatória

## 🔧 Funções Principais

### `sync_client_for_order(venda_id)`
- Busca dados do cliente da venda
- Sincroniza cliente no Bling
- Retorna resultado da operação

### `create_or_update_client_in_bling(cliente_data)`
- Valida dados fiscais
- Busca cliente existente por CPF/CNPJ
- Cria novo ou atualiza existente
- Retorna ID do cliente no Bling

### `find_client_in_bling(cpf_cnpj)`
- Busca cliente no Bling por CPF/CNPJ
- Retorna dados do cliente se encontrado

### `validate_fiscal_data(cliente_data)`
- Valida todos os campos obrigatórios
- Retorna lista de erros (vazia se válido)

### `validate_cpf_cnpj(cpf_cnpj)`
- Valida CPF ou CNPJ
- Verifica dígitos verificadores
- Retorna (is_valid, tipo)

## 🎯 Como Testar

### Teste 1: Criar Cliente Novo

```powershell
# Criar pedido no site (com dados fiscais)
# Depois sincronizar pedido com Bling
POST /api/bling/pedidos/sync/{venda_id}

# Verificar logs: cliente criado no Bling
# Verificar no painel Bling: cliente deve aparecer
```

### Teste 2: Reutilizar Cliente Existente

```powershell
# Criar segundo pedido com mesmo CPF/CNPJ
# Sincronizar pedido
POST /api/bling/pedidos/sync/{venda_id}

# Verificar logs: cliente encontrado e atualizado
# Verificar no Bling: cliente não foi duplicado
```

### Teste 3: Validar CPF/CNPJ

```powershell
# Tentar criar pedido com CPF inválido
# Deve falhar na validação
# Verificar mensagem de erro
```

## ⚠️ Armadilhas Evitadas

1. **Duplicação de Clientes**
   - ✅ Busca cliente antes de criar
   - ✅ Reutiliza cliente existente
   - ✅ Atualiza dados se necessário

2. **Dados Fiscais Incompletos**
   - ✅ Validação completa antes de enviar
   - ✅ Erros claros e específicos
   - ✅ Não cria cliente inválido

3. **CPF/CNPJ Inválido**
   - ✅ Validação de dígitos verificadores
   - ✅ Formatação automática removida
   - ✅ Tipo detectado automaticamente

4. **Endereço Incompleto**
   - ✅ Validação de todos os campos obrigatórios
   - ✅ CEP validado (8 dígitos)
   - ✅ UF validada (2 letras)

5. **Inscrição Estadual para CNPJ**
   - ✅ Obrigatória apenas para CNPJ
   - ✅ Opcional para CPF

## 📝 Próximos Passos

Após validar gerenciamento de clientes:
- **ETAPA 6**: Pedidos (criação no Bling com CFOP)
- **ETAPA 7**: NF-e (emissão automática)
- **ETAPA 8**: Logística
- **ETAPA 9**: Financeiro
- **ETAPA 10**: Dashboards

## 🔗 Integração com Outras Etapas

- **ETAPA 4 (Estoque)**: Cliente não afeta estoque
- **ETAPA 6 (Pedidos)**: Cliente criado automaticamente antes do pedido
- **ETAPA 7 (NF-e)**: Cliente necessário para emissão de nota fiscal

