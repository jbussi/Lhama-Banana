# 🚀 Como Enviar Imagens para Docker Hub

## 📋 Passo a Passo Simples

### 1️⃣ Login no Docker Hub

Abra o terminal e execute:

```bash
docker login
```

Digite seu **usuário** e **senha** do Docker Hub.

> 💡 **Não tem conta?** Crie em: https://hub.docker.com/signup

---

### 2️⃣ Configurar Seu Usuário

**Windows (PowerShell):**
```powershell
$env:DOCKERHUB_USER = "seu-usuario"
```

**Linux/Mac:**
```bash
export DOCKERHUB_USER=seu-usuario
```

> ⚠️ **Substitua `seu-usuario` pelo seu usuário real do Docker Hub!**

---

### 3️⃣ Executar Deploy

**Windows (PowerShell):**
```powershell
cd Lhama-Banana
.\scripts\deploy-to-dockerhub.ps1 -Version v1.0.0
```

**Linux/Mac:**
```bash
cd Lhama-Banana
chmod +x scripts/*.sh
./scripts/deploy-to-dockerhub.sh v1.0.0
```

---

### 4️⃣ Aguardar Conclusão

O script vai:
1. ✅ Construir as imagens
2. ✅ Aplicar tags
3. ✅ Fazer push para Docker Hub

Isso pode levar alguns minutos dependendo da sua conexão.

---

### 5️⃣ Verificar no Docker Hub

Acesse seu perfil no Docker Hub:
- https://hub.docker.com/u/seu-usuario

Você verá os repositórios:
- `lhama-banana-flask`
- `lhama-banana-strapi`
- `lhama-banana-nginx`

---

## 🎯 Resumo dos Comandos

```bash
# 1. Login
docker login

# 2. Configurar usuário
export DOCKERHUB_USER=seu-usuario  # Linux/Mac
# ou
$env:DOCKERHUB_USER = "seu-usuario"  # Windows PowerShell

# 3. Deploy
./scripts/deploy-to-dockerhub.sh v1.0.0  # Linux/Mac
# ou
.\scripts\deploy-to-dockerhub.ps1 -Version v1.0.0  # Windows
```

---

## ❓ Problemas Comuns

### "DOCKERHUB_USER não configurado"
→ Configure a variável de ambiente (passo 2)

### "unauthorized: authentication required"
→ Execute `docker login` novamente

### "permission denied"
→ No Linux/Mac, execute: `chmod +x scripts/*.sh`

---

## 📦 O que será publicado?

- `seu-usuario/lhama-banana-flask:v1.0.0` e `latest`
- `seu-usuario/lhama-banana-strapi:v1.0.0` e `latest`
- `seu-usuario/lhama-banana-nginx:v1.0.0` e `latest`

---

## 🔄 Para Publicar Nova Versão

```bash
./scripts/deploy-to-dockerhub.sh v1.1.0
```

---

## 📚 Documentação Completa

Para mais detalhes, veja: [DOCKERHUB_DEPLOY.md](DOCKERHUB_DEPLOY.md)
