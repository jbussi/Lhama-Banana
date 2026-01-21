# ETAPA 7 - Emissão de Nota Fiscal (NF-e/NFC-e)

## ✅ O Que Foi Implementado

### 1. **Emissão Automática de NF-e via Bling**

#### Condições para Emissão
- ✅ Pagamento confirmado (status `processando_envio` ou superior)
- ✅ Pedido existe no Bling (sincronizado)
- ✅ Dados fiscais completos (CPF/CNPJ, nome, endereço)
- ✅ Cliente existe no Bling

#### Fluxo de Emissão
1. Verifica condições necessárias
2. Solicita emissão de NF-e via API do Bling
3. Armazena informações da NF-e (XML, chave de acesso, número)
4. Atualiza status da NF-e

### 2. **Snapshot Fiscal**

#### Dados Armazenados
- Dados fiscais do cliente (snapshot no momento da venda)
- Endereço fiscal completo
- CPF/CNPJ e inscrições
- Todos os dados necessários para emissão

### 3. **Armazenamento de NF-e**

#### Tabelas Utilizadas
- `notas_fiscais`: Registro principal da NF-e
- `bling_pedidos`: Referência com ID da NF-e no Bling

#### Dados Armazenados
- **Número da NF-e**: Número sequencial
- **Chave de Acesso**: 44 dígitos (obrigatória)
- **XML**: XML completo da NF-e (quando disponível)
- **Status**: `pendente`, `processando`, `emitida`, `erro`, `cancelada`
- **Resposta da API**: JSON completo com todos os dados

### 4. **Consulta de Status**

#### Verificação Automática
- Consulta status da NF-e no Bling
- Atualiza informações localmente
- Detecta mudanças de status

### 5. **Tratamento de Erros Fiscais**

#### Validações
- Dados fiscais completos
- Pedido existe no Bling
- Status do pedido adequado
- Erros específicos da API do Bling

#### Recuperação
- Registro criado mesmo se falhar
- Status `pendente` permite retry posterior
- Logs detalhados para debug

## 🔄 Fluxos de NF-e

### Fluxo 1: Emissão Automática (Após Pagamento Confirmado)

```
1. Pagamento confirmado (webhook PagBank)
   ↓
2. Pedido sincronizado com Bling
   ↓
3. Status muda para 'processando_envio'
   ↓
4. check_and_emit_nfe() chamado automaticamente
   ↓
5. emit_nfe_for_order() verifica condições
   ↓
6. NF-e emitida via Bling API
   ↓
7. Informações salvas (XML, chave, número)
   ✅ NF-e emitida e armazenada
```

### Fluxo 2: Emissão Manual

```
1. Admin solicita emissão manual
   ↓
2. POST /api/bling/pedidos/nfe/emitir/{venda_id}
   ↓
3. Verificações de condições
   ↓
4. NF-e emitida via Bling
   ✅ NF-e disponível
```

### Fluxo 3: Consulta de Status

```
1. GET /api/bling/pedidos/nfe/status/{venda_id}
   ↓
2. Busca pedido no Bling
   ↓
3. Consulta informações da NF-e
   ↓
4. Atualiza status local
   ✅ Status atualizado
```

## 📋 Estrutura de Dados

### Informações da NF-e Armazenadas:

```json
{
  "id": 123,
  "venda_id": 456,
  "codigo_pedido": "LB-20260110-ABCD",
  "numero_nfe": "12345",
  "chave_acesso": "35200112345678000100550010000012345678901234",
  "status_emissao": "emitida",
  "data_emissao": "2026-01-10T14:30:00",
  "api_response": {
    "id": 789012,
    "numero": 12345,
    "chaveAcesso": "35200112345678000100550010000012345678901234",
    "situacao": "AUTORIZADA",
    "xml": "<nfeProc>...</nfeProc>"
  }
}
```

### Status da NF-e:

