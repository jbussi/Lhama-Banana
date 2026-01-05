# 🔐 Guia de Verificação em Duas Etapas (2FA) - LhamaBanana

## 📋 Visão Geral

Sistema de verificação em duas etapas (2FA) implementado usando **TOTP (Time-based One-Time Password)**, compatível com apps autenticadores populares como:
- Google Authenticator
- Microsoft Authenticator
- Authy
- 1Password
- LastPass Authenticator

**Importante:** 2FA é **obrigatório apenas para administradores** que habilitarem a funcionalidade.

## 🎯 Funcionalidades

### ✅ Implementado

1. **Geração de QR Code** - Para escanear com app autenticador
2. **Chave Manual** - Para inserir manualmente no app
3. **Validação de Códigos** - Verificação de códigos de 6 dígitos
4. **Habilitar/Desabilitar** - Controle completo via perfil
5. **Verificação no Login** - Exige código 2FA para admins com 2FA habilitado
6. **Proteção de Rotas Admin** - Decorator verifica 2FA automaticamente

## 🚀 Como Usar

### Para Administradores

#### 1. Habilitar 2FA

1. Faça login como administrador
2. Acesse **Perfil** → **Segurança da Conta**
3. Na seção **"Verificação em Duas Etapas (2FA)"**, clique em **"Habilitar 2FA"**
4. Você verá:
   - **QR Code** para escanear
   - **Chave manual** (caso não consiga escanear)
5. Escaneie o QR code com seu app autenticador ou digite a chave manualmente
6. Digite o código de 6 dígitos gerado pelo app
7. Clique em **"Confirmar e Habilitar"**

#### 2. Fazer Login com 2FA

1. Faça login normalmente (email/senha ou Google)
2. Se você tiver 2FA habilitado, aparecerá um modal pedindo o código
3. Abra seu app autenticador
4. Digite o código de 6 dígitos
5. Clique em **"Verificar"**
6. Após verificação, você será redirecionado para o perfil

#### 3. Desabilitar 2FA

1. Acesse **Perfil** → **Segurança da Conta**
2. Na seção **"Verificação em Duas Etapas (2FA)"**, clique em **"Desabilitar 2FA"**
3. Digite o código 2FA atual para confirmar
4. Clique em **"Desabilitar 2FA"**

## 📱 Apps Autenticadores Recomendados

