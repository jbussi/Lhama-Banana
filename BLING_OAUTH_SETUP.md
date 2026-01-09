# 🔗 Configuração OAuth 2.0 Bling

## ✅ Implementação Concluída

A integração OAuth 2.0 com o Bling foi implementada e está pronta para uso.

## 📋 URL de Callback para Configuração no Bling

**Use esta URL ao criar a aplicação no Bling:**

```
https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/callback
```

## 🔧 Passos para Configurar no Bling

### 1. Acessar Painel de Desenvolvedor

1. Acesse: https://www.bling.com.br/configuracoes/api-tokens
2. Faça login na sua conta Bling
3. Clique em **"Aplicações"** ou **"API Tokens"**
4. Clique em **"Criar nova aplicação"** ou **"Nova aplicação"**

### 2. Preencher Dados da Aplicação

**Nome da Aplicação:**
```
LhamaBanana E-commerce
```

**URL de Redirecionamento:**
```
https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/callback
```

**Descrição (opcional):**
```
Integração OAuth 2.0 para sincronização de produtos, pedidos, NF-e e financeiro do LhamaBanana com Bling ERP.
```

### 3. Selecionar Permissões (Scopes)

Marque as seguintes permissões:

- ✅ **Produtos** - Para sincronizar catálogo de produtos
- ✅ **Pedidos** - Para criar e gerenciar pedidos de venda
- ✅ **NF-e** - Para emitir notas fiscais eletrônicas
- ✅ **Estoques** - Para sincronizar controle de estoque
- ✅ **Contatos** - Para gerenciar clientes
- ✅ **Financeiro** - Para contas a receber/pagar e fluxo de caixa

### 4. Salvar e Obter Credenciais

Após criar a aplicação, o Bling irá fornecer:

- **Client ID** (ID do Cliente)
- **Client Secret** (Segredo do Cliente)

⚠️ **IMPORTANTE:** Guarde o Client Secret com segurança! Ele não será exibido novamente.

### 5. Configurar Variáveis de Ambiente

Adicione as credenciais no arquivo `.env` ou variáveis de ambiente:

```bash
# Bling OAuth 2.0
BLING_CLIENT_ID=seu-client-id-aqui
BLING_CLIENT_SECRET=seu-client-secret-aqui
```

Ou configure diretamente no ambiente:

**Windows PowerShell:**
```powershell
$env:BLING_CLIENT_ID="seu-client-id-aqui"
$env:BLING_CLIENT_SECRET="seu-client-secret-aqui"
```

**Linux/Mac:**
```bash
export BLING_CLIENT_ID="seu-client-id-aqui"
export BLING_CLIENT_SECRET="seu-client-secret-aqui"
```

### 6. Iniciar Autorização

Após configurar as credenciais, acesse:

```
https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/authorize
```

Isso irá redirecionar para a página de autorização do Bling. Após autorizar, você será redirecionado de volta e os tokens serão armazenados automaticamente.

## 📡 Endpoints Disponíveis

### 1. Iniciar Autorização
```
GET /api/bling/authorize
```
Redireciona para página de autorização do Bling.

### 2. Callback (Automático)
```
GET /api/bling/callback?code=...&state=...
```
Chamado automaticamente pelo Bling após autorização.

### 3. Verificar Status
```
GET /api/bling/status
```
Retorna informações sobre configuração OAuth.

### 4. Informações dos Tokens
```
GET /api/bling/tokens
```
Retorna informações sobre tokens armazenados (sem expor tokens completos).

### 5. Revogar Autorização
```
POST /api/bling/revoke
```
Remove tokens armazenados (desconecta aplicação).

## 🔍 Como Verificar se Funcionou

1. Acesse: `https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/status`
2. Verifique se `client_id_configured` e `client_secret_configured` são `true`
3. Acesse: `https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/authorize`
4. Autorize a aplicação no Bling
5. Verifique: `https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/tokens`
6. Deve retornar `authorized: true` com informações dos tokens

## 🗄️ Armazenamento de Tokens

Os tokens são armazenados na tabela `bling_tokens` no banco de dados PostgreSQL:

```sql
CREATE TABLE bling_tokens (
    id SERIAL PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(20) DEFAULT 'Bearer',
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

A tabela é criada automaticamente na primeira autorização.

## 🔄 Renovação Automática de Tokens

O sistema renova automaticamente os tokens quando necessário usando o `refresh_token`. Os tokens são atualizados na tabela `bling_tokens` quando renovados.

## ⚠️ Importante

1. **URL de Callback:** Certifique-se de usar exatamente a URL fornecida acima ao criar a aplicação no Bling
2. **Client Secret:** Mantenha o Client Secret seguro e não o exponha em código público
3. **Ambiente de Testes:** Esta configuração usa o domínio ngrok fornecido - atualize para produção quando necessário
4. **HTTPS:** O Bling requer HTTPS para callbacks em produção

## 🚀 Próximos Passos

Após configurar OAuth:

1. Testar sincronização de produtos
2. Implementar criação de pedidos
3. Configurar emissão automática de NF-e
4. Sincronizar estoque
5. Integrar financeiro

## 📚 Documentação Adicional

- [Documentação API Bling](https://developer.bling.com.br/)
- [Documentação OAuth 2.0 Bling](https://developer.bling.com.br/referencia/autenticacao)


