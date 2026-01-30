# Dockerfile para Nginx Reverse Proxy
# Versionamento exato para reprodutibilidade total
ARG NGINX_VERSION=1.25.5
FROM nginx:${NGINX_VERSION}-alpine

# Instalar wget para health check
RUN apk add --no-cache wget

# Copiar configuração customizada
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Criar diretórios de log e cache
RUN mkdir -p /var/log/nginx /var/cache/nginx

# Expor porta
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]
