# 🐳 Deploy para Docker Hub - Guia Completo

Este guia explica como fazer build, tag e push das imagens Docker para o Docker Hub.

## 📋 Pré-requisitos

1. **Conta no Docker Hub**: [Criar conta](https://hub.docker.com/signup)
2. **Docker instalado**: Docker Desktop ou Docker Engine
3. **Docker Compose**: Já incluído no Docker Desktop

## 🚀 Passo a Passo

### 1. Login no Docker Hub

```bash
docker login
```

Você será solicitado a inserir:
- **Username**: Seu usuário do Docker Hub
- **Password**: Sua senha ou Access Token

> 💡 **Dica**: Para maior segurança, use um Access Token ao invés da senha:
> - Docker Hub > Account Settings > Security > New Access Token

### 2. Configurar Usuário

```bash
# Opção 1: Variável de ambiente (temporária)
export DOCKERHUB_USER=seu-usuario

# Opção 2: Adicionar ao .env (permanente)
echo "DOCKERHUB_USER=seu-usuario" >> .env
```

### 3. Tornar Scripts Executáveis

```bash
# Linux/Mac
chmod +x scripts/build-and-tag.sh
chmod +x scripts/push-to-dockerhub.sh
chmod +x scripts/test-images.sh
chmod +x scripts/deploy-to-dockerhub.sh

# Windows (PowerShell)
# Os scripts .sh precisam ser executados via Git Bash ou WSL
```

### 4. Deploy Completo (Recomendado)

```bash
# Deploy completo: Build + Test + Push
./scripts/deploy-to-dockerhub.sh v1.0.0
```

Este script faz tudo automaticamente:
1. ✅ Constrói as imagens
2. ✅ Aplica tags
3. ✅ Testa as imagens
4. ✅ Faz push para Docker Hub

### 5. Deploy Manual (Passo a Passo)

Se preferir fazer manualmente:

```bash
# 1. Build e Tag
./scripts/build-and-tag.sh v1.0.0

# 2. Testar imagens
./scripts/test-images.sh v1.0.0

# 3. Push para Docker Hub
./scripts/push-to-dockerhub.sh v1.0.0
```

## 📦 O que será publicado

As seguintes imagens serão publicadas no Docker Hub:

- `seu-usuario/lhama-banana-flask:v1.0.0` e `latest`
- `seu-usuario/lhama-banana-strapi:v1.0.0` e `latest`
- `seu-usuario/lhama-banana-nginx:v1.0.0` e `latest`

## 🔍 Verificar Publicação

### No Docker Hub

Acesse:
- https://hub.docker.com/r/seu-usuario/lhama-banana-flask
- https://hub.docker.com/r/seu-usuario/lhama-banana-strapi
- https://hub.docker.com/r/seu-usuario/lhama-banana-nginx

### Via Linha de Comando

```bash
# Verificar se as imagens existem
docker pull seu-usuario/lhama-banana-flask:v1.0.0
docker pull seu-usuario/lhama-banana-strapi:v1.0.0
docker pull seu-usuario/lhama-banana-nginx:v1.0.0

# Listar imagens locais
docker images | grep seu-usuario/lhama-banana
```

## 🔄 Atualizar Versão

Para publicar uma nova versão:

```bash
# Exemplo: versão 1.1.0
./scripts/deploy-to-dockerhub.sh v1.1.0
```

## 📝 Usar Imagens do Docker Hub

Após publicar, você pode atualizar o `docker-compose.yml` para usar as imagens do Docker Hub:

```yaml
flask:
  image: seu-usuario/lhama-banana-flask:v1.0.0
  # build:  # Comentar ou remover
  #   context: .
  #   dockerfile: Dockerfile

strapi:
  image: seu-usuario/lhama-banana-strapi:v1.0.0
  # build:  # Comentar ou remover
  #   context: ./strapi-admin
  #   dockerfile: Dockerfile

nginx:
  image: seu-usuario/lhama-banana-nginx:v1.0.0
  # build:  # Comentar ou remover
  #   context: .
  #   dockerfile: nginx/Dockerfile
```

## 🐛 Troubleshooting

### Erro: "unauthorized: authentication required"

```bash
# Reautenticar
docker login
```

### Erro: "DOCKERHUB_USER não configurado"

```bash
# Configurar variável
export DOCKERHUB_USER=seu-usuario

# Ou adicionar ao .env
echo "DOCKERHUB_USER=seu-usuario" >> .env
```

### Erro: "repository does not exist"

O Docker Hub criará os repositórios automaticamente no primeiro push. Não é necessário criar manualmente.

### Push muito lento

```bash
# Verificar conexão
docker pull hello-world

# Usar conexão mais rápida (se disponível)
# Configurar mirror no Docker Desktop
```

### Imagem muito grande

```bash
# Ver tamanho das imagens
docker images | grep lhama-banana

# Analisar camadas
docker history seu-usuario/lhama-banana-flask:v1.0.0
```

## 📊 Comandos Úteis

```bash
# Ver imagens locais
docker images | grep lhama-banana

# Inspecionar imagem
docker inspect seu-usuario/lhama-banana-flask:v1.0.0

# Ver histórico de uma imagem
docker history seu-usuario/lhama-banana-flask:v1.0.0

# Remover imagens antigas
docker rmi seu-usuario/lhama-banana-flask:v1.0.0

# Limpar imagens não utilizadas
docker image prune -a
```

## ✅ Checklist Antes do Deploy

- [ ] Conta no Docker Hub criada
- [ ] Login realizado (`docker login`)
- [ ] `DOCKERHUB_USER` configurado
- [ ] Scripts tornados executáveis
- [ ] Versão definida (ex: `v1.0.0`)
- [ ] Testes locais passando
- [ ] Código commitado (opcional, mas recomendado)

## 🔗 Links Úteis

- [Docker Hub](https://hub.docker.com/)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `docker compose logs`
2. Verifique autenticação: `docker info`
3. Teste conexão: `docker pull hello-world`
4. Verifique permissões no Docker Hub