| Status Local | Situação Bling | Descrição |
|--------------|----------------|-----------|
| `pendente` | PENDENTE | Aguardando emissão |
| `processando` | PROCESSANDO | Em processamento |
| `emitida` | EMITIDA, AUTORIZADA | NF-e emitida com sucesso |
| `erro` | ERRO, REJEITADA | Erro na emissão |
| `cancelada` | CANCELADA | NF-e cancelada |

## 🔧 Endpoints Disponíveis

### Emitir NF-e
```http
POST /api/bling/pedidos/nfe/emitir/{venda_id}
```

**Resposta de Sucesso:**
```json
{
  "success": true,
  "nfe_id": 789012,
  "nfe_numero": 12345,
  "nfe_chave_acesso": "35200112345678000100550010000012345678901234",
  "nfe_situacao": "AUTORIZADA",
  "message": "Emissão de NF-e solicitada com sucesso"
}
```

### Consultar Status da NF-e
```http
GET /api/bling/pedidos/nfe/status/{venda_id}
```

**Resposta:**
```json
{
  "success": true,
  "nfe_id": 789012,
  "nfe_numero": 12345,
  "nfe_chave_acesso": "35200112345678000100550010000012345678901234",
  "nfe_situacao": "AUTORIZADA",
  "has_xml": true
}
```

### Buscar NF-e por Venda
```http
GET /api/nfe/{venda_id}
# Usa get_nfe_by_venda_id() do nfe_service.py
```

## ✅ Validações Implementadas

### Antes de Emitir:
- ✅ Pagamento confirmado (status adequado)
- ✅ Pedido existe no Bling
- ✅ Dados fiscais completos
- ✅ Cliente existe no Bling

### Dados Obrigatórios:
- ✅ CPF/CNPJ do cliente
- ✅ Nome/Razão Social
- ✅ Endereço fiscal completo
- ✅ Produtos com NCM válido (já validado na ETAPA 3)
- ✅ CFOP calculado (já implementado na ETAPA 6)

## 🎯 Como Testar

### Teste 1: Emissão Automática

```powershell
# 1. Criar pedido no site
# 2. Confirmar pagamento (webhook PagBank)
# 3. Verificar logs: NF-e emitida automaticamente
# 4. Verificar no Bling: NF-e deve aparecer no pedido
```

### Teste 2: Emissão Manual

```powershell
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

# Emitir NF-e para pedido específico
Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/nfe/emitir/1" `
    -Method POST -Headers @{"ngrok-skip-browser-warning"="true"}
```

### Teste 3: Consultar Status

```powershell
# Consultar status da NF-e
Invoke-RestMethod -Uri "$ngrokUrl/api/bling/pedidos/nfe/status/1" `
    -Method GET -Headers @{"ngrok-skip-browser-warning"="true"}
```

## ⚠️ Armadilhas Evitadas

1. **Emissão em Duplicidade**
   - ✅ Verifica se NF-e já existe antes de emitir
   - ✅ Consulta status se já foi emitida

2. **Pedido Não Sincronizado**
   - ✅ Verifica se pedido existe no Bling
   - ✅ Sugere sincronização se não encontrado

3. **Dados Fiscais Incompletos**
   - ✅ Valida antes de tentar emitir
   - ✅ Cria registro com erro se dados incompletos

4. **Pagamento Não Confirmado**
   - ✅ Verifica status do pedido
   - ✅ Emite apenas após confirmação

5. **Erros da API do Bling**
   - ✅ Trata erros específicos
   - ✅ Salva mensagens de erro
   - ✅ Permite retry posterior

## 📝 Próximos Passos

Após validar emissão de NF-e:
- **ETAPA 8**: Logística (integração com Melhor Envio)
- **ETAPA 9**: Financeiro (contas a receber, dashboards)
- **ETAPA 10**: Dashboards e insights

## 🔗 Integração com Outras Etapas

- **ETAPA 3 (Produtos)**: NCM obrigatório para emissão
- **ETAPA 5 (Clientes)**: Cliente deve existir no Bling
- **ETAPA 6 (Pedidos)**: Pedido com CFOP correto é necessário
- **Bling**: Gerencia emissão real via SEFAZ


