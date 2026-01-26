#!/bin/bash
set -e

# Sincronizar relógio do sistema (importante para timestamps corretos)
echo "🕐 Sincronizando relógio do sistema..."
if command -v ntpdate &> /dev/null; then
    ntpdate -s time.nist.gov || true
elif command -v chronyd &> /dev/null; then
    chronyd -q || true
fi

# Aguardar PostgreSQL estar pronto
echo "⏳ Aguardando PostgreSQL estar pronto..."
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" > /dev/null 2>&1; do
    echo "   PostgreSQL ainda não está pronto. Aguardando..."
    sleep 2
done
echo "✅ PostgreSQL está pronto!"

# Determinar se deve usar Gunicorn ou Flask dev server
if [ "${USE_GUNICORN:-true}" = "true" ]; then
    echo "🚀 Iniciando aplicação com Gunicorn..."
    
    # Verificar se Gunicorn está instalado, se não, instalar
    if ! python -c "import gunicorn" 2>/dev/null; then
        echo "⚠️ Gunicorn não encontrado. Instalando..."
        pip install --no-cache-dir gunicorn==21.2.0
    fi
    
    # Configurações do Gunicorn
    WORKERS=${GUNICORN_WORKERS:-3}
    THREADS=${GUNICORN_THREADS:-2}
    TIMEOUT=${GUNICORN_TIMEOUT:-120}
    GRACEFUL_TIMEOUT=${GUNICORN_GRACEFUL_TIMEOUT:-30}
    MAX_REQUESTS=${GUNICORN_MAX_REQUESTS:-1000}
    MAX_REQUESTS_JITTER=${GUNICORN_MAX_REQUESTS_JITTER:-50}
    WORKER_CLASS=${GUNICORN_WORKER_CLASS:-sync}
    BIND=${GUNICORN_BIND:-0.0.0.0:5000}
    
    # Criar diretório de logs se não existir
    mkdir -p /app/logs
    
    # Executar Gunicorn usando python -m para garantir que está no PATH correto
    exec python -m gunicorn \
        --bind "${BIND}" \
        --workers "${WORKERS}" \
        --threads "${THREADS}" \
        --timeout "${TIMEOUT}" \
        --graceful-timeout "${GRACEFUL_TIMEOUT}" \
        --max-requests "${MAX_REQUESTS}" \
        --max-requests-jitter "${MAX_REQUESTS_JITTER}" \
        --worker-class "${WORKER_CLASS}" \
        --worker-connections 1000 \
        --access-logfile - \
        --error-logfile - \
        --log-level "${LOG_LEVEL:-info}" \
        --capture-output \
        --enable-stdio-inheritance \
        --preload \
        --name lhama_banana_flask \
        "app:app"
else
    echo "🔧 Iniciando aplicação com Flask dev server..."
    exec python app.py
fi
