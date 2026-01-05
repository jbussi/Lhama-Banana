# Dockerfile para Strapi Admin
# Usando node:20-slim ao invés de alpine para melhor compatibilidade com sharp
FROM node:20-slim

# Variáveis de ambiente
ENV NODE_ENV=production

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
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

# Instalar dependências (incluindo opcionais como sharp)
RUN npm ci --include=optional

# Instalar sharp explicitamente para garantir compatibilidade
RUN npm install sharp --platform=linux --arch=x64 --force || \
    npm install --os=linux --cpu=x64 sharp --force || \
    npm rebuild sharp --platform=linux --arch=x64 || \
    npm install sharp --include=optional --force

# Copiar código da aplicação
COPY . .

# Tornar script de entrada executável
RUN chmod +x entrypoint.sh || true

# Build do Strapi (será sobrescrito pelo volume, mas serve como fallback)
RUN npm run build || true

# Expor porta
EXPOSE 1337

# Usar script de entrada que verifica se precisa fazer build
CMD ["sh", "/app/entrypoint.sh"]

