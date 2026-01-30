#!/bin/bash
# Script para fazer push das imagens para Docker Hub

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configurações
VERSION=${1:-latest}
DOCKERHUB_USER=${DOCKERHUB_USER:-""}

if [ -z "$DOCKERHUB_USER" ]; then
    echo -e "${RED}❌ DOCKERHUB_USER não configurado${NC}"
    echo "Configure com: export DOCKERHUB_USER=seu-usuario"
    exit 1
fi

REGISTRY="docker.io/${DOCKERHUB_USER}"

echo -e "${GREEN}📤 Fazendo push das imagens para Docker Hub...${NC}"
echo -e "${YELLOW}Usuário: ${DOCKERHUB_USER}${NC}"
echo -e "${YELLOW}Versão: ${VERSION}${NC}"
echo ""

# Verificar login
echo -e "${YELLOW}🔐 Verificando autenticação no Docker Hub...${NC}"
if ! docker info | grep -q "Username" 2>/dev/null; then
    echo -e "${RED}❌ Não autenticado no Docker Hub${NC}"
    echo -e "${YELLOW}Execute: docker login${NC}"
    exit 1
fi

CURRENT_USER=$(docker info 2>/dev/null | grep "Username" | awk '{print $2}' || echo "")
if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != "$DOCKERHUB_USER" ]; then
    echo -e "${YELLOW}⚠️  Usuário logado (${CURRENT_USER}) diferente do configurado (${DOCKERHUB_USER})${NC}"
    read -p "Continuar mesmo assim? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✅ Autenticado no Docker Hub${NC}"
echo ""

# Push Flask
echo -e "${YELLOW}📤 Fazendo push Flask (${VERSION})...${NC}"
docker push ${REGISTRY}/lhama-banana-flask:${VERSION}
docker push ${REGISTRY}/lhama-banana-flask:latest
echo -e "${GREEN}✅ Flask enviado!${NC}"
echo ""

# Push Strapi
echo -e "${YELLOW}📤 Fazendo push Strapi (${VERSION})...${NC}"
docker push ${REGISTRY}/lhama-banana-strapi:${VERSION}
docker push ${REGISTRY}/lhama-banana-strapi:latest
echo -e "${GREEN}✅ Strapi enviado!${NC}"
echo ""

# Push Nginx
echo -e "${YELLOW}📤 Fazendo push Nginx (${VERSION})...${NC}"
docker push ${REGISTRY}/lhama-banana-nginx:${VERSION}
docker push ${REGISTRY}/lhama-banana-nginx:latest
echo -e "${GREEN}✅ Nginx enviado!${NC}"
echo ""

echo -e "${GREEN}🎉 Push concluído com sucesso!${NC}"
echo ""
echo -e "${YELLOW}Imagens disponíveis em:${NC}"
echo "  - https://hub.docker.com/r/${DOCKERHUB_USER}/lhama-banana-flask"
echo "  - https://hub.docker.com/r/${DOCKERHUB_USER}/lhama-banana-strapi"
echo "  - https://hub.docker.com/r/${DOCKERHUB_USER}/lhama-banana-nginx"
echo ""
echo -e "${YELLOW}Para usar as imagens:${NC}"
echo "  docker pull ${DOCKERHUB_USER}/lhama-banana-flask:${VERSION}"
echo "  docker pull ${DOCKERHUB_USER}/lhama-banana-strapi:${VERSION}"
echo "  docker pull ${DOCKERHUB_USER}/lhama-banana-nginx:${VERSION}"
