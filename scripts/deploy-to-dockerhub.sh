#!/bin/bash
# Script completo: Build, Tag, Test e Push para Docker Hub

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

VERSION=${1:-latest}
SKIP_BUILD=${2:-false}

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 Deploy para Docker Hub - Lhama Banana  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Verificar DOCKERHUB_USER
if [ -z "$DOCKERHUB_USER" ]; then
    echo -e "${RED}❌ DOCKERHUB_USER não configurado${NC}"
    echo ""
    echo -e "${YELLOW}Configure com:${NC}"
    echo "  export DOCKERHUB_USER=seu-usuario"
    echo ""
    echo -e "${YELLOW}Ou edite o script e defina DOCKERHUB_USER diretamente${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configuração:${NC}"
echo -e "  Usuário: ${DOCKERHUB_USER}"
echo -e "  Versão: ${VERSION}"
echo ""

# 1. Build
if [ "$SKIP_BUILD" != "true" ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📦 Passo 1: Construindo imagens...${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    ./scripts/build-and-tag.sh $VERSION
    echo ""
else
    echo -e "${YELLOW}⏭️  Pulando build (SKIP_BUILD=true)${NC}"
    echo ""
fi

# 2. Test
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🧪 Passo 2: Testando imagens...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
./scripts/test-images.sh $VERSION
echo ""

# 3. Confirmação antes do push
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📤 Pronto para fazer push para Docker Hub${NC}"
echo -e "${YELLOW}   Usuário: ${DOCKERHUB_USER}${NC}"
echo -e "${YELLOW}   Versão: ${VERSION}${NC}"
echo ""
read -p "Deseja continuar com o push? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Push cancelado pelo usuário${NC}"
    exit 0
fi

# 4. Push
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📤 Passo 3: Fazendo push para Docker Hub...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
./scripts/push-to-dockerhub.sh $VERSION
echo ""

# 5. Resumo final
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Deploy concluído com sucesso!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📦 Imagens publicadas:${NC}"
echo -e "  • ${DOCKERHUB_USER}/lhama-banana-flask:${VERSION}"
echo -e "  • ${DOCKERHUB_USER}/lhama-banana-strapi:${VERSION}"
echo -e "  • ${DOCKERHUB_USER}/lhama-banana-nginx:${VERSION}"
echo ""
echo -e "${YELLOW}🔗 Links:${NC}"
echo -e "  • https://hub.docker.com/r/${DOCKERHUB_USER}/lhama-banana-flask"
echo -e "  • https://hub.docker.com/r/${DOCKERHUB_USER}/lhama-banana-strapi"
echo -e "  • https://hub.docker.com/r/${DOCKERHUB_USER}/lhama-banana-nginx"
echo ""
