# 🐳 Guia Docker - LhamaBanana

Este projeto usa Docker Compose para gerenciar todos os serviços necessários.

## 📋 Serviços

O `docker-compose.yml` inclui:

1. **PostgreSQL** - Banco de dados
2. **Flask** - Aplicação principal (e-commerce)
3. **Strapi** - Painel administrativo

## 🚀 Início Rápido

### 1. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas configurações
nano .env  # ou use seu editor preferido
```

### 2. Subir Todos os Serviços

```bash
docker compose up -d
```

Isso irá:
- Criar e iniciar todos os containers
- Aplicar o schema do banco de dados automaticamente
- Configurar a rede interna entre serviços

### 3. Verificar Status

```bash
docker compose ps
```

### 4. Ver Logs

```bash
# Todos os serviços
docker compose logs -f

# Apenas Flask
docker compose logs -f flask

# Apenas Strapi
docker compose logs -f strapi

# Apenas PostgreSQL
docker compose logs -f postgres
```

## 🔧 Comandos Úteis

### Parar Serviços

```bash
docker compose stop
```

### Reiniciar Serviços

```bash
docker compose restart
```

### Parar e Remover Containers

```bash
docker compose down
```

### Reconstruir Imagens

```bash
# Reconstruir todas as imagens
docker compose build

# Reconstruir apenas Flask
docker compose build flask

# Reconstruir apenas Strapi
docker compose build strapi
```

### Executar Comandos Dentro dos Containers

```bash
# Flask
docker compose exec flask python manage.py <comando>

# Strapi
docker compose exec strapi npm run <comando>

# PostgreSQL
docker compose exec postgres psql -U postgres -d sistema_usuarios
```

## 🌐 Acessar os Serviços

Após subir os containers:

- **Flask (E-commerce)**: http://localhost:5000
- **Strapi (Admin)**: http://localhost:5000/admin (via proxy reverso do Flask)
- **PostgreSQL**: Apenas acessível internamente via `postgres:5432`

### Acesso Interno aos Serviços

Para acessar serviços internos durante desenvolvimento/testes:

```bash
# Acessar PostgreSQL via container Flask
docker compose exec flask psql -h postgres -U postgres -d sistema_usuarios

# Acessar Strapi via container Flask (curl)
docker compose exec flask curl http://strapi:1337

# Entrar no container Strapi
docker compose exec strapi sh
```

## 📁 Estrutura de Volumes

Os dados são persistidos em:

- **PostgreSQL**: `./db/docker/postgres/data/`
- **Flask Logs**: Volume Docker `flask_logs`
- **Strapi Data**: Volume Docker `strapi_data`
- **Strapi Uploads**: Volume Docker `strapi_uploads`

## 🔄 Desenvolvimento

### Modo Desenvolvimento

O Flask está configurado para modo desenvolvimento por padrão. Para produção:

1. Edite `.env`:
```bash
FLASK_ENV=production
FLASK_DEBUG=0
```

2. Reconstrua e reinicie:
```bash
docker compose build flask
docker compose up -d flask
```

### Hot Reload

O Flask está configurado com hot reload. Alterações no código são refletidas automaticamente.

Para Strapi, em desenvolvimento você pode montar o código como volume (já está configurado).

## 🗄️ Banco de Dados

### Resetar Banco de Dados

```bash
# Parar containers
docker compose down

# Remover volume de dados
docker volume rm lhama_banana_visual_estatica_corrigida_postgres_data
# OU (se usando bind mount)
rm -rf db/docker/postgres/data/*

# Subir novamente (schema será aplicado automaticamente)
docker compose up -d
```

### Backup do Banco

```bash
docker compose exec postgres pg_dump -U postgres sistema_usuarios > backup.sql
```

### Restaurar Backup

```bash
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < backup.sql
```

## 🔍 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker compose logs <nome_do_servico>

# Verificar status
docker compose ps

# Verificar saúde dos serviços
docker compose ps --format json | jq '.[] | {name: .Name, status: .Status, health: .Health}'
```

### Porta já em uso

Se a porta 5000 já estiver em uso:

1. Edite `.env`:
```bash
FLASK_PORT=5001
```

2. Reinicie:
```bash
docker compose up -d
```

**Nota:** O Strapi não expõe porta externa, sendo acessível apenas via proxy reverso do Flask em `/admin` ou internamente via `strapi:1337`.

### Erro de permissão

```bash
# Ajustar permissões do diretório de dados
sudo chown -R $USER:$USER db/docker/postgres/data/
```

### Reconstruir do zero

```bash
# Parar e remover tudo
docker compose down -v

# Remover imagens
docker compose rm -f

# Reconstruir
docker compose build --no-cache
docker compose up -d
```

## 📊 Monitoramento

### Ver uso de recursos

```bash
docker stats
```

### Ver processos dentro dos containers

```bash
docker compose top
```

## 🔐 Segurança

### Produção

Para produção, certifique-se de:

1. Alterar todas as senhas padrão no `.env`
2. Usar `SECRET_KEY` forte e único
3. Configurar `STRAPI_APP_KEYS` e outras chaves de segurança
4. Desabilitar `FLASK_DEBUG=0`
5. Configurar `NODE_ENV=production`
6. Usar HTTPS (configure reverse proxy)

## 🚀 Adicionar Novos Serviços

Para adicionar novos serviços no futuro:

1. Adicione o serviço em `docker-compose.yml`
2. Configure dependências com `depends_on`
3. Adicione à rede `lhama_banana_network`
4. Documente no README

## 📚 Mais Informações

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Strapi Documentation](https://docs.strapi.io/)

