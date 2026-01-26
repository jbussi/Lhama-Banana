# 🚀 Guia de Deploy - LhamaBanana

## 📋 Índice
1. [Docker](#docker)
2. [Nginx](#nginx)
3. [Gunicorn](#gunicorn)
4. [SSL/HTTPS](#sslhttps)
5. [Comandos Úteis](#comandos-úteis)

## 🐳 Docker

### Estrutura
O projeto usa Docker Compose com os seguintes serviços:
- **PostgreSQL**: Banco de dados (porta 5432)
- **Flask**: Aplicação principal (porta 5000)
- **NGINX**: Reverse proxy (portas 80/443)
- **Strapi**: Painel administrativo (porta 1337)
- **Certbot**: Renovação automática de certificados SSL

### Comandos Básicos

```bash
# Subir todos os serviços
docker-compose up -d

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Reconstruir após mudanças
docker-compose up -d --build

# Limpar volumes (CUIDADO: apaga dados!)
docker-compose down -v
```

### Logs Específicos
```bash
# Apenas Flask
docker-compose logs -f flask

# Apenas PostgreSQL
docker-compose logs -f postgres

# Apenas Strapi
docker-compose logs -f strapi
```

### Executar Comandos
```bash
# No container Flask
docker-compose exec flask python scripts/sync_estoque_bling.py

# No PostgreSQL
docker-compose exec postgres psql -U postgres -d sistema_usuarios

# No Strapi
docker-compose exec strapi npm run strapi build
```

## 🌐 Nginx

### Configuração Básica
O Nginx está configurado como proxy reverso:

```nginx
# Flask (porta 5000)
location / {
    proxy_pass http://flask:5000;
}

# Strapi Admin (porta 1337)
location /admin {
    proxy_pass http://strapi:1337/admin;
}
```

### Arquivos de Configuração
- `nginx/nginx.conf` - Configuração principal
- `nginx/ssl.conf` - Configuração SSL (se aplicável)

### Recarregar Nginx
```bash
docker-compose exec nginx nginx -s reload
```

## 🔧 Gunicorn

### Configuração
O Flask roda com Gunicorn em produção.

**Arquivo:** `gunicorn.conf.py`

```python
workers = 4
bind = "0.0.0.0:5000"
timeout = 120
```

### Comandos
```bash
# Iniciar manualmente
gunicorn -c gunicorn.conf.py app:app

# Com configuração customizada
gunicorn -c gunicorn.conf.py --workers 8 app:app
```

## 🔒 SSL/HTTPS

### Usando Certbot (Let's Encrypt)

#### 1. Configurar Nginx para SSL
```nginx
server {
    listen 443 ssl;
    server_name seudominio.com;
    
    ssl_certificate /etc/letsencrypt/live/seudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seudominio.com/privkey.pem;
}
```

#### 2. Obter Certificado
```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seudominio.com -d www.seudominio.com

# Renovação automática (já configurado no cron)
sudo certbot renew
```

#### 3. Renovação Automática
Certbot cria um cron job automaticamente. Verificar:
```bash
sudo crontab -l | grep certbot
```

### Usando Docker com Certbot
```bash
# Script de inicialização
./scripts/certbot-init.sh
```

## 📊 Monitoramento

### Health Check
```bash
# Verificar saúde dos serviços
curl http://localhost:5000/health

# Verificar banco
docker-compose exec postgres pg_isready
```

### Logs
```bash
# Todos os logs
docker-compose logs --tail=100

# Logs com filtro
docker-compose logs flask | grep ERROR

# Salvar logs
docker-compose logs > logs.txt
```

## 🔄 Backup

### Banco de Dados
```bash
# Backup completo
docker-compose exec postgres pg_dump -U postgres sistema_usuarios > backup.sql

# Restaurar
docker-compose exec -T postgres psql -U postgres sistema_usuarios < backup.sql
```

### Volumes Docker
```bash
# Backup volumes
docker run --rm -v lhamabanana_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# Restaurar volumes
docker run --rm -v lhamabanana_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## 🛠️ Comandos Úteis

### Limpeza
```bash
# Remover containers parados
docker-compose rm

# Limpar imagens não utilizadas
docker image prune -a

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes
```

### Debug
```bash
# Entrar no container
docker-compose exec flask bash

# Ver variáveis de ambiente
docker-compose exec flask env

# Testar conexão com banco
docker-compose exec flask python -c "from blueprints.services import get_db; print(get_db())"
```

### Atualização
```bash
# Atualizar código
git pull

# Reconstruir containers
docker-compose up -d --build

# Aplicar migrações (se houver)
docker-compose exec postgres psql -U postgres -d sistema_usuarios -f db/migrate_strapi_changes.sql
```

## ⚠️ Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
docker-compose logs flask

# Verificar variáveis de ambiente
docker-compose config
```

### Erro de conexão com banco
```bash
# Verificar se PostgreSQL está rodando
docker-compose ps postgres

# Testar conexão
docker-compose exec postgres psql -U postgres -c "SELECT 1;"
```

### Porta já em uso
```bash
# Verificar o que está usando a porta
sudo lsof -i :5000

# Parar processo
sudo kill -9 <PID>
```

### Problemas de permissão
```bash
# Ajustar permissões
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

## 🗄️ Banco de Dados

### Estrutura do Banco

O banco de dados está versionado em:
- `db/schema.sql` - Schema completo (executado automaticamente no Docker)
- `db/seeds.sql` - Dados iniciais opcionais
- `db/connection.py` - Módulo de conexão PostgreSQL
- `sql/` - Scripts de migração e atualização

### Onde os dados ficam armazenados?

**Com Docker:**
```
db/docker/postgres/data/
```

Este diretório está no `.gitignore` e não deve ser versionado.

### Scripts SQL Disponíveis

Scripts em `sql/` para migrações e atualizações:

- `fix-strapi-indexes.sql` - Criar índices faltantes do Strapi
- `atualizar-checkout-pagamentos.sql` - Atualizar schema para PagBank
- `tabela_etiquetas.sql` - Criar tabela de etiquetas de frete
- `limpar-registros-orfaos.sql` - Limpar registros órfãos do Strapi
- `seed-example-data.sql` - Popular dados de exemplo (categorias, produtos, etc.)

**Executar script:**
```bash
docker-compose exec -T postgres psql -U postgres -d sistema_usuarios < sql/nome-do-script.sql
```

### Resetar o banco (⚠️ apaga todos os dados)

```bash
# Parar o container
docker-compose down

# Remover o volume de dados
# Windows PowerShell:
Remove-Item -Recurse -Force db\docker\postgres\data\*

# Linux/Mac:
# rm -rf db/docker/postgres/data/*

# Subir novamente (schema.sql será executado automaticamente)
docker-compose up -d
```
