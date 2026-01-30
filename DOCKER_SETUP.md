# 🐳 Docker Compose - Setup Completo

Este documento descreve a configuração completa do Docker Compose para o projeto Lhama Banana, incluindo todas as funcionalidades de produção.

## 📋 Requisitos

- Docker Engine 24.0+ ou Docker Desktop
- Docker Compose 2.20+
- 4GB RAM mínimo (8GB recomendado)
- 20GB espaço em disco

## 🚀 Primeira Execução

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp env.example .env

# Editar com suas configurações
nano .env  # ou use seu editor preferido
```

**Variáveis obrigatórias:**
- `SECRET_KEY`: Chave secreta do Flask (gere uma aleatória)
- `DB_PASSWORD`: Senha do PostgreSQL
- `FIREBASE_SERVICE_ACCOUNT_JSON`: JSON completo do Firebase (ou configure `KEY_JSON_PATH`)
- `CERTBOT_EMAIL`: Email para certificados SSL
- `CERTBOT_DOMAIN`: Domínio principal

### 2. Tornar Scripts Executáveis

```bash
chmod +x scripts/*.sh
```

### 3. Inicializar Banco de Dados

```bash
# Subir apenas PostgreSQL primeiro
docker compose up -d postgres

# Aguardar PostgreSQL estar pronto (30 segundos)
sleep 30

# Inicializar schema do banco
./scripts/init-database.sh
```

### 4. Iniciar Todos os Serviços

```bash
# Subir todos os serviços
docker compose up -d

# Verificar status
docker compose ps

# Ver logs
docker compose logs -f
```

## 📦 Estrutura de Serviços

### 1. PostgreSQL (postgres)
- **Imagem**: `postgres:16.11-alpine`
- **Porta interna**: 5432
- **Volumes**: `postgres_data`, `postgres_backups`
- **Healthcheck**: Verifica `pg_isready` e conexão
- **Configurações**: Otimizado para performance (256MB shared_buffers, 1GB cache)

### 2. PostgreSQL Backup (postgres_backup)
- **Imagem**: `postgres:16.11-alpine`
- **Função**: Backup automático via cron
- **Agendamento**: Configurável via `BACKUP_SCHEDULE` (padrão: diário às 2h)
- **Retenção**: Configurável via `BACKUP_RETENTION_DAYS` (padrão: 7 dias)
- **Localização**: Volume `postgres_backups`

### 3. Flask (flask)
- **Imagem**: `lhama_banana_flask:latest` (build local)
- **Porta interna**: 5000
- **Workers**: 4 (configurável via `GUNICORN_WORKERS`)
- **Threads**: 2 por worker
- **Logs**: JSON estruturado
- **Healthcheck**: Verifica conexão na porta 5000
- **Volumes**: `flask_logs`, `flask_cache`

### 4. Strapi (strapi)
- **Imagem**: `lhama_banana_strapi:latest` (build local)
- **Porta interna**: 1337
- **Migrações**: **DESABILITADAS** (`AUTO_MIGRATE=false`)
- **Schema**: Pré-criado via SQL antes do Strapi iniciar
- **Healthcheck**: Verifica endpoint `/_health`
- **Volumes**: `strapi_data`, `strapi_uploads`, `strapi_cache`

### 5. Nginx (nginx)
- **Imagem**: `lhama_banana_nginx:latest` (build local)
- **Portas**: 80 (HTTP), 443 (HTTPS)
- **Funcionalidades**:
  - SSL/TLS via Certbot
  - Headers de segurança (HSTS, CSP, X-Frame-Options, etc.)
  - Rate limiting por zona (API, Admin, Geral)
  - Logs formatados
  - Cache de arquivos estáticos
- **Volumes**: `nginx_logs`, `nginx_cache`, `certbot_www`, `certbot_conf`

### 6. Certbot (certbot)
- **Imagem**: `certbot/certbot:v2.9.0`
- **Função**: Renovação automática de certificados SSL
- **Agendamento**: A cada 12 horas
- **Deploy hook**: Recarrega Nginx após renovação

## 🔒 Segurança

### Headers de Segurança (Nginx)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy`: Configurado para permitir apenas recursos necessários
- `Strict-Transport-Security`: HSTS habilitado (max-age=31536000)

### Rate Limiting (Nginx)
- **API**: 10 req/s (burst: 20)
- **Admin**: 2 req/s (burst: 5) - Proteção contra brute force
- **Geral**: 30 req/s (burst: 50)

### PostgreSQL
- Usuário com permissões restritas
- Schema pré-criado via SQL (não via Strapi)
- Logs de todas as queries habilitados

## 📊 Logging

Todos os serviços usam `json-file` driver com:
- **max-size**: 10m por arquivo
- **max-file**: 3-5 arquivos (dependendo do serviço)
- **labels**: Identificação por serviço

### Ver Logs

```bash
# Todos os serviços
docker compose logs -f

# Serviço específico
docker compose logs -f flask
docker compose logs -f postgres
docker compose logs -f nginx
docker compose logs -f strapi

# Últimas 100 linhas
docker compose logs --tail=100 flask
```

## 🔄 Backup e Restauração

### Backup Automático
O backup é executado automaticamente via cron no container `postgres_backup`.

### Backup Manual

```bash
# Fazer backup manual
docker compose exec postgres_backup /backup-postgres.sh

# Listar backups
docker compose exec postgres_backup ls -lh /backups
```

### Restaurar Backup

```bash
# Parar serviços
docker compose down

# Restaurar do backup
docker compose up -d postgres
sleep 30
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < backup_completo.sql

# Reiniciar serviços
docker compose up -d
```

## 🛠️ Desenvolvimento

### Habilitar Modo Desenvolvimento

No `.env`, descomente:
```bash
DEV_MODE=true
KEY_JSON_PATH=./key.json
```

Isso habilita:
- Bind mounts para hot reload (`blueprints/`, `templates/`, `strapi-admin/src/`)
- Acesso direto ao `key.json` da raiz

### Rebuild de Imagens

```bash
# Rebuild específico
docker compose build flask
docker compose build strapi
docker compose build nginx

# Rebuild tudo
docker compose build --no-cache

# Rebuild e restart
docker compose up -d --build
```

## 📈 Monitoramento

### Health Checks

```bash
# Verificar saúde de todos os serviços
docker compose ps

# Verificar logs de healthcheck
docker compose logs | grep -i health
```

### Recursos

Limites configurados:
- **Flask**: 2 CPUs, 2GB RAM (reserva: 0.5 CPU, 512MB)
- **Strapi**: 2 CPUs, 2GB RAM (reserva: 0.5 CPU, 512MB)
- **PostgreSQL**: Sem limites (usa recursos do host)

## 🔧 Comandos Úteis

```bash
# Parar todos os serviços
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados!)
docker compose down -v

# Reiniciar serviço específico
docker compose restart flask

# Executar comando em container
docker compose exec flask python manage.py migrate
docker compose exec postgres psql -U postgres -d sistema_usuarios

# Ver uso de recursos
docker stats

# Limpar sistema Docker
docker system prune -a
```

## 🐛 Troubleshooting

### PostgreSQL não inicia
```bash
# Verificar logs
docker compose logs postgres

# Verificar permissões de volume
docker compose exec postgres ls -la /var/lib/postgresql/data
```

### Strapi com erro de migração
```bash
# Verificar se AUTO_MIGRATE=false
docker compose exec strapi env | grep AUTO_MIGRATE

# Verificar schema do banco
docker compose exec postgres psql -U postgres -d sistema_usuarios -c "\dt"
```

### Nginx não carrega certificados
```bash
# Verificar certificados
docker compose exec nginx ls -la /etc/letsencrypt/live/

# Testar configuração
docker compose exec nginx nginx -t

# Recarregar configuração
docker compose exec nginx nginx -s reload
```

### Flask não responde
```bash
# Verificar logs
docker compose logs flask

# Verificar healthcheck
docker compose exec flask curl http://localhost:5000/health

# Verificar workers Gunicorn
docker compose exec flask ps aux | grep gunicorn
```

## 📝 Notas Importantes

1. **Migrações Strapi**: Sempre desabilitadas. O schema deve ser pré-criado via SQL.
2. **Backup**: Configure `BACKUP_SCHEDULE` e `BACKUP_RETENTION_DAYS` conforme necessário.
3. **SSL**: Certificados são renovados automaticamente a cada 12 horas.
4. **Logs**: Rotacionam automaticamente (10MB por arquivo, 3-5 arquivos).
5. **Volumes**: Dados são persistentes. Use `docker compose down -v` apenas se quiser apagar tudo.

## 🔗 Referências

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Strapi Documentation](https://docs.strapi.io/)
