# Dockerfile para Strapi Admin
# Versionamento exato para reprodutibilidade total
ARG NODE_VERSION=20.11.1
ARG STRAPI_VERSION=5.33.1
FROM node:${NODE_VERSION}-slim

# Variáveis de ambiente (aumentar heap do Node para evitar "JavaScript heap out of memory")
ENV NODE_ENV=production \
    STRAPI_VERSION=${STRAPI_VERSION} \
    NODE_OPTIONS="--max-old-space-size=2048"

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    libvips-dev \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Configurar npm para melhor resiliência de rede
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000

# Instalar dependências (incluindo opcionais como sharp) com cache
RUN --mount=type=cache,target=/root/.npm \
    npm ci --include=optional --no-audit || \
    (echo "npm ci falhou, tentando npm install..." && npm install --include=optional --no-audit)

# Instalar sharp explicitamente para garantir compatibilidade
RUN --mount=type=cache,target=/root/.npm \
    npm install sharp@0.33.0 --platform=linux --arch=x64 --force || \
    npm install --os=linux --cpu=x64 sharp@0.33.0 --force || \
    npm rebuild sharp@0.33.0 --platform=linux --arch=x64 || \
    npm install sharp@0.33.0 --include=optional --force

# Copiar código da aplicação
COPY . .

# Tornar script de entrada executável
RUN chmod +x entrypoint.sh || true

# Build do Strapi (será sobrescrito pelo volume, mas serve como fallback)
# Desabilitado - schema será pré-criado via SQL
# RUN npm run build || true

# Expor porta
EXPOSE 1337

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:1337/_health || exit 1

# Usar script de entrada que verifica se precisa fazer build
CMD ["sh", "/app/entrypoint.sh"]

