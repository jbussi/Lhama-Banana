# 📊 Metabase - Analytics e Dashboards

## 📋 Visão Geral

O Metabase é uma ferramenta de Business Intelligence (BI) integrada ao projeto LhamaBanana para criação de dashboards e análises de dados. Ele utiliza o mesmo banco PostgreSQL do sistema, garantindo acesso em tempo real aos dados do e-commerce.

## 🔒 Segurança

### Acesso Protegido

O Metabase **não é público** e está protegido da seguinte forma:

1. **Sem exposição direta**: A porta 3000 do Metabase não está exposta externamente
2. **Proxy reverso via Flask**: Acesso apenas através de `/analytics` no Flask
3. **Autenticação admin obrigatória**: Usa o mesmo sistema de autenticação do Strapi (`admin_required_email`)
4. **Rede interna Docker**: Comunicação apenas dentro da rede interna do Docker

### Como Funciona

```
Usuário → http://localhost:5000/analytics → Flask (verifica admin) → Metabase (porta 3000 interna)
```

Apenas usuários com:
- Email na lista `ADMIN_EMAILS` OU
- Role `admin` no banco de dados

Podem acessar o Metabase.

## 🚀 Como Subir o Metabase

### ⚠️ IMPORTANTE: Criar Banco "metabase" Primeiro

Antes de subir o Metabase, certifique-se de que o banco "metabase" existe:

**Windows (PowerShell)**:
```powershell
.\scripts\fix-all.ps1
```

**Linux/Mac**:
```bash
chmod +x scripts/fix-all.sh
./scripts/fix-all.sh
```

**Ou manualmente**:
```bash
docker compose up -d postgres
# Aguarde ~10 segundos
docker compose exec postgres psql -U postgres -c "CREATE DATABASE metabase;"
docker compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;"
```

### 1. Subir todos os serviços

```bash
docker compose up -d
```

Isso irá subir:
- PostgreSQL
- Flask
- Strapi
- **Metabase** (novo)

### 2. Aguardar inicialização

O Metabase leva aproximadamente 90 segundos para inicializar na primeira vez. Você pode verificar o status:

```bash
docker compose logs -f metabase
```

Aguarde até ver mensagens como:
```
Metabase initialization complete
```

**Se ver erros de "database metabase does not exist"**, execute o script de correção acima.

### 3. Acessar o Metabase

1. **Faça login no Flask** como admin:
   - Acesse: `http://localhost:5000`
   - Faça login com email admin

2. **Acesse o Metabase**:
   - URL: `http://localhost:5000/analytics`
   - Você será redirecionado automaticamente para o Metabase

## ⚙️ Configuração Inicial do Metabase

### Primeira Configuração

Na primeira vez que acessar o Metabase, você precisará:

1. **Criar conta de administrador**:
   - Nome completo
   - Email (use o mesmo email admin do Flask)
   - Senha (crie uma senha forte)

2. **Configurar conexão com o banco**:
   - O Metabase já está configurado para usar o PostgreSQL
   - Mas você precisará adicionar a conexão com o banco de dados do sistema

### Adicionar Conexão com PostgreSQL

1. No Metabase, vá em **Settings** → **Admin** → **Databases**
2. Clique em **Add database**
3. Selecione **PostgreSQL**
4. Preencha:
   - **Name**: `LhamaBanana DB`
   - **Host**: `postgres` (nome do serviço Docker)
   - **Port**: `5432`
   - **Database name**: `sistema_usuarios` (ou o valor de `DB_NAME`)
   - **Username**: `postgres` (ou o valor de `DB_USER`)
   - **Password**: `far111111` (ou o valor de `DB_PASSWORD`)
   - **Database name**: `sistema_usuarios`

5. **Importante**: Marque a opção **"Use a secure connection (SSL)"** como **desabilitada** (já que é conexão interna)

6. Clique em **Save**

### Configurações Recomendadas

Após criar a conexão, configure:

1. **Sincronização automática**:
   - Vá em **Settings** → **Admin** → **Databases** → Selecione o banco
   - Configure **Synchronization schedule** para atualizar automaticamente

2. **Cache**:
   - Configure cache para queries frequentes
   - Vá em **Settings** → **Admin** → **Settings** → **Caching**

## 📊 Criando Dashboards

