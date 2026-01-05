# 🐛 Debug de Autenticação - Login Google

## Problema

Erro 401 ao fazer login com Google:
```
POST http://127.0.0.1:5000/api/auth/login 401 (UNAUTHORIZED)
Erro no fluxo de login: Token inválido ou expirado
```

**Erro específico nos logs:**
```
Token Firebase inválido: Token used too early, 1767627825 < 1767627836. 
Check that your computer's clock is set correctly.
```

Este é um problema de **clock skew** - o servidor está alguns segundos à frente do cliente, então o token ainda não é válido quando chega ao servidor.

## Soluções Aplicadas

### 1. Retry Logic para Clock Skew ✅

Adicionado retry logic no `auth_service.py` para lidar com problemas de sincronização de relógio entre cliente e servidor.

**Correção importante:** O erro "too early" vem como `InvalidIdTokenError`, então agora tratamos esse caso específico antes de rejeitar o token.

### 2. Force Refresh do Token ✅

No frontend, o token agora é forçado a ser atualizado antes de enviar:
```javascript
id_token = await user.getIdToken(true); // true = force refresh
```

### 3. Delay Aumentado ✅

Delay aumentado para **2000ms (2 segundos)** no frontend para dar mais tempo ao token ser válido antes de enviar ao servidor.

### 4. Tratamento Específico de "Too Early" ✅

O erro "Token used too early" agora é tratado corretamente mesmo quando vem como `InvalidIdTokenError`, permitindo que o retry logic funcione.

### 4. Melhor Tratamento de Erros ✅

Logs mais detalhados adicionados para identificar o problema exato.

### 5. Endpoint de Teste ✅

Criado endpoint `/api/auth/test-token` para testar tokens diretamente.

## Como Debuggar

### 1. Verificar Logs do Flask

```bash
docker compose logs flask -f
```

Procure por:
- "Token verificado com sucesso"
- "Token Firebase inválido"
- "Erro ao verificar token"

### 2. Usar Endpoint de Teste

No console do navegador, após fazer login com Google:

```javascript
// Obter token
const user = auth.currentUser;
const token = await user.getIdToken(true);

// Testar token
fetch('/api/auth/test-token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: token })
})
.then(r => r.json())
.then(console.log);
```

Isso mostrará:
- Se o token foi recebido
- Se o Firebase está inicializado
- Se o token é válido
- Detalhes do token decodificado
- Erro específico (se houver)

### 3. Verificar Firebase Admin SDK

Verifique se o Firebase está inicializado corretamente:

```bash
docker compose logs flask | grep -i firebase
```

Deve mostrar:
```
✅ Firebase Admin SDK inicializado com sucesso!
```

### 4. Verificar key.json

Certifique-se de que o arquivo `key.json` está no lugar correto:
- No Docker: `/app/key.json` (montado via volume)
- Localmente: `../key.json` (raiz do workspace)

## Possíveis Causas

### 1. Clock Skew
**Sintoma**: Token válido mas rejeitado
**Solução**: Já implementado retry logic

### 2. Token Expirado Muito Rápido
**Sintoma**: Token obtido mas expirado antes de chegar ao servidor
**Solução**: Force refresh implementado

### 3. Firebase Admin SDK Não Inicializado
**Sintoma**: Erro 503 ou "Serviço de autenticação não disponível"
**Solução**: Verificar inicialização no `plataform_config/__init__.py`

### 4. key.json Inválido ou Ausente
**Sintoma**: Firebase não inicializa
**Solução**: Verificar arquivo e permissões

### 5. Token do Google OAuth com Formato Diferente
**Sintoma**: Token válido no cliente mas rejeitado no servidor
**Solução**: Verificar se o Firebase Admin SDK suporta tokens OAuth do Google

## Próximos Passos

1. **Testar o endpoint de teste** para ver o erro exato
2. **Verificar logs** para ver mensagens detalhadas
3. **Se o problema persistir**, pode ser necessário:
   - Verificar se o projeto Firebase está configurado corretamente
   - Verificar se o Google OAuth está habilitado no Firebase Console
   - Verificar se os domínios autorizados estão corretos

## Comandos Úteis

```bash
# Ver logs em tempo real
docker compose logs flask -f

# Reiniciar Flask
docker compose restart flask

# Verificar se Firebase está inicializado
docker compose exec flask python -c "import firebase_admin; print('Firebase apps:', firebase_admin._apps)"
```

---

**Última atualização**: 2024-01-05

