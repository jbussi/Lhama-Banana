# Estrutura de Banco de Dados

Este diretório contém a estrutura versionada do banco de dados do projeto Lhama Banana.

## Estrutura

```
db/
├── __init__.py          # Módulo Python para importação
├── connection.py        # Serviço de conexão PostgreSQL via psycopg2
├── schema.sql           # Definição completa do schema do banco
├── seeds.sql            # Dados iniciais (opcional)
├── docker/
│   └── postgres/
│       └── data/       # Dados persistentes do PostgreSQL (não versionado)
└── README.md            # Esta documentação
```

## 🐳 Executando o PostgreSQL com Docker

O projeto usa Docker Compose para rodar o PostgreSQL localmente como serviço.

### Subir o banco de dados

Na raiz do projeto (`Lhama-Banana/`), execute:

```bash
docker compose up -d
```

Isso irá:
- Criar e iniciar o container PostgreSQL
- Executar automaticamente o `schema.sql` na primeira inicialização
- Executar automaticamente o `seeds.sql` (se houver dados)
- Criar o volume persistente em `db/docker/postgres/data/`

### Verificar status

```bash
docker compose ps
```

### Ver logs

```bash
docker compose logs postgres
```

### Parar o banco

```bash
docker compose stop
```

### Reiniciar o banco

```bash
docker compose restart postgres
```

### Resetar o banco (⚠️ apaga todos os dados)

Se você precisar recriar o banco do zero:

```bash
# Parar o container
docker compose down

# Remover o volume de dados (apaga todos os dados!)
# No Windows PowerShell:
Remove-Item -Recurse -Force db\docker\postgres\data\*

# No Linux/Mac:
# rm -rf db/docker/postgres/data/*

# Subir novamente (schema.sql será executado automaticamente)
docker compose up -d
```

### Onde os dados ficam armazenados?

Os dados do PostgreSQL são persistidos em:
```
db/docker/postgres/data/
```

Este diretório está no `.gitignore` e **não deve ser versionado**.

## Arquivos

### `schema.sql`
Contém a definição completa do banco de dados, incluindo:
- Todas as tabelas (usuarios, produtos, vendas, pagamentos, etc.)
- Índices para otimização
- Funções e triggers
- Constraints e relacionamentos

**Execução automática:** Este arquivo é executado automaticamente na primeira inicialização do container Docker.

**Execução manual (se necessário):**
```bash
docker compose exec postgres psql -U postgres -d sistema_usuarios -f /docker-entrypoint-initdb.d/01_schema.sql
```

### `seeds.sql`
Dados iniciais opcionais para popular o banco de dados com informações de exemplo.
Atualmente vazio, pode ser preenchido conforme necessário.

**Execução automática:** Este arquivo é executado automaticamente na primeira inicialização do container Docker (após o schema.sql).

**Execução manual (se necessário):**
```bash
docker compose exec postgres psql -U postgres -d sistema_usuarios -f /docker-entrypoint-initdb.d/02_seeds.sql
```

### `connection.py`
Módulo Python que fornece uma interface reutilizável para conexões com o banco de dados.

**Funcionalidades:**
- Pool de conexões com psycopg2
- Gerenciamento automático de conexões por requisição (Flask)
- Tratamento de erros e rollback automático

**Uso básico:**
```python
from db.connection import init_db_pool, get_db, close_db_connection
from config import Config

# Na inicialização da aplicação
init_db_pool(Config.DATABASE_CONFIG)

# Em rotas/views
conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT * FROM usuarios")
result = cursor.fetchall()
```

## Como o Flask se conecta ao banco

O Flask usa o módulo `db/connection.py` (ou `blueprints/services/db.py`) que se conecta ao PostgreSQL usando psycopg2.

**Configuração padrão** (em `config.py`):
- Host: `localhost` (ou `127.0.0.1`)
- Porta: `5432` (exposta pelo Docker)
- Banco: `sistema_usuarios`
- Usuário: `postgres`
- Senha: `far111111` (ou via variável de ambiente `DB_PASSWORD`)

**Variáveis de ambiente** (opcional):
Você pode sobrescrever as configurações usando variáveis de ambiente:
```bash
export DB_HOST=localhost
export DB_NAME=sistema_usuarios
export DB_USER=postgres
export DB_PASSWORD=sua_senha_aqui
```

**Conexão no código:**
```python
from config import Config
from db.connection import init_db_pool, get_db

# Na inicialização da aplicação
init_db_pool(Config.DATABASE_CONFIG)

# Em rotas/views
conn = get_db()
cursor = conn.cursor()
cursor.execute("SELECT * FROM usuarios")
result = cursor.fetchall()
```

## Compatibilidade

Este módulo é compatível com o código existente que usa `blueprints/services/db.py`.
A estrutura foi criada para facilitar a migração gradual, se necessário.

## Backup e Restauração

### Fazer backup do banco

```bash
docker compose exec postgres pg_dump -U postgres sistema_usuarios > backup.sql
```

### Restaurar backup

```bash
docker compose exec -T postgres psql -U postgres -d sistema_usuarios < backup.sql
```

## Migração do Schema

O schema usa `CREATE TABLE IF NOT EXISTS`, então é seguro executar múltiplas vezes.

**Nota:** Alterações estruturais (como adicionar colunas) podem exigir scripts de migração específicos, pois o `IF NOT EXISTS` não aplica alterações em tabelas existentes.

## Próximos Passos

- [ ] Definir o banco de dados completo para o painel de administração no Strapi
- [ ] Criar scripts de migração versionados (se necessário)
- [ ] Adicionar dados iniciais em `seeds.sql` (se necessário)

