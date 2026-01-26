# 🦙 LhamaBanana - E-commerce Platform

Uma plataforma de e-commerce moderna construída com Flask, PostgreSQL e Firebase.

## 🚀 Funcionalidades Implementadas

### ✅ Sistema de Checkout Completo
- **Processamento de Pedidos** com validação de estoque
- **Integração PagBank** (PIX, Cartão de Crédito, Boleto)
- **Cálculo de Frete** em tempo real via Melhor Envio
- **Páginas de Pagamento** dedicadas (PIX, Boleto)
- **Status de Pedidos** com atualização automática
- **Webhook** para atualização de status de pagamento

### ✅ Sistema de Frete Inteligente
- **Validação de CEP** via ViaCEP
- **Múltiplas Modalidades**: PAC, SEDEX, Frete Grátis
- **Cálculo Dinâmico** baseado em peso, distância e valor

### ✅ Autenticação e Usuários
- **Firebase Authentication** integrado
- **Sistema de Perfis** de usuário
- **Carrinho Persistente** por sessão

## 🛠️ Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Banco de Dados**: PostgreSQL
- **Autenticação**: Firebase Admin SDK
- **Pagamentos**: PagBank API (PagSeguro)
- **Frontend**: HTML5, CSS3, JavaScript
- **Frete**: Melhor Envio API

## ⚠️ Requisitos de Infraestrutura

### Sincronização de Relógio (NTP)

**IMPORTANTE**: O servidor de produção **DEVE** ter o relógio sincronizado via NTP/Chrony para evitar erros de "clock skew" com tokens do Firebase.

O sistema implementa retry automático para diferenças pequenas (< 2s), mas para garantir a melhor experiência:

1. **Em produção**: Configure NTP no host ou use um serviço de sincronização de tempo
2. **No Docker**: O Dockerfile já inclui o pacote `ntp`, mas você deve garantir que o host esteja sincronizado
3. **Verificação**: Use `ntpdate -q pool.ntp.org` ou `chrony sources` para verificar a sincronização

**Nota**: O sistema detecta automaticamente clock skew e faz retry silencioso. Se a diferença for >= 2s, o frontend faz refresh automático do token.

## 📦 Instalação

### 1. Clonar o Repositório
```bash
git clone <seu-repositorio>
cd LhamaBanana_visual_estatica_corrigida/Lhama-Banana
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar o Sistema

Edite o arquivo `config.py` com suas configurações:

```python
# Banco de Dados
DATABASE_CONFIG = {
    "host": "localhost",
    "dbname": "sistema_usuarios",
    "user": "postgres",
    "password": "sua_senha"
}

# PagBank
PAGBANK_API_TOKEN = "seu-token-aqui"
PAGBANK_ENVIRONMENT = "sandbox"  # ou "production"
PAGBANK_NOTIFICATION_URL = "http://localhost:5000/api/webhook/pagbank"

# Melhor Envio
MELHOR_ENVIO_TOKEN = "seu-token-aqui"
MELHOR_ENVIO_CEP_ORIGEM = "13219-052"
```

**Ou use variáveis de ambiente:**
```bash
# Windows PowerShell
$env:DB_PASSWORD="sua_senha"
$env:PAGBANK_API_TOKEN="seu-token"
$env:PAGBANK_ENVIRONMENT="sandbox"

# Linux/Mac
export DB_PASSWORD="sua_senha"
export PAGBANK_API_TOKEN="seu-token"
export PAGBANK_ENVIRONMENT="sandbox"
```

### 4. Configurar Firebase
- Coloque o arquivo `key.json` na raiz do projeto (mesmo nível de `Lhama-Banana/`)
- Configure as credenciais do Firebase

### 5. Configurar Banco de Dados

#### Opção 1: Usando Docker (Recomendado)
```bash
# Subir o PostgreSQL com Docker
docker compose up -d

