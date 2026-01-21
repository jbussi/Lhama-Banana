# 🔄 Como Renovar Token Bling Manualmente

## ⚠️ Situação Atual

O token do Bling está expirado e o rate limiting está bloqueando a renovação automática.

## ✅ Solução: Renovar Manualmente via Navegador

### Passo 1: Verificar se o ngrok está rodando

O ngrok é necessário para o callback OAuth funcionar. Verifique se está rodando:

```bash
# Verificar processos ngrok
Get-Process | Where-Object {$_.ProcessName -like "*ngrok*"}
```

Se não estiver rodando, inicie o ngrok:

```bash
ngrok http 5000
```

Anote a URL HTTPS gerada (exemplo: `https://xxxx-xxxx-xxxx.ngrok-free.dev`)

### Passo 2: Configurar Redirect URI (se necessário)

Se o ngrok gerou uma URL diferente, atualize a variável de ambiente:

```powershell
$env:BLING_REDIRECT_URI="https://SUA-URL-NGROK.ngrok-free.dev/api/bling/callback"
```

E reinicie o Flask:

```bash
docker-compose restart flask
```

### Passo 3: Renovar Token via Navegador

1. **Acesse o endpoint de autorização:**

   ```
   http://localhost:5000/api/bling/authorize
   ```

   OU se o ngrok estiver rodando:

   ```
   https://SUA-URL-NGROK.ngrok-free.dev/api/bling/authorize
   ```

2. **Você será redirecionado para o Bling**
   - Faça login na sua conta Bling
   - Autorize a aplicação "LhamaBanana E-commerce"
   - Clique em "Autorizar" ou "Permitir"

3. **Você será redirecionado de volta**
   - O sistema irá trocar o código por tokens automaticamente
   - Os tokens serão salvos no banco de dados

### Passo 4: Verificar se funcionou

```bash
curl http://localhost:5000/api/bling/tokens
```

Deve retornar `"authorized": true` e um novo `expires_at`.

### Passo 5: Sincronizar Situações

Após renovar o token, execute:

```bash
docker-compose exec -T flask python renovar_token_e_sincronizar.py
```

Ou use o endpoint da API:

```bash
# Via curl (PowerShell)
Invoke-WebRequest -Uri "http://localhost:5000/api/bling/situacoes/sync" -Method POST
```

## 🔍 Troubleshooting

### Problema: "Redirect URI mismatch"
- Verifique se a URL do ngrok está configurada corretamente no Bling
- Verifique se `BLING_REDIRECT_URI` está configurado corretamente

### Problema: "Rate limiting"
- Aguarde 10-15 minutos antes de tentar novamente
- Ou use a renovação manual via navegador (não afetada por rate limiting)

### Problema: "Token inválido"
- O refresh_token pode ter expirado
- É necessário autorizar novamente via navegador
