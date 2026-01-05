# 🔐 Sistema de Autenticação Expandido - LhamaBanana

## 📋 Visão Geral

Sistema completo de autenticação usando **Firebase Authentication** como fonte de verdade para identidade, com o backend Flask atuando como camada de autorização, regras de negócio e auditoria.

## 🏗️ Arquitetura

### Firebase (Fonte de Verdade)
- ✅ Autenticação (email/senha e Google OAuth)
- ✅ Verificação de email
- ✅ Recuperação de senha
- ✅ Hash de senhas
- ✅ Gerenciamento de tokens JWT

### Backend Flask (Autorização e Negócio)
- ✅ Validação de tokens Firebase
- ✅ Sincronização com banco local
- ✅ Controle de permissões (admin/user)
- ✅ Verificação de email verificado
- ✅ Regras de negócio
- ✅ Auditoria e logs

### PostgreSQL (Dados e Auditoria)
- ✅ Dados do usuário
- ✅ Flags administrativas
- ✅ Histórico e métricas
- ✅ Rastreabilidade

## 🚀 Funcionalidades Implementadas

### 1. Login e Cadastro por Email/Senha ✅

**Frontend:**
- Login via Firebase `signInWithEmailAndPassword()`
- Registro via Firebase `createUserWithEmailAndPassword()`
- Validação de formulários
- Tratamento de erros

**Backend:**
- Validação de token Firebase
- Sincronização automática com banco local
- Criação de usuário se não existir
- Atualização de `email_verificado` baseado no token

**Endpoints:**
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Registro
- `POST /api/login_user` - Compatibilidade (redireciona para `/auth/login`)
- `POST /api/register_user` - Compatibilidade (redireciona para `/auth/register`)

### 2. Login e Cadastro via Google ✅

**Frontend:**
- Login via Firebase `signInWithPopup()` com Google Provider
- Botão "Entrar com Google" na página de login
- Botão "Cadastrar com Google" na página de registro
- Tratamento de erros (popup bloqueado, cancelado, etc)

**Backend:**
- Suporte completo a OAuth Google
- Sincronização automática
- Email verificado automaticamente para login Google
- Prevenção de duplicação de usuários

**Configuração:**
- Google OAuth já configurado no Firebase Console
- Escopos: `email` e `profile`

### 3. Verificação de Email ✅

**Firebase:**
- Envio automático de email de verificação após cadastro
- Método `sendEmailVerification()` no cliente

**Backend:**
- Verificação de `email_verified` no token Firebase
- Sincronização automática do status
- Bloqueio de acesso admin se email não verificado
- Campo `email_verificado` no banco sincronizado

**Endpoints:**
- `POST /api/auth/verify-email-status` - Verificar status atual
- `POST /api/auth/resend-verification` - Gerar link (para envio manual)

**Decorators:**
- `@admin_required_email` - Verifica email verificado para admins

### 4. Recuperação de Senha ✅

**Firebase:**
- Envio automático de email de reset
- Método `sendPasswordResetEmail()` no cliente

**Frontend:**
- Link "Esqueceu a senha?" na página de login
- Envio automático via Firebase

**Backend:**
- Endpoint para gerar link (caso necessário envio manual)
- `POST /api/auth/password-reset` - Gerar link de reset

### 5. Regras para Administradores ✅

**Verificações:**
- ✅ Email verificado (obrigatório)
- ✅ Role `admin` no banco OU email na lista `ADMIN_EMAILS`
- ✅ Token Firebase válido

**Decorators:**
- `@admin_required_email` - Verifica tudo automaticamente
- Retorna 403 se email não verificado
- Retorna 404 se não for admin (para não revelar área admin)

**Endpoints:**
- `POST /api/auth/check-admin` - Verificar se é admin

### 6. Sistema de Emails Customizados ✅

**Serviço:**
- `blueprints/services/email_service.py`
- Envio via SMTP
- Emails HTML formatados

**Funcionalidades:**
- `send_admin_alert()` - Alertas para todos os admins
- `send_security_alert()` - Alertas de segurança
- `send_new_user_notification()` - Notificação de novo usuário

