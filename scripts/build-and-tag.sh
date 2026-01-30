#!/bin/bash
# Script para construir e fazer tag das imagens Docker para Docker Hub

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configurações
VERSION=${1:-latest}
DOCKERHUB_USER=${DOCKERHUB_USER:-""}

if [ -z "$DOCKERHUB_USER" ]; then
    echo -e "${RED}❌ DOCKERHUB_USER não configurado${NC}"
    echo "Configure com: export DOCKERHUB_USER=seu-usuario"
    echo "Ou edite o script e defina DOCKERHUB_USER diretamente"
    exit 1
fi

REGISTRY="docker.io/${DOCKERHUB_USER}"

echo -e "${GREEN}🏗️  Construindo imagens Docker para Docker Hub...${NC}"
echo -e "${YELLOW}Usuário: ${DOCKERHUB_USER}${NC}"
echo -e "${YELLOW}Versão: ${VERSION}${NC}"
echo ""

# Construir imagens
echo -e "${YELLOW}📦 Construindo Flask...${NC}"
docker compose build flask

echo -e "${YELLOW}📦 Construindo Strapi...${NC}"
docker compose build strapi

echo -e "${YELLOW}📦 Construindo Nginx...${NC}"
docker compose build nginx

echo ""
echo -e "${GREEN}🏷️  Aplicando tags para Docker Hub...${NC}"

# Flask
echo -e "${YELLOW}  Tagging Flask...${NC}"
docker tag lhama_banana_flask:latest ${REGISTRY}/lhama-banana-flask:${VERSION}
docker tag lhama_banana_flask:latest ${REGISTRY}/lhama-banana-flask:latest

# Strapi
echo -e "${YELLOW}  Tagging Strapi...${NC}"
docker tag lhama_banana_strapi:latest ${REGISTRY}/lhama-banana-strapi:${VERSION}
docker tag lhama_banana_strapi:latest ${REGISTRY}/lhama-banana-strapi:latest

# Nginx
echo -e "${YELLOW}  Tagging Nginx...${NC}"
docker tag lhama_banana_nginx:latest ${REGISTRY}/lhama-banana-nginx:${VERSION}
docker tag lhama_banana_nginx:latest ${REGISTRY}/lhama-banana-nginx:latest

echo ""
echo -e "${GREEN}✅ Imagens construídas e tags aplicadas!${NC}"
echo ""
echo -e "${YELLOW}Imagens prontas para push:${NC}"
docker images | grep ${REGISTRY}/lhama-banana | head -6
