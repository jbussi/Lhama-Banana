#!/bin/bash
# Script para testar imagens Docker

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DOCKERHUB_USER=${DOCKERHUB_USER:-""}
VERSION=${1:-latest}

if [ -z "$DOCKERHUB_USER" ]; then
    echo -e "${YELLOW}⚠️  DOCKERHUB_USER não configurado, testando imagens locais...${NC}"
    PREFIX="lhama_banana"
else
    PREFIX="${DOCKERHUB_USER}/lhama-banana"
fi

echo -e "${GREEN}🧪 Testando imagens Docker...${NC}"
echo ""

# Função para testar imagem
test_image() {
    local image=$1
    local name=$2
    
    echo -e "${YELLOW}🔍 Testando ${name} (${image})...${NC}"
    
    # Verificar se imagem existe
    if ! docker image inspect $image >/dev/null 2>&1; then
        echo -e "${RED}❌ Imagem ${image} não encontrada${NC}"
        return 1
    fi
    
    # Verificar tamanho
    SIZE=$(docker image inspect $image --format='{{.Size}}' 2>/dev/null | numfmt --to=iec-i --suffix=B 2>/dev/null || echo "N/A")
    echo -e "  📏 Tamanho: ${SIZE}"
    
    # Verificar healthcheck
    HEALTH=$(docker image inspect $image --format='{{.Config.Healthcheck}}' 2>/dev/null)
    if [ "$HEALTH" != "<no value>" ] && [ -n "$HEALTH" ]; then
        echo -e "  ✅ Healthcheck configurado"
    else
        echo -e "  ⚠️  Healthcheck não configurado"
    fi
    
    # Verificar variáveis de ambiente
    ENV_COUNT=$(docker image inspect $image --format='{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | wc -l)
    echo -e "  🔧 Variáveis de ambiente: ${ENV_COUNT}"
    
    # Verificar se tem entrypoint ou cmd
    CMD=$(docker image inspect $image --format='{{.Config.Cmd}}' 2>/dev/null)
    if [ "$CMD" != "<no value>" ] && [ -n "$CMD" ]; then
        echo -e "  ✅ Comando de inicialização configurado"
    fi
    
    echo -e "${GREEN}✅ ${name} testado com sucesso${NC}"
    echo ""
}

# Testar imagens
test_image "${PREFIX}-flask:${VERSION}" "Flask"
test_image "${PREFIX}-strapi:${VERSION}" "Strapi"
test_image "${PREFIX}-nginx:${VERSION}" "Nginx"

echo -e "${GREEN}🎉 Todos os testes concluídos!${NC}"