### Estrutura de Dados

O banco `sistema_usuarios` contém as seguintes tabelas principais:

- **vendas**: Pedidos e vendas
- **produtos**: Catálogo de produtos
- **usuarios**: Usuários do sistema
- **cupons**: Cupons de desconto
- **etiqueta_fretes**: Etiquetas de frete
- **pagamentos**: Status de pagamentos
- **itens_venda**: Itens de cada venda

### Dashboards Sugeridos

#### 1. Dashboard de Vendas

**Métricas principais:**
- Total de vendas (contador)
- Receita total (soma)
- Ticket médio (média)
- Vendas por período (gráfico de linha)

**Queries sugeridas:**
```sql
-- Total de vendas
SELECT COUNT(*) FROM vendas;

-- Receita total
SELECT SUM(valor_total) FROM vendas;

-- Vendas por dia
SELECT DATE(data_criacao) as dia, COUNT(*) as vendas
FROM vendas
GROUP BY DATE(data_criacao)
ORDER BY dia DESC;
```

#### 2. Dashboard de Produtos

**Métricas principais:**
- Produtos mais vendidos (tabela)
- Estoque atual vs mínimo (gráfico de barras)
- Produtos com estoque baixo (alerta)

**Queries sugeridas:**
```sql
-- Produtos mais vendidos
SELECT p.nome, SUM(iv.quantidade) as total_vendido
FROM itens_venda iv
JOIN produtos p ON iv.produto_id = p.id
GROUP BY p.id, p.nome
ORDER BY total_vendido DESC
LIMIT 10;

-- Produtos com estoque baixo
SELECT nome, estoque, estoque_minimo
FROM produtos
WHERE estoque <= estoque_minimo;
```

#### 3. Dashboard de Pagamentos

**Métricas principais:**
- Status de pagamentos (gráfico de pizza)
- Métodos de pagamento (gráfico de barras)
- Taxa de conversão (pagos vs pendentes)

#### 4. Dashboard de Frete

**Métricas principais:**
- Total de etiquetas geradas
- Status de envios
- Custo total de frete

### Como Criar um Dashboard

1. **Criar uma pergunta (Question)**:
   - Clique em **+ New** → **Question**
   - Selecione o banco de dados
   - Escolha a tabela
   - Configure a visualização (tabela, gráfico, etc.)
   - Salve a pergunta

2. **Criar um Dashboard**:
   - Clique em **+ New** → **Dashboard**
   - Dê um nome ao dashboard
   - Adicione perguntas salvas
   - Organize os cards
   - Configure atualização automática (opcional)

3. **Compartilhar Dashboard**:
   - Clique em **Sharing** no dashboard
   - Configure permissões
   - Gere link público (se necessário, mas cuidado com segurança)

## 🔧 Configuração Avançada

### Variáveis de Ambiente

O Metabase pode ser configurado via variáveis de ambiente no `docker-compose.yml`:

```yaml
environment:
  # Banco de dados do Metabase (interno)
  MB_DB_TYPE: postgres
  MB_DB_DBNAME: metabase
  MB_DB_PORT: 5432
  MB_DB_USER: postgres
  MB_DB_PASS: far111111
  MB_DB_HOST: postgres
  
  # Configurações gerais
  MB_SITE_NAME: "LhamaBanana Analytics"
  MB_SITE_LOCALE: pt_BR
  MB_TIMEZONE: America/Sao_Paulo
  MB_SITE_URL: http://localhost:5000/analytics
```

### Persistência de Dados

Os dados do Metabase (configurações, dashboards, etc.) são armazenados em:

```
./metabase/data
```

Este volume é persistente e mantém todas as configurações mesmo após reiniciar o container.

### Backup

Para fazer backup do Metabase:

```bash
# Backup do volume
docker run --rm -v lhama_banana_metabase_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/metabase-backup-$(date +%Y%m%d).tar.gz /data
```

## 🐛 Troubleshooting

### ⚡ Erro: "database metabase does not exist" (Correção Rápida)

Se você ver este erro:
```
FATAL: database "metabase" does not exist
```

**Solução Rápida** (1 comando):

**Windows (PowerShell)**:
```powershell
.\scripts\fix-all.ps1
```

**Linux/Mac**:
```bash
chmod +x scripts/fix-all.sh
./scripts/fix-all.sh
```