# O schema será aplicado automaticamente na primeira inicialização
```

#### Opção 2: Manual
```bash
# Aplicar o schema completo
psql -U postgres -d sistema_usuarios -f db/schema.sql
```

**Nota:** O schema está consolidado em `db/schema.sql` e inclui todas as tabelas, índices, triggers e funções necessárias.

## 🚀 Execução

### Usando Docker (Recomendado)

O projeto usa Docker Compose para gerenciar todos os serviços.

#### 1. Configurar Variáveis de Ambiente

**Windows (PowerShell):**
```powershell
Copy-Item env.example .env
```

**Linux/Mac:**
```bash
cp env.example .env
```

**Ou use o script:**
- Windows: `.\setup-env.ps1`
- Linux/Mac: `./setup-env.sh`

O arquivo `.env` já vem pré-configurado com valores funcionais. Você pode ajustar se necessário.

**📚 Para mais informações sobre configuração, consulte [CONFIGURACAO.md](CONFIGURACAO.md)**

#### 2. Subir Todos os Serviços

```bash
docker compose up -d
```

Isso irá iniciar:
- **PostgreSQL** (porta 5432 - `localhost:5432`)
- **Flask** (porta 5000 - `http://localhost:5000`)
- **Strapi** (porta 1337 - `http://localhost:1337/admin`, também acessível via Flask em `/admin`)

#### 3. Verificar Status

```bash
docker compose ps
```

#### 4. Ver Logs

```bash
# Todos os serviços
docker compose logs -f

# Apenas Flask
docker compose logs -f flask
```

**📚 Para mais informações sobre Docker e deploy, consulte [DEPLOY.md](DEPLOY.md)**

### Modo de Desenvolvimento (Sem Docker)

```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

**⚠️ Nota:** Sem Docker, você precisará configurar o PostgreSQL manualmente.

## 🌐 URLs da Aplicação

### Páginas Principais
- **Home**: http://localhost:5000/
- **Loja**: http://localhost:5000/produtos/
- **Carrinho**: http://localhost:5000/carrinho
- **Checkout**: http://localhost:5000/checkout
- **Login**: http://localhost:5000/auth/login
- **Status Pedido**: http://localhost:5000/status-pedido?token=...
- **Strapi Admin**: http://localhost:5000/admin (via proxy reverso)

### APIs
- **Checkout**: `POST /api/checkout/process`
- **Frete**: `POST /api/shipping/calculate`
- **Status Pedido**: `GET /api/orders/<token>`
- **Status Pedido (polling)**: `GET /api/orders/<token>/status`
- **Webhook PagBank**: `POST /api/webhook/pagbank`

## 📁 Estrutura do Projeto

```
Lhama-Banana/
├── app.py                          # Aplicação principal Flask
├── config.py                       # Configurações do sistema (EDITAR AQUI)
├── requirements.txt                # Dependências Python
├── Dockerfile                      # Dockerfile para Flask
├── docker-compose.yml              # Configuração Docker (PostgreSQL, Flask, Strapi)
├── env.example                     # Exemplo de variáveis de ambiente
├── README.md                       # Este arquivo
├── CONFIGURACAO.md                 # Guia completo de configuração
├── DEPLOY.md                       # Guia de deploy e Docker
├── INTEGRACAO_BLING.md             # Documentação da integração Bling
├── GUIA_PREENCHIMENTO_STRAPI.md     # Como preencher conteúdo no Strapi
├── blueprints/                     # Módulos da aplicação
│   ├── api/                        # APIs REST
│   │   ├── checkout.py             # API de checkout
│   │   ├── orders.py               # API de status de pedidos
│   │   ├── shipping.py             # API de frete
│   │   └── webhook.py              # Webhook do PagBank
│   ├── main/                       # Rotas principais
│   │   ├── checkout.py             # Página de checkout
│   │   ├── payment_routes.py       # Páginas de pagamento
│   │   └── static/                 # CSS e JS das páginas
│   └── services/                    # Lógica de negócio
│       ├── checkout_service.py     # Serviços de checkout
│       ├── order_service.py        # Serviços de pedidos
│       └── shipping_service.py     # Serviços de frete
├── templates/                      # Templates HTML base
├── static/                         # Arquivos estáticos globais
├── db/                             # Estrutura do banco de dados
│   ├── schema.sql                  # Schema completo do banco
│   ├── seeds.sql                   # Dados iniciais (opcional)
│   ├── connection.py               # Módulo de conexão PostgreSQL
│   └── README.md                   # Documentação do banco
└── strapi-admin/                   # Painel administrativo Strapi
    ├── Dockerfile                  # Dockerfile para Strapi
    └── ...
