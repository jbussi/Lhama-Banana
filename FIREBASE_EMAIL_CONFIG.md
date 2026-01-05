# Configuração de Templates de Email no Firebase

Este guia explica como configurar os templates de email do Firebase Authentication para que os emails de verificação de conta e recuperação de senha sejam enviados corretamente.

## 📧 Emails Gerenciados pelo Firebase

O Firebase Authentication envia automaticamente dois tipos de emails:

1. **Email de Verificação de Conta** - Enviado após cadastro
2. **Email de Recuperação de Senha** - Enviado quando o usuário solicita "Esqueci minha senha"

## 🔧 Como Configurar

### Passo 1: Acessar o Firebase Console

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Selecione seu projeto (`lhamabanana-981d5`)
3. No menu lateral, vá em **Authentication**
4. Clique na aba **Templates**

### Passo 2: Configurar Email de Verificação

1. Na lista de templates, encontre **Email address verification**
2. Clique para editar
3. Configure:

   **Assunto do Email:**
   ```
   Verifique seu email - LhamaBanana
   ```

   **Corpo do Email (HTML):**
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="UTF-8">
       <style>
           body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
           .container { max-width: 600px; margin: 0 auto; padding: 20px; }
           .header { background: linear-gradient(135deg, #40e0d0, #2ab7a9); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
           .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
           .button { display: inline-block; background: #40e0d0; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
           .footer { text-align: center; margin-top: 20px; color: #666; font-size: 0.9rem; }
       </style>
   </head>
   <body>
       <div class="container">
           <div class="header">
               <h1>Bem-vindo ao LhamaBanana!</h1>
           </div>
           <div class="content">
               <p>Olá!</p>
               <p>Obrigado por se cadastrar. Para ativar sua conta, clique no botão abaixo para verificar seu endereço de email:</p>
               <p style="text-align: center;">
                   <a href="%LINK%" class="button">Verificar Email</a>
               </p>
               <p>Ou copie e cole este link no seu navegador:</p>
               <p style="word-break: break-all; color: #40e0d0;">%LINK%</p>
               <p><strong>Importante:</strong> Este link expira em 3 dias.</p>
               <p>Se você não criou esta conta, pode ignorar este email.</p>
           </div>
           <div class="footer">
               <p>© 2025 LhamaBanana. Todos os direitos reservados.</p>
           </div>
       </div>
   </body>
   </html>
   ```

   **Corpo do Email (Texto Simples):**
   ```
   Bem-vindo ao LhamaBanana!

   Obrigado por se cadastrar. Para ativar sua conta, clique no link abaixo para verificar seu endereço de email:

   %LINK%

   Este link expira em 3 dias.

   Se você não criou esta conta, pode ignorar este email.

   © 2025 LhamaBanana. Todos os direitos reservados.
   ```

4. Clique em **Salvar**

### Passo 3: Configurar Email de Recuperação de Senha

1. Na lista de templates, encontre **Password reset**
2. Clique para editar
3. Configure:

   **Assunto do Email:**
   ```
   Redefinir sua senha - LhamaBanana
   ```

   **Corpo do Email (HTML):**
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="UTF-8">
       <style>
           body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
           .container { max-width: 600px; margin: 0 auto; padding: 20px; }
           .header { background: linear-gradient(135deg, #40e0d0, #2ab7a9); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
           .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }
           .button { display: inline-block; background: #40e0d0; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }
           .footer { text-align: center; margin-top: 20px; color: #666; font-size: 0.9rem; }
           .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
       </style>
   </head>
   <body>
       <div class="container">
           <div class="header">
               <h1>Redefinir Senha</h1>
           </div>
           <div class="content">
               <p>Olá!</p>
               <p>Recebemos uma solicitação para redefinir a senha da sua conta no LhamaBanana.</p>
               <p>Clique no botão abaixo para criar uma nova senha:</p>
               <p style="text-align: center;">
                   <a href="%LINK%" class="button">Redefinir Senha</a>
               </p>
               <p>Ou copie e cole este link no seu navegador:</p>
               <p style="word-break: break-all; color: #40e0d0;">%LINK%</p>
               <div class="warning">
                   <strong>⚠️ Importante:</strong>
                   <ul style="margin: 10px 0; padding-left: 20px;">
                       <li>Este link expira em 1 hora</li>
                       <li>Se você não solicitou esta redefinição, ignore este email</li>
                       <li>Sua senha não será alterada até que você clique no link</li>
                   </ul>
               </div>
           </div>
           <div class="footer">
               <p>© 2025 LhamaBanana. Todos os direitos reservados.</p>
           </div>
       </div>
   </body>
   </html>
   ```

   **Corpo do Email (Texto Simples):**
   ```
   Redefinir Senha - LhamaBanana

   Recebemos uma solicitação para redefinir a senha da sua conta.

   Clique no link abaixo para criar uma nova senha:

   %LINK%

   ⚠️ IMPORTANTE:
   - Este link expira em 1 hora
   - Se você não solicitou esta redefinição, ignore este email
   - Sua senha não será alterada até que você clique no link

   © 2025 LhamaBanana. Todos os direitos reservados.
   ```

4. Clique em **Salvar**

### Passo 4: Configurar URL de Redirecionamento (Opcional)

1. Em **Authentication** > **Settings** > **Authorized domains**
2. Adicione seus domínios autorizados:
   - `localhost` (já vem por padrão para desenvolvimento)
   - Seu domínio de produção (ex: `lhamabanana.com.br`)

3. Em **Authentication** > **Settings** > **Action URL**
   - Configure a URL de redirecionamento após verificação/reset
   - Exemplo: `https://lhamabanana.com.br/auth/login?verified=true`

## 🔗 Variáveis Disponíveis nos Templates

O Firebase fornece as seguintes variáveis que você pode usar nos templates:

- `%LINK%` - Link de ação (verificação ou reset)
- `%EMAIL%` - Email do usuário
- `%DISPLAY_NAME%` - Nome do usuário (se disponível)

## ✅ Verificação

### Testar Email de Verificação:

1. Crie uma nova conta no sistema
2. Verifique se o email foi recebido
3. Clique no link de verificação
4. Confirme que a conta foi verificada

### Testar Email de Recuperação:

1. Na página de login, clique em "Esqueceu a senha?"
2. Digite um email cadastrado
3. Verifique se o email foi recebido
4. Clique no link e redefina a senha

## 🚨 Troubleshooting

### Emails não estão sendo enviados:

1. **Verifique o domínio autorizado:**
   - O Firebase só envia emails para domínios autorizados
   - Certifique-se de que seu domínio está na lista

2. **Verifique a configuração do projeto:**
   - Vá em **Project Settings** > **General**
   - Confirme que o "Public-facing name" está correto

3. **Verifique limites de quota:**
   - O Firebase tem limites de emails por dia
   - Verifique em **Usage and billing**

4. **Verifique spam:**
   - Os emails podem estar indo para a pasta de spam
   - Adicione `noreply@lhamabanana-981d5.firebaseapp.com` aos contatos

### Link não funciona:

1. **Verifique expiração:**
   - Email de verificação: 3 dias
   - Email de reset: 1 hora

2. **Verifique domínio autorizado:**
   - O link só funciona em domínios autorizados

3. **Verifique HTTPS:**
   - Em produção, o Firebase requer HTTPS

## 📝 Notas Importantes

1. **Personalização:**
   - Você pode personalizar completamente os templates
   - Use HTML para criar emails bonitos
   - Mantenha o `%LINK%` para que o link funcione

2. **Segurança:**
   - Os links gerados pelo Firebase são seguros e únicos
   - Cada link só pode ser usado uma vez
   - Links expiram automaticamente

3. **Localização:**
   - Você pode criar templates em múltiplos idiomas
   - Configure em **Authentication** > **Templates** > **Language**

## 🔄 Atualização dos Templates

Se você atualizar os templates:

1. As mudanças são aplicadas imediatamente
2. Emails já enviados continuam com o template antigo
3. Novos emails usarão o template atualizado

---

**Última atualização:** Janeiro 2025


