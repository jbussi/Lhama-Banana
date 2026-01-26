"""
Configuração do Gunicorn para LhamaBanana
==========================================

Este arquivo pode ser usado como alternativa ao entrypoint.sh
para configurações mais complexas do Gunicorn.
"""

import multiprocessing
import os

# Bind address
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:5000')

# Workers
workers = int(os.getenv('GUNICORN_WORKERS', 3))

# Threads por worker
threads = int(os.getenv('GUNICORN_THREADS', 2))

# Worker class
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')

# Timeouts
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', 30))
keepalive = 5

# Max requests (para prevenir memory leaks)
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 50))

# Worker connections (para async workers)
worker_connections = 1000

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'lhama_banana_flask'

# Preload app (melhor performance, mas menos flexível)
preload_app = True

# Capture output
capture_output = True
enable_stdio_inheritance = True

# User/Group (se necessário)
# user = 'www-data'
# group = 'www-data'

# Umask (se necessário)
# umask = 0o007

# SSL (se necessário)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

def when_ready(server):
    """Callback quando o servidor está pronto"""
    server.log.info("🚀 Gunicorn iniciado com sucesso!")
    server.log.info(f"   Workers: {workers}")
    server.log.info(f"   Threads por worker: {threads}")
    server.log.info(f"   Worker class: {worker_class}")
    server.log.info(f"   Bind: {bind}")

def on_exit(server):
    """Callback quando o servidor está saindo"""
    server.log.info("👋 Gunicorn encerrando...")

def worker_int(worker):
    """Callback quando um worker recebe SIGINT ou SIGQUIT"""
    worker.log.info("⚠️ Worker recebeu sinal de interrupção")

def worker_abort(worker):
    """Callback quando um worker recebe SIGABRT"""
    worker.log.warning("⚠️ Worker recebeu sinal de abort")