### Google Authenticator
- **iOS:** [App Store](https://apps.apple.com/app/google-authenticator/id388497605)
- **Android:** [Google Play](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)

### Microsoft Authenticator
- **iOS:** [App Store](https://apps.apple.com/app/microsoft-authenticator/id983156458)
- **Android:** [Google Play](https://play.google.com/store/apps/details?id=com.azure.authenticator)

### Authy
- **iOS:** [App Store](https://apps.apple.com/app/authy/id494168017)
- **Android:** [Google Play](https://play.google.com/store/apps/details?id=com.authy.authy)

## 🔧 Endpoints da API

### `POST /api/auth/mfa/setup`
Gera secret e QR code para configurar 2FA.

**Request:**
```json
{
  "id_token": "firebase_token_aqui"
}
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,...",
  "manual_entry_key": "JBSWY3DPEHPK3PXP",
  "instrucoes": "Escaneie o QR code..."
}
```

### `POST /api/auth/mfa/enable`
Habilita 2FA após verificar código.

**Request:**
```json
{
  "id_token": "firebase_token_aqui",
  "secret": "JBSWY3DPEHPK3PXP",
  "code": "123456"
}
```

### `POST /api/auth/mfa/verify`
Verifica código 2FA durante login.

**Request:**
```json
{
  "id_token": "firebase_token_aqui",
  "code": "123456"
}
```

### `POST /api/auth/mfa/disable`
Desabilita 2FA (requer código para confirmar).

**Request:**
```json
{
  "id_token": "firebase_token_aqui",
  "code": "123456"
}
```

### `POST /api/auth/mfa/status`
Retorna status de 2FA do usuário.

**Request:**
```json
{
  "id_token": "firebase_token_aqui"
}
```

**Response:**
```json
{
  "mfa_enabled": true,
  "has_secret": true,
  "is_admin": true
}
```

## 🔒 Segurança

### Boas Práticas

1. ✅ **Secret armazenado com segurança** - Apenas hash no banco
2. ✅ **Validação rigorosa** - Códigos expiram em 30 segundos
3. ✅ **Tolerância de tempo** - Aceita códigos adjacentes (±30s)
4. ✅ **Logs de auditoria** - Todas as ações são registradas
5. ✅ **Obrigatório para admins** - Se habilitado, é obrigatório no login
6. ✅ **Verificação em cada requisição admin** - Decorator verifica automaticamente

### Recomendações

1. **Backup do Secret:**
   - Anote a chave manual em local seguro
   - Use apps que permitem backup (Authy, 1Password)

2. **Múltiplos Dispositivos:**
   - Configure 2FA em mais de um dispositivo
   - Use apps com sincronização (Authy)

3. **Códigos de Recuperação:**
   - Considere gerar códigos de backup
   - Armazene em local seguro

## 🗄️ Estrutura do Banco de Dados

### Campos Adicionados

```sql
ALTER TABLE usuarios 
ADD COLUMN mfa_secret VARCHAR(32),
ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE;
```

- `mfa_secret`: Secret key TOTP (base32)
- `mfa_enabled`: Flag indicando se 2FA está habilitado

## 🔄 Fluxo de Login com 2FA

1. Usuário faz login (email/senha ou Google)
2. Backend verifica se é admin e se 2FA está habilitado
3. Se sim, retorna `requer_mfa: true`
4. Frontend mostra modal para inserir código
5. Usuário digita código do app autenticador
6. Backend valida código TOTP
7. Se válido, marca `mfa_verified` na sessão
8. Usuário é redirecionado para perfil

## 🛡️ Proteção de Rotas

O decorator `@admin_required_email` verifica automaticamente:

1. ✅ Token Firebase válido
2. ✅ Email verificado
3. ✅ Role admin
4. ✅ **2FA verificado** (se habilitado)

Se 2FA estiver habilitado mas não verificado, retorna **403 Forbidden**.

## 📝 Logs e Auditoria

Todas as ações de 2FA são registradas:

- `mfa_enable` - 2FA habilitado
- `mfa_disable` - 2FA desabilitado
- `mfa_verify` - Código verificado (sucesso/falha)

Logs incluem:
- UID do usuário
- Email
- IP address
- Timestamp
- Resultado (sucesso/falha)

## ⚙️ Configuração

### Variável de Ambiente (Opcional)

```env
# Nome do emissor que aparece no app autenticador
MFA_ISSUER_NAME=LhamaBanana
```

Padrão: `LhamaBanana`

## 🐛 Troubleshooting

### "Código 2FA inválido"

**Possíveis causas:**
1. Relógio do servidor/device dessincronizado
2. Código expirado (válido por 30s)
3. Secret incorreto no banco

**Soluções:**
1. Verifique se o relógio do dispositivo está correto
2. Use o código mais recente do app
3. Reconfigure 2FA se necessário

### "2FA não verificado" ao acessar área admin

**Causa:** Sessão expirou ou 2FA não foi verificado no login.

**Solução:** Faça logout e login novamente, verificando o código 2FA.

### Não consigo escanear o QR code

**Solução:** Use a chave manual fornecida e digite manualmente no app.

## 📚 Referências Técnicas

- **TOTP:** RFC 6238
- **Biblioteca:** pyotp (Python)
- **QR Code:** qrcode[pil] (Python)
- **Algoritmo:** SHA1 (padrão TOTP)
- **Período:** 30 segundos
- **Dígitos:** 6

## ✅ Checklist de Implementação

- [x] Campos no banco de dados
- [x] Funções de geração e validação
- [x] Endpoints da API
- [x] Interface no perfil
- [x] Modal de verificação no login
- [x] Decorator de proteção
- [x] Logs de auditoria
- [x] Documentação

---

**Última atualização:** Janeiro 2025


