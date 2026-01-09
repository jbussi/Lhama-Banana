# 🧪 Guia de Teste - Integração Bling

## ✅ Passo 1: Verificar Configuração

Primeiro, vamos verificar se as variáveis estão configuradas corretamente:

### 1.1 - Verificar Status da Configuração

Acesse no navegador ou via curl:

```
GET https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/status
```

**Resposta esperada:**
```json
{
  "client_id_configured": true,
  "client_secret_configured": true,
  "redirect_uri": "https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/callback",
  "authorize_url": "https://www.bling.com.br/Api/v3/oauth/authorize?..."
}
```

Se algum campo estiver `false`, verifique:
- ✅ `BLING_CLIENT_ID` está configurado no `.env` ou variáveis de ambiente
- ✅ `BLING_CLIENT_SECRET` está configurado
- ✅ `BLING_REDIRECT_URI` está configurado (deve ser exatamente a URL do callback)

---

## 🔐 Passo 2: Iniciar Autorização OAuth

### 2.1 - Acessar Endpoint de Autorização

Abra no navegador:

```
https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/authorize
```

### 2.2 - O que vai acontecer:

1. Você será redirecionado para a página de login do Bling
2. Faça login na sua conta Bling
3. Você verá uma página pedindo permissão para a aplicação "LhamaBanana E-commerce"
4. Revise as permissões solicitadas:
   - ✅ Produtos
   - ✅ Pedidos
   - ✅ NF-e
   - ✅ Estoques
   - ✅ Contatos
   - ✅ Financeiro
5. Clique em **"Autorizar"** ou **"Permitir"**

### 2.3 - Redirecionamento

Após autorizar, você será redirecionado para:

```
https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/callback?code=...&state=...
```

O sistema irá:
- ✅ Validar o código de autorização
- ✅ Trocar código por access token e refresh token
- ✅ Armazenar tokens no banco de dados
- ✅ Retornar mensagem de sucesso

---

## ✅ Passo 3: Verificar Tokens Armazenados

### 3.1 - Verificar Status dos Tokens

Acesse:

```
GET https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/tokens
```

**Resposta esperada (sucesso):**
```json
{
  "authorized": true,
  "token_type": "Bearer",
  "access_token_preview": "abc123...",
  "refresh_token_preview": "xyz789...",
  "expires_at": "2026-01-08T12:00:00",
  "status": "Válido",
  "created_at": "2026-01-07T10:00:00",
  "updated_at": "2026-01-07T10:00:00"
}
```

**Se ainda não autorizado:**
```json
{
  "authorized": false,
  "message": "Bling não autorizado. Use /api/bling/authorize para autorizar."
}
```

---

## 🔍 Passo 4: Verificar no Banco de Dados

### 4.1 - Verificar Tabela `bling_tokens`

Execute no PostgreSQL:

```sql
SELECT 
    id,
    LEFT(access_token, 20) || '...' as access_token_preview,
    CASE WHEN refresh_token IS NOT NULL 
         THEN LEFT(refresh_token, 20) || '...' 
         ELSE NULL END as refresh_token_preview,
    token_type,
    expires_at,
    created_at,
    updated_at,
    CASE 
        WHEN expires_at > NOW() THEN 'Válido'
        ELSE 'Expirado'
    END as status
FROM bling_tokens
WHERE id = 1;
```

**Resultado esperado:** 1 linha com tokens válidos

---

## 🐛 Troubleshooting

### Erro: "BLING_CLIENT_ID não configurado"

**Solução:**
1. Verifique se a variável está no `.env` ou ambiente
2. Reinicie o servidor Flask após adicionar variáveis
3. Verifique se o nome da variável está correto (exatamente `BLING_CLIENT_ID`)

### Erro: "State token inválido ou expirado"

**Causa:** O state token expira em 5 minutos ou foi usado duas vezes

**Solução:**
1. Tente novamente acessando `/api/bling/authorize`
2. Complete o fluxo em menos de 5 minutos

### Erro: "Código de autorização não fornecido"

**Causa:** O Bling não retornou o código no callback

**Solução:**
1. Verifique se a URL de callback está correta no painel do Bling
2. Verifique se você autorizou a aplicação
3. Verifique logs do servidor para mais detalhes

### Erro: "Falha ao obter tokens do Bling"

**Causa:** Credenciais incorretas ou código inválido

**Solução:**
1. Verifique `BLING_CLIENT_ID` e `BLING_CLIENT_SECRET`
2. Verifique se a URL de callback no Bling está EXATAMENTE igual à configurada
3. Verifique logs do servidor para resposta do Bling

---

## ✅ Checklist de Validação

- [ ] `GET /api/bling/status` retorna todas as configurações como `true`
- [ ] `GET /api/bling/authorize` redireciona para página do Bling
- [ ] Login e autorização no Bling funcionam
- [ ] Callback retorna mensagem de sucesso
- [ ] `GET /api/bling/tokens` retorna `authorized: true`
- [ ] Tabela `bling_tokens` tem 1 registro com tokens válidos

---

## 🚀 Próximos Passos (Após Autorização Bem-Sucedida)

Uma vez que a autorização está funcionando, podemos implementar:

1. **Testar API do Bling**
   - Fazer requisição de teste para listar produtos
   - Verificar se access token está funcionando

2. **Sincronização de Produtos**
   - Criar função para enviar produtos do LhamaBanana para Bling
   - Criar função para buscar produtos do Bling

3. **Criação de Pedidos**
   - Enviar pedidos confirmados do LhamaBanana para Bling

4. **Emissão de NF-e**
   - Implementar emissão automática após pagamento confirmado

5. **Sincronização de Estoque**
   - Implementar sincronização bidirecional de estoque

---

## 📝 Comandos Úteis

### Testar com cURL

```bash
# Verificar status
curl https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/status

# Verificar tokens (após autorização)
curl https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/tokens

# Revogar autorização
curl -X POST https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/revoke
```

### Testar Requisição à API Bling (após autorização)

```python
# Exemplo de teste (implementar depois)
import requests

access_token = get_bling_access_token()  # Função a ser criada

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Listar produtos
response = requests.get(
    'https://www.bling.com.br/Api/v3/produtos',
    headers=headers
)

print(response.json())
```