**Configuração:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
EMAIL_FROM=noreply@lhamabanana.com
```

**Nota:** Para emails de autenticação (verificação, reset), o Firebase envia automaticamente.

### 7. Logs de Auditoria ✅

**Funcionalidades:**
- Registro de todos os eventos de autenticação
- Logs no banco (tabela `auditoria_logs`)
- Logs no console
- Alertas de segurança para eventos suspeitos

**Eventos Registrados:**
- Login (sucesso/falha)
- Registro (sucesso/falha)
- Tentativas inválidas
- Ações administrativas

**Função:**
- `log_auth_event(event_type, firebase_uid, success, details, ip_address)`

## 📁 Estrutura de Arquivos

```
Lhama-Banana/
├── blueprints/
│   ├── api/
│   │   └── auth.py                    # Novos endpoints de autenticação
│   ├── auth/
│   │   ├── static/
│   │   │   └── js/
│   │   │       ├── login.js           # Login com Google e verificação
│   │   │       └── register.js        # Registro com Google
│   │   └── templates/
│   │       ├── login.html            # Template atualizado
│   │       └── register.html         # Template atualizado
│   ├── admin/
│   │   └── decorators.py             # Decorators melhorados
│   └── services/
│       ├── auth_service.py           # Serviço centralizado de auth
│       └── email_service.py          # Serviço de emails customizados
├── config.py                          # Configurações de email adicionadas
└── env.example                        # Variáveis de ambiente atualizadas
```

## 🔧 Configuração

### 1. Firebase Console

1. Acesse [Firebase Console](https://console.firebase.google.com)
2. Vá em **Authentication** → **Sign-in method**
3. Habilite:
   - ✅ Email/Password
   - ✅ Google (configure OAuth consent screen)

### 2. Variáveis de Ambiente

Adicione ao seu `.env`:

```env
# Email (opcional - apenas para emails customizados)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
EMAIL_FROM=noreply@lhamabanana.com

# Admin (já existe)
ADMIN_EMAILS=admin1@email.com,admin2@email.com
```

### 3. Banco de Dados

O campo `email_verificado` já existe na tabela `usuarios`. O sistema sincroniza automaticamente.

## 📝 Uso

### Login com Email/Senha

```javascript
// Frontend já implementado
signInWithEmailAndPassword(auth, email, password)
  .then(userCredential => {
    // Token enviado automaticamente para backend
  })
```

### Login com Google

```javascript
// Frontend já implementado
signInWithPopup(auth, googleProvider)
  .then(userCredential => {
    // Token enviado automaticamente para backend
  })
```

### Verificar Status de Email

```javascript
// Frontend
const user = auth.currentUser;
if (!user.emailVerified) {
  await sendEmailVerification(user);
}
```

### Recuperar Senha

```javascript
// Frontend
await sendPasswordResetEmail(auth, email);
```

### Verificar se é Admin (Backend)

```python
from blueprints.services.auth_service import check_admin_access

is_admin = check_admin_access(user_data)
```

## 🔒 Segurança

### Boas Práticas Implementadas

1. ✅ **Validação rigorosa de tokens** em todas as requisições
2. ✅ **Não confiar em dados do frontend** - sempre validar no backend
3. ✅ **Logs de auditoria** para todas as ações
4. ✅ **Alertas de segurança** para eventos suspeitos
5. ✅ **Email verificado obrigatório** para administradores
6. ✅ **Firebase como fonte de verdade** - não duplicar lógica

### Recomendações

1. **Em produção:**
   - Configure HTTPS obrigatório
   - Use variáveis de ambiente seguras
   - Configure rate limiting
   - Monitore logs de auditoria

2. **SMTP:**
   - Use senha de app (não senha normal)
   - Configure SPF/DKIM para emails
   - Considere usar serviço de email (SendGrid, Mailgun, etc)

3. **Firebase:**
   - Configure domínios autorizados
   - Configure regras de segurança
   - Monitore uso da API

## 🐛 Troubleshooting

### "Email não verificado" mesmo após verificar

**Solução:** O status é sincronizado do Firebase. Faça logout e login novamente, ou chame `/api/auth/verify-email-status`.

### Login Google não funciona

**Verificar:**
1. Google OAuth habilitado no Firebase Console
2. Domínios autorizados configurados
3. Popups não bloqueados no navegador

### Emails não são enviados

**Para emails de autenticação:**
- O Firebase envia automaticamente
- Verifique spam/lixo eletrônico
- Verifique configurações do Firebase Console

**Para emails customizados:**
- Verifique configurações SMTP no `.env`
- Teste conexão SMTP
- Verifique logs do servidor

## 📚 Referências

- [Firebase Authentication Docs](https://firebase.google.com/docs/auth)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Google OAuth](https://developers.google.com/identity/protocols/oauth2)

---

**Última atualização:** 2024
**Versão:** 1.0.0

