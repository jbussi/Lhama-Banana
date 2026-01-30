#!/bin/sh
# Script de backup automático do PostgreSQL
# Executado via cron no container postgres_backup

set -e

# Configurações
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Criar diretório de backup se não existir
mkdir -p "${BACKUP_DIR}"

# Fazer backup
echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Iniciando backup do PostgreSQL..."
pg_dump -h "${PGHOST}" -p "${PGPORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
    --clean --if-exists --no-owner --no-acl --verbose \
    > "${BACKUP_FILE}" 2>&1

# Verificar se o backup foi bem-sucedido
if [ $? -eq 0 ]; then
    # Comprimir backup
    gzip "${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] ✅ Backup criado com sucesso: ${BACKUP_FILE}"
    
    # Remover backups antigos (manter apenas os últimos N dias)
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Removendo backups mais antigos que ${RETENTION_DAYS} dias..."
    find "${BACKUP_DIR}" -name "backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
    
    # Listar backups restantes
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Backups disponíveis:"
    ls -lh "${BACKUP_DIR}"/backup_*.sql.gz 2>/dev/null || echo "  (nenhum backup encontrado)"
else
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] ❌ Erro ao criar backup!"
    exit 1
fi