**Ou manualmente**:
```bash
# 1. Verificar se PostgreSQL está rodando
docker compose ps postgres

# 2. Se não estiver, subir
docker compose up -d postgres
# Aguarde ~10 segundos

# 3. Criar banco
docker compose exec postgres psql -U postgres -c "CREATE DATABASE metabase;"
docker compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;"

# 4. Reiniciar Metabase
docker compose restart metabase
```

Veja também: `QUICK_FIX_METABASE.md` para instruções detalhadas.

### Metabase não inicia

1. **Verificar logs**:
   ```bash
   docker compose logs metabase
   ```

2. **Verificar se PostgreSQL está saudável**:
   ```bash
   docker compose ps postgres
   ```

3. **Verificar se o banco "metabase" existe**:
   ```bash
   docker compose exec postgres psql -U postgres -l | grep metabase
   ```

4. **Se não existir, criar o banco**:
   ```bash
   docker compose exec -T postgres psql -U postgres < sql/create-metabase-db.sql
   ```

5. **Verificar conectividade**:
   ```bash
   docker compose exec metabase ping postgres
   ```

### Erro 502 ao acessar /analytics

1. **Verificar se Metabase está rodando**:
   ```bash
   docker compose ps metabase
   ```

2. **Verificar se está autenticado como admin**:
   - Faça login no Flask primeiro
   - Verifique se seu email está em `ADMIN_EMAILS`

3. **Verificar logs do Flask**:
   ```bash
   docker compose logs flask | grep metabase
   ```

### Metabase lento

1. **Aumentar recursos**:
   - Edite `docker-compose.yml` e adicione limites de memória
   - Reinicie: `docker compose restart metabase`

2. **Configurar cache**:
   - No Metabase: Settings → Admin → Settings → Caching
   - Configure cache para queries frequentes

### Esquecer senha do Metabase

1. **Reset via banco de dados**:
   ```bash
   docker compose exec postgres psql -U postgres -d metabase
   ```
   
   ```sql
   -- Ver usuários
   SELECT id, email FROM core_user;
   
   -- Resetar senha (hash para 'password123')
   UPDATE core_user 
   SET password = '$2a$10$...' 
   WHERE email = 'seu-email@exemplo.com';
   ```

   Ou simplesmente recrie o container (perderá configurações):
   ```bash
   docker compose down metabase
   docker volume rm lhama_banana_metabase_data
   docker compose up -d metabase
   ```

## 📁 Arquivos de Referência

O projeto inclui arquivos prontos para facilitar a criação de dashboards:

### 1. `metabase/queries.sql`
Arquivo com **todas as queries SQL prontas** organizadas por dashboard:
- ✅ Dashboard de Vendas (8 queries)
- ✅ Dashboard de Produtos (6 queries)
- ✅ Dashboard de Pagamentos (6 queries)
- ✅ Dashboard de Frete (6 queries)
- ✅ Dashboard de Cupons (5 queries)
- ✅ Dashboard de Usuários (5 queries)
- ✅ Métricas Operacionais (5 queries)
- ✅ Visão Geral (3 queries)

**Total: 44 queries prontas para uso!**

### 2. `metabase/DASHBOARDS_GUIDE.md`
Guia completo passo a passo para criar todos os dashboards:
- Instruções detalhadas para cada métrica
- Tipos de visualização recomendados
- Configurações de cores e filtros
- Dicas de customização

### 3. `metabase/setup_connection.sql`
Script SQL para testar a conexão e verificar estrutura do banco antes de configurar no Metabase.

## 🚀 Início Rápido

### Passo 1: Configurar Conexão
1. Acesse `http://localhost:5000/analytics`
2. Faça login como admin
3. Vá em **Settings** → **Admin** → **Databases**
4. Adicione PostgreSQL com:
   - Host: `postgres`
   - Database: `sistema_usuarios`
   - User: `postgres`
   - Password: `far111111`

### Passo 2: Criar Dashboards
1. Abra o arquivo `metabase/DASHBOARDS_GUIDE.md`
2. Siga as instruções para cada dashboard
3. Use as queries do arquivo `metabase/queries.sql`
4. Copie e cole as queries diretamente no Metabase

### Passo 3: Personalizar
- Ajuste cores e visualizações conforme necessário
- Configure filtros de data
- Configure atualização automática

