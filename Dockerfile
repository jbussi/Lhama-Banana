# Dockerfile para Flask Application
# Versionamento exato para reprodutibilidade total
ARG PYTHON_VERSION=3.11.7
FROM python:${PYTHON_VERSION}-slim

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python (com cache para builds mais rápidos)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretório para logs
RUN mkdir -p /app/logs

# Tornar entrypoint.sh executável
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expor porta
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c 'import socket; s=socket.socket(); s.settimeout(2); result = s.connect_ex((\"localhost\", 5000)); s.close(); exit(0 if result == 0 else 1)' || exit 1

# Usar script de entrada que sincroniza o relógio antes de iniciar
CMD ["/app/entrypoint.sh"]

