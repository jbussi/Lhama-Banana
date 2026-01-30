# 🧪 Docker Test Environment - Lhama Banana

Este diretório contém uma configuração de teste simplificada para validar as imagens Docker antes de aplicar no projeto principal.

## 📋 Objetivo

- Testar builds de imagens Docker
- Validar configurações do docker-compose
- Testar integração entre serviços
- Preparar imagens para push em repositório Docker

## 🚀 Uso Rápido

### 1. Construir Imagens de Teste

```bash
cd docker-test
docker compose -f docker-compose.test.yml build
```

### 2. Iniciar Serviços de Teste

```bash
docker compose -f docker-compose.test.yml up -d
```

### 3. Verificar Status

```bash
docker compose -f docker-compose.test.yml ps
docker compose -f docker-compose.test.yml logs -f
```

### 4. Parar e Limpar

```bash
docker compose -f docker-compose.test.yml down
docker compose -f docker-compose.test.yml down -v  # Remove volumes também
```

## 🏷️ Tagging de Imagens

### Tag Local

```bash
# Flask
docker tag lhama_banana_flask:test lhama_banana_flask:latest
docker tag lhama_banana_flask:test lhama_banana_flask:v1.0.0

# Strapi (se necessário)
docker tag lhama_banana_strapi:test lhama_banana_strapi:latest
docker tag lhama_banana_strapi:test lhama_banana_strapi:v1.0.0

# Nginx (se necessário)
docker tag lhama_banana_nginx:test lhama_banana_nginx:latest
docker tag lhama_banana_nginx:test lhama_banana_nginx:v1.0.0
```

### Tag para Repositório

```bash
# Docker Hub
docker tag lhama_banana_flask:test seu-usuario/lhama-banana-flask:v1.0.0
docker tag lhama_banana_flask:test seu-usuario/lhama-banana-flask:latest

# GitHub Container Registry
docker tag lhama_banana_flask:test ghcr.io/seu-usuario/lhama-banana-flask:v1.0.0
docker tag lhama_banana_flask:test ghcr.io/seu-usuario/lhama-banana-flask:latest

# AWS ECR
docker tag lhama_banana_flask:test 123456789012.dkr.ecr.us-east-1.amazonaws.com/lhama-banana-flask:v1.0.0
docker tag lhama_banana_flask:test 123456789012.dkr.ecr.us-east-1.amazonaws.com/lhama-banana-flask:latest
```

## 📤 Push para Repositório

### Docker Hub

```bash
# Login
docker login

# Push
docker push seu-usuario/lhama-banana-flask:v1.0.0
docker push seu-usuario/lhama-banana-flask:latest
```

### GitHub Container Registry

```bash
# Login (use seu GitHub Personal Access Token)
echo $GITHUB_TOKEN | docker login ghcr.io -u seu-usuario --password-stdin

# Push
docker push ghcr.io/seu-usuario/lhama-banana-flask:v1.0.0
docker push ghcr.io/seu-usuario/lhama-banana-flask:latest
```

### AWS ECR

```bash
# Login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Criar repositório (se não existir)
aws ecr create-repository --repository-name lhama-banana-flask --region us-east-1

# Push
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/lhama-banana-flask:v1.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/lhama-banana-flask:latest
```

## 🧪 Testes Automatizados

### Script de Teste Completo

```bash
./test-build.sh
```

Este script:
1. Constrói todas as imagens
2. Executa testes básicos
3. Verifica healthchecks
4. Gera relatório

## 📊 Verificar Imagens

```bash
# Listar imagens locais
docker images | grep lhama_banana

# Inspecionar imagem
docker inspect lhama_banana_flask:test

# Ver histórico
docker history lhama_banana_flask:test

# Ver tamanho
docker images lhama_banana_flask:test --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

## 🔍 Troubleshooting

### Build Falha

```bash
# Ver logs detalhados
docker compose -f docker-compose.test.yml build --no-cache --progress=plain

# Testar Dockerfile isoladamente
docker build -t lhama_banana_flask:test -f ../Dockerfile ..
```

### Imagem Muito Grande

```bash
# Analisar camadas
docker history lhama_banana_flask:test

# Usar multi-stage build (ver Dockerfile otimizado)
```

### Push Falha

```bash
# Verificar login
docker login

# Verificar permissões no repositório
# Docker Hub: Settings > Access Tokens
# GitHub: Settings > Developer settings > Personal access tokens
# AWS: IAM policies para ECR
```

## 📝 Checklist Antes do Push

- [ ] Imagens construídas com sucesso
- [ ] Testes passando
- [ ] Healthchecks funcionando
- [ ] Tamanho das imagens aceitável
- [ ] Tags corretas aplicadas
- [ ] Login no repositório configurado
- [ ] Permissões verificadas
- [ ] Documentação atualizada

## 🔗 Links Úteis

- [Docker Hub](https://hub.docker.com/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [AWS ECR](https://aws.amazon.com/ecr/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
