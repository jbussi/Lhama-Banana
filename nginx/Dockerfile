FROM nginx:1.25-alpine

# Instalar wget para health check
RUN apk add --no-cache wget

# Copiar configuração customizada
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Criar diretórios de log
RUN mkdir -p /var/log/nginx

# Expor porta
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]
