# ⚙️ Configuração Completa - LhamaBanana

## 📋 Índice
1. [Configuração Inicial](#configuração-inicial)
2. [Variáveis de Ambiente](#variáveis-de-ambiente)
3. [Firebase](#firebase)
4. [PagBank](#pagbank)
5. [Bling](#bling)
6. [Melhor Envio](#melhor-envio)
7. [Strapi](#strapi)
8. [Banco de Dados](#banco-de-dados)

## 🚀 Configuração Inicial

### 1. Criar arquivo `.env`

```bash
# Windows
Copy-Item env.example .env

# Linux/Mac
cp env.example .env
```

Ou use os scripts:
- Windows: `.\setup-env.ps1`
- Linux/Mac: `./setup-env.sh`

### 2. Configurar NTP (Importante!)

O servidor **DEVE** ter o relógio sincronizado via NTP para evitar erros com tokens do Firebase.

**Verificar sincronização:**
```bash
ntpdate -q pool.ntp.org
# ou
chrony sources
```

## 🔐 Variáveis de Ambiente

### Ambiente
```bash
ENV=development  # development, production, testing
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_PORT=5000
```

### Banco de Dados
```bash
DB_HOST=postgres  # No Docker: 'postgres', Local: 'localhost'
DB_NAME=sistema_usuarios
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_PORT=5432
```

## 🔥 Firebase

### 1. Obter credenciais
1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Crie um projeto ou selecione existente
3. Vá em **Configurações do Projeto** > **Contas de Serviço**
4. Clique em **Gerar nova chave privada**
5. Baixe o arquivo JSON

### 2. Configurar no projeto
```bash
# Coloque o arquivo JSON na raiz do projeto
# Renomeie para: key.json
```

**No `.env`:**
```bash
FIREBASE_ADMIN_SDK_PATH=/app/key.json  # Docker
# FIREBASE_ADMIN_SDK_PATH=../key.json  # Local
```

### 3. Configurar Email (Opcional)
```bash
FIREBASE_EMAIL_ENABLED=true
FIREBASE_EMAIL_FROM=noreply@seudominio.com
```

**Nota:** O sistema usa Firebase Authentication para envio de emails. Configure o template de email no Firebase Console se necessário.

### 4. Configurar E-mails Personalizados

O Firebase permite personalizar os links de ação (verificação de email, reset de senha) para usar seu próprio domínio.

#### URL de Ação Personalizada

Configure no Firebase Console:
```
https://seudominio.com/account-action?mode=%ACTION%&oobCode=%CODE%
```

**Para desenvolvimento local (com ngrok):**
```
https://seu-ngrok-url.ngrok-free.dev/account-action?mode=%ACTION%&oobCode=%CODE%
```

#### Como Configurar no Firebase Console

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Vá em **Authentication** > **Templates**
3. Para **Verificação de email**:
   - Clique no ícone de editar
   - Clique em **Personalizar URL de ação**
   - Cole: `https://seudominio.com/account-action?mode=verifyEmail&oobCode=%CODE%`
4. Para **Redefinir senha**:
   - Clique no ícone de editar
   - Clique em **Personalizar URL de ação**
   - Cole: `https://seudominio.com/account-action?mode=resetPassword&oobCode=%CODE%`

#### Rotas Implementadas

O sistema possui a rota `/account-action` que processa:
- `mode=verifyEmail` - Verificação de email
- `mode=resetPassword` - Redefinição de senha
- `mode=recoverEmail` - Recuperação de email
- `mode=emailSignin` - Login via email

### 5. Autenticação e Segurança

#### MFA (Multi-Factor Authentication)
O sistema suporta MFA via Firebase. Para habilitar:
1. Configure no Firebase Console
2. Os usuários podem ativar MFA no perfil
3. Endpoint: `POST /api/auth/enable-mfa`

#### Permissões de Admin
Configure emails de administradores no `.env`:
```bash
ADMIN_EMAILS=admin1@exemplo.com,admin2@exemplo.com
```

## 💳 PagBank

### 1. Obter credenciais
1. Acesse [PagBank Developers](https://dev.pagbank.uol.com.br/)
2. Crie uma aplicação
3. Obtenha o **API Token**

### 2. Configurar no `.env`
```bash
PAGBANK_API_TOKEN=seu-token-aqui
PAGBANK_ENVIRONMENT=sandbox  # sandbox ou production
PAGBANK_NOTIFICATION_URL=http://seudominio.com/api/webhook/pagbank
PAGBANK_SIMULATION_MODE=false  # true apenas para testes
```

### 3. Configurar Webhook
- **Sandbox**: Use ngrok para desenvolvimento local
- **Production**: Configure URL pública no painel PagBank

**Exemplo com ngrok:**
```bash
ngrok http 5000
# Use a URL gerada em PAGBANK_NOTIFICATION_URL
```

## 📦 Bling

### 1. OAuth Setup
1. Acesse [Bling Developers](https://developer.bling.com.br/)
2. Crie uma aplicação OAuth
3. Configure redirect URI: `http://seudominio.com/api/bling/callback`

### 2. Configurar no `.env`
```bash
BLING_CLIENT_ID=seu-client-id
BLING_CLIENT_SECRET=seu-client-secret
BLING_REDIRECT_URI=http://seudominio.com/api/bling/callback
```

### 3. Autorizar aplicação
Acesse: `http://seudominio.com/api/bling/authorize`

O sistema irá:
- Redirecionar para página de autorização do Bling
- Solicitar permissões necessárias
- Salvar tokens automaticamente

### 4. Sincronização de Estoque
O estoque é gerenciado pelo Bling e sincronizado automaticamente via webhook.

**Webhook do Bling:**
- Configure em: Bling > Configurações > Webhooks
- URL: `http://seudominio.com/api/webhook/bling`
- Eventos: `stock.created`, `stock.updated`, `stock.deleted`

**Sincronização manual:**
```bash
docker-compose exec flask python scripts/sync_estoque_bling.py
```

## 🚚 Melhor Envio

### 1. Obter token
1. Acesse [Melhor Envio](https://melhorenvio.com.br/)
2. Vá em **Integrações** > **API**
3. Gere um token de API

### 2. Configurar no `.env`
```bash
MELHOR_ENVIO_TOKEN=seu-token-aqui
MELHOR_ENVIO_CEP_ORIGEM=13219-052  # CEP da sua loja
```

## 📝 Strapi

### Configuração no `.env`
```bash
STRAPI_ENABLED=true
STRAPI_URL=http://strapi:1337  # Docker
# STRAPI_URL=http://localhost:1337  # Local
```

### Acessar Admin
- URL: `http://seudominio.com/admin`
- Ou diretamente: `http://localhost:1337/admin`

### Primeiro acesso
1. Acesse `/admin`
2. Crie conta de administrador
3. Configure Content Types conforme necessário

## 🗄️ Banco de Dados

### Estrutura

O banco de dados está versionado em:
- `db/schema.sql` - Schema completo do banco
- `db/seeds.sql` - Dados iniciais (opcional)
- `sql/` - Scripts de migração e atualização

### Usando Docker (Recomendado)
```bash
docker-compose up -d postgres
```

O schema será aplicado automaticamente na primeira inicialização.

### Manual
```bash
psql -U postgres -d sistema_usuarios -f db/schema.sql
```

### Scripts SQL Disponíveis

Scripts de migração e atualização estão em `sql/`:
- `fix-strapi-indexes.sql` - Criar índices faltantes do Strapi
- `atualizar-checkout-pagamentos.sql` - Atualizar schema para PagBank
- `tabela_etiquetas.sql` - Criar tabela de etiquetas de frete
- `seed-example-data.sql` - Popular dados de exemplo

**Executar script:**
```bash
docker-compose exec -T postgres psql -U postgres -d sistema_usuarios < sql/nome-do-script.sql
```

### Sincronizar relacionamentos Strapi
```bash
docker-compose exec postgres psql -U postgres -d sistema_usuarios -f db/sync_relations.sql
```

## ✅ Verificação

Após configurar tudo, verifique:

```bash
# Status dos serviços
docker-compose ps

# Logs
docker-compose logs -f

# Testar conexão com banco
docker-compose exec postgres psql -U postgres -d sistema_usuarios -c "SELECT 1;"
```

## 🔄 Atualização de Tokens

### Bling (quando expirar)
1. Acesse: `http://seudominio.com/api/bling/authorize`
2. Reautorize a aplicação

### PagBank
- Tokens não expiram, mas podem ser regenerados no painel

### Melhor Envio
- Tokens podem ser regenerados no painel Melhor Envio
