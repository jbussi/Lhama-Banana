# Dockerfile para Strapi Admin
FROM node:20-alpine

# Variáveis de ambiente
ENV NODE_ENV=production

# Instalar wget para healthcheck
RUN apk add --no-cache wget

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências
COPY package*.json ./

# Instalar dependências (incluindo dev para build)
RUN npm ci

# Copiar código da aplicação
COPY . .

# Build do Strapi
RUN npm run build

# Expor porta
EXPOSE 1337

# Comando padrão
CMD ["npm", "run", "start"]