```

## 🔧 Configuração Detalhada

### Configurações via Arquivo `.env`

Todas as configurações são gerenciadas via arquivo `.env`. O sistema suporta diferentes ambientes:

- **development**: Desenvolvimento local (padrão)
- **production**: Produção
- **testing**: Testes

Para mudar de ambiente, edite a variável `ENV` no arquivo `.env`.

**📚 Consulte [CONFIGURACAO_AMBIENTES.md](CONFIGURACAO_AMBIENTES.md) para detalhes completos.**

### Configurações Disponíveis (via .env)

#### Ambiente
```bash
ENV=development  # development, production, testing
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_PORT=5000
```

#### Banco de Dados
```bash
DB_HOST=postgres  # No Docker: 'postgres', Local: 'localhost'
DB_NAME=sistema_usuarios
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_PORT=5432
```

#### Firebase
```bash
FIREBASE_ADMIN_SDK_PATH=/app/key.json  # No Docker
# FIREBASE_ADMIN_SDK_PATH=../key.json  # Local
```

#### PagBank (Gateway de Pagamento)
```bash
PAGBANK_API_TOKEN=seu-token
PAGBANK_ENVIRONMENT=sandbox  # sandbox ou production
PAGBANK_NOTIFICATION_URL=http://localhost:5000/api/webhook/pagbank
PAGBANK_SIMULATION_MODE=true  # true para testes sem API real
```

#### Melhor Envio (Cálculo de Frete)
```bash
MELHOR_ENVIO_TOKEN=seu-token
MELHOR_ENVIO_CEP_ORIGEM=13219-052
```

#### Administração
```bash
ADMIN_EMAILS=admin@exemplo.com
```

#### Strapi
```bash
STRAPI_ENABLED=true
STRAPI_URL=http://strapi:1337
```

**Nota:** Todas as configurações são lidas do arquivo `.env`. Não é necessário definir variáveis de ambiente manualmente, a menos que você queira sobrescrever valores específicos.

Para produção, edite o arquivo `.env` e defina:
```bash
ENV=production
FLASK_ENV=production
FLASK_DEBUG=0
PAGBANK_ENVIRONMENT=production
PAGBANK_SIMULATION_MODE=false
```

## 📚 Documentação

- **`README.md`**: Este arquivo - visão geral e instalação
- **`CONFIGURACAO.md`**: Guia completo de configuração (Firebase, PagBank, Bling, Melhor Envio, Strapi, Banco de Dados)
- **`DEPLOY.md`**: Guia de deploy (Docker, Nginx, Gunicorn, SSL, Banco de Dados, Scripts SQL)
- **`INTEGRACAO_BLING.md`**: Documentação completa da integração com Bling
- **`GUIA_PREENCHIMENTO_STRAPI.md`**: Guia completo do Strapi (configuração, Content Types, preenchimento de conteúdo)

## 🧪 Testes

### Testar Checkout
1. Adicione produtos ao carrinho
2. Acesse `/checkout`
3. Preencha os dados
4. Selecione método de pagamento
5. Finalize a compra

### Testar Webhook (Local)
1. Use ngrok: `ngrok http 5000`
2. Configure URL temporária no painel PagBank
3. Faça um pagamento de teste
4. Verifique logs do webhook

## 📊 Status do Projeto

| Funcionalidade | Status | Descrição |
|----------------|--------|-----------|
| ✅ Checkout | 100% | Sistema completo com PIX, Boleto e Cartão |
| ✅ Frete | 100% | Cálculo dinâmico via Melhor Envio |
| ✅ Pagamentos | 100% | PagBank integrado com webhook |
| ✅ Status Pedidos | 100% | Páginas dedicadas com polling |
| ✅ Admin Panel | 100% | Painel administrativo funcional |

## 🎯 Próximas Melhorias

1. **Notificações por Email**
   - Confirmação de pedido
   - Atualização de status
   - Recuperação de senha

2. **Dashboard Analytics**
   - Relatórios de vendas
   - Gráficos de performance
   - Análise de produtos

3. **Melhorias de UX**
   - Animações suaves
   - Feedback visual aprimorado
   - Loading states

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.

---

**Desenvolvido com ❤️ para o e-commerce moderno**