## 📚 Recursos Adicionais

### Documentação Oficial

- [Metabase Documentation](https://www.metabase.com/docs/)
- [Metabase SQL Guide](https://www.metabase.com/docs/latest/questions/native-editor/sql-parameters)
- [Metabase Dashboard Guide](https://www.metabase.com/docs/latest/dashboards/introduction)

### Boas Práticas

1. **Performance**:
   - Use índices no banco de dados para queries frequentes
   - Configure cache para dashboards pesados
   - Evite queries que escaneiam tabelas inteiras

2. **Segurança**:
   - Não compartilhe links públicos sem necessidade
   - Use permissões adequadas nos dashboards
   - Revise queries SQL antes de executar

3. **Manutenção**:
   - Faça backup regular do volume do Metabase
   - Monitore uso de recursos
   - Atualize a imagem Docker periodicamente

## 🔄 Atualização

Para atualizar o Metabase:

```bash
# Parar o serviço
docker compose stop metabase

# Atualizar imagem
docker compose pull metabase

# Reiniciar
docker compose up -d metabase
```

## 📝 Notas Importantes

1. **Banco de dados compartilhado**: O Metabase usa o mesmo PostgreSQL, mas cria seu próprio banco (`metabase`) para armazenar configurações internas.

2. **Acesso ao banco**: O Metabase precisa de acesso de leitura ao banco `sistema_usuarios`. Em produção, considere criar um usuário PostgreSQL específico com permissões apenas de leitura.

3. **Performance**: Queries complexas podem impactar o banco de dados. Configure limites e cache adequadamente.

4. **Backup**: Sempre faça backup do volume `metabase_data` antes de atualizações importantes.

## 🔧 Troubleshooting

### Erro: "database metabase does not exist"

**Problema**: O Metabase não consegue conectar ao banco de dados interno.

**Solução Rápida (1 comando)**:

**Windows (PowerShell)**:
```powershell
.\scripts\fix-all.ps1
```

**Linux/Mac**:
```bash
chmod +x scripts/fix-all.sh
./scripts/fix-all.sh
```

O script irá:
1. ✅ Verificar se PostgreSQL está rodando
2. ✅ Criar o banco "metabase" se não existir
3. ✅ Reiniciar o Metabase

**Solução Manual (3 passos)**:

1. **Subir o PostgreSQL**:
   ```bash
   docker compose up -d postgres
   ```
   Aguarde ~10 segundos.

2. **Criar o Banco**:
   ```bash
   docker compose exec postgres psql -U postgres -c "CREATE DATABASE metabase;"
   docker compose exec postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;"
   ```

3. **Reiniciar Metabase**:
   ```bash
   docker compose restart metabase
   ```
   Aguarde ~90 segundos.

**Verificação**:
```bash
# Verificar se o banco existe
docker compose exec postgres psql -U postgres -l | grep metabase

# Verificar logs do Metabase
docker compose logs metabase --tail 20
```

### Erro: Metabase não inicia

**Verificar logs**:
```bash
docker compose logs metabase
```

**Possíveis causas**:
- Banco "metabase" não existe (veja solução acima)
- PostgreSQL não está saudável
- Porta 3000 já está em uso

**Solução**:
```bash
# Verificar saúde do PostgreSQL
docker compose ps postgres

# Verificar porta 3000
netstat -an | grep 3000  # Linux/Mac
netstat -an | findstr 3000  # Windows
```

### Erro: Não consigo acessar o Metabase

**Desenvolvimento (porta 3000 exposta)**:
- Acesse: `http://localhost:3000`
- Certifique-se de que a porta está exposta no `docker-compose.yml`

**Produção (via proxy Flask)**:
- Faça login como admin: `http://localhost:5000/admin`
- Acesse: `http://localhost:5000/analytics`
- Verifique se o decorador `@admin_required_email` está funcionando

## 🎯 Próximos Passos

1. ✅ Metabase integrado e funcionando
2. ⏳ Criar dashboards iniciais
3. ⏳ Configurar sincronização automática
4. ⏳ Configurar alertas (opcional)
5. ⏳ Documentar queries específicas do projeto

---

**Última atualização**: 2024
**Versão do Metabase**: Latest (via Docker Hub)

