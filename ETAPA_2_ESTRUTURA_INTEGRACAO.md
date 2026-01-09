# ETAPA 2 - Estrutura de Integração Bling

## ✅ O Que Foi Implementado

### 1. **Camada de Abstração Robusta (`bling_api_service.py`)**

A camada de abstração fornece:
- **Retry automático** com backoff exponencial
- **Rate limiting** (delay mínimo entre requisições)
- **Tratamento de erros padronizado** com classes de exceção customizadas
- **Renovação automática de tokens** (401)
- **Logs estruturados** para auditoria

### 2. **Sistema de Retry com Backoff Exponencial**

```python
# Retry automático para:
# - 429 (Rate Limit): delay 60s, 120s, 180s
# - 500-503 (Server Errors): backoff exponencial 1s, 2s, 4s, 8s
# - Timeout/Network errors: backoff exponencial
```

**Características:**
- Máximo de 3 tentativas (configurável)
- Delay crescente entre tentativas
- Tratamento especial para rate limit (delay maior)
- Não faz retry em erros de validação (400, 422)

### 3. **Classes de Exceção Customizadas**

```python
BlingAPIError
├── error_type: BlingErrorType (enum)
├── status_code: int
├── message: str
└── error_details: dict
```

**Tipos de Erro:**
- `AUTHENTICATION_ERROR` (401): Token inválido/expirado
- `VALIDATION_ERROR` (400): Dados inválidos
- `RATE_LIMIT_ERROR` (429): Limite de requisições excedido
- `NOT_FOUND_ERROR` (404): Recurso não encontrado
- `SERVER_ERROR` (500+): Erro no servidor Bling
- `NETWORK_ERROR`: Timeout/conexão
- `UNKNOWN_ERROR`: Erro não classificado

### 4. **Rate Limiting**

```python
# Delay mínimo de 0.5s entre requisições
# Previne atingir limite de 100 req/min do Bling
_rate_limiter = BlingRateLimiter(min_delay_seconds=0.5)
```

### 5. **Error Handler no Blueprint**

Todos os erros `BlingAPIError` são capturados automaticamente e retornam respostas JSON padronizadas:

```json
{
  "success": false,
  "error": "validation_error",
  "message": "Descrição do erro",
  "status_code": 400,
  "details": { ... }  // apenas em DEBUG
}
```

### 6. **Logs Estruturados**

Todos os logs incluem:
- ✅ Sucesso (status 200-299)
- ⚠️ Avisos (retry, token expirado)
- ❌ Erros (classificados por tipo)
- 🌐 Requisições (método + endpoint)
- 🔄 Retries (tentativa X de Y)

## 🔍 Como Testar

### Teste 1: Verificar Estrutura Básica

```powershell
$ngrokUrl = "https://efractory-burdenless-kathlene.ngrok-free.dev"

# Testar endpoint simples
$response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/test" `
    -Method GET -Headers @{"ngrok-skip-browser-warning"="true"}

$response | ConvertTo-Json
```

**Resultado Esperado:**
```json
{
  "success": true,
  "message": "Conexão com API Bling funcionando!",
  "status_code": 200,
  "products_count": 1
}
```

### Teste 2: Testar Rate Limiting

```powershell
# Fazer múltiplas requisições rapidamente
# O sistema deve adicionar delay automático entre elas
1..5 | ForEach-Object {
    $start = Get-Date
    Invoke-RestMethod -Uri "$ngrokUrl/api/bling/test" `
        -Method GET -Headers @{"ngrok-skip-browser-warning"="true"} | Out-Null
    $elapsed = ((Get-Date) - $start).TotalSeconds
    Write-Host "Requisição $_: $elapsed segundos"
}
```

**Resultado Esperado:**
- Cada requisição deve levar pelo menos 0.5s (devido ao rate limiting)
- Logs devem mostrar requisições sendo feitas sequencialmente

### Teste 3: Testar Tratamento de Erros

```powershell
# Tentar acessar recurso inexistente (deve retornar erro padronizado)
try {
    $response = Invoke-RestMethod -Uri "$ngrokUrl/api/bling/test" `
        -Method GET -Headers @{"ngrok-skip-browser-warning"="true"} -ErrorAction Stop
} catch {
    $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
    Write-Host "Erro capturado: $($errorResponse.error)"
    Write-Host "Mensagem: $($errorResponse.message)"
}
```

### Teste 4: Verificar Logs

```powershell
# Ver logs do Flask para verificar estrutura de logs
docker compose logs flask -f --tail=50
```

**O que procurar nos logs:**
- `🌐 Bling API Request: GET /produtos`
- `✅ Bling API: GET /produtos - OK (200)`
- `⚠️ Token expirado. Renovando...` (se aplicável)
- `❌ Bling API Error: ...` (em caso de erro)

### Teste 5: Testar Retry Automático (Simulado)

```powershell
# O sistema automaticamente retry em caso de:
# - Rate limit (429)
# - Erros de servidor (500-503)
# - Timeout

# Este teste pode ser feito via logs quando ocorrer naturalmente
# Ou forçando uma situação de rate limit (muitas requisições)
```

## 📊 Estrutura de Dados

### Resposta de Sucesso Padrão
```json
{
  "success": true,
  "data": { ... },
  "status_code": 200
}
```

### Resposta de Erro Padrão
```json
{
  "success": false,
  "error": "validation_error",
  "message": "Descrição humanizada do erro",
  "status_code": 400,
  "details": {
    "fields": [...],
    "raw_response": "..."
  }
}
```

## 🔧 Configurações

### Rate Limiting
```python
# Em bling_api_service.py
_rate_limiter = BlingRateLimiter(min_delay_seconds=0.5)
```

### Retry
```python
# Parâmetros padrão
max_retries=3
base_delay=1.0  # segundos
max_delay=60.0  # segundos
```

### Timeout
```python
timeout=30  # segundos para todas as requisições
```

## 🎯 Próximos Passos

Com a estrutura de integração completa, podemos avançar para:

**ETAPA 3 - Cadastro e Sincronização de Produtos**
- Mapeamento de campos
- Validação fiscal
- Criação/atualização no Bling
- Sincronização bidirecional

## ⚠️ Armadilhas Evitadas

1. **Rate Limiting**: Delay automático previne bloqueio
2. **Token Expired**: Renovação automática sem interrupção
3. **Retry Infinito**: Máximo de tentativas evita loops
4. **Erros Não Tratados**: Todas as exceções são capturadas
5. **Logs Inconsistentes**: Formato padronizado facilita debug

## 📚 Arquivos Modificados

1. `blueprints/services/bling_api_service.py`
   - Classes de exceção
   - Rate limiter
   - Retry com backoff exponencial
   - Tratamento de erros

2. `blueprints/api/bling.py`
   - Error handler padronizado
   - Atualização de endpoints para usar nova estrutura

