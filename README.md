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
Execute as migrações SQL na ordem:
```bash
# 1. Criar estrutura base
psql -U postgres -d sistema_usuarios -f sql/criar-banco-de-dados.sql

# 2. Atualizar checkout e pagamentos
psql -U postgres -d sistema_usuarios -f sql/atualizar-checkout-pagamentos.sql

# 3. Criar tabela orders
cd Lhama-Banana
python run_migration_orders.py
```

## 🚀 Execução

### Modo de Desenvolvimento
```bash
python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

## 🌐 URLs da Aplicação

### Páginas Principais
- **Home**: http://localhost:5000/
- **Loja**: http://localhost:5000/produtos/
- **Carrinho**: http://localhost:5000/carrinho
- **Checkout**: http://localhost:5000/checkout
- **Login**: http://localhost:5000/auth/login
- **Status Pedido**: http://localhost:5000/status-pedido?token=...

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
├── run_migration_orders.py         # Script para executar migração SQL
├── README.md                       # Este arquivo
├── CONFIGURACAO_PAGBANK.md         # Guia de configuração do PagBank
├── VERIFICACAO_RAPIDA.md          # Checklist de verificação
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
└── sql/                            # Scripts SQL de migração
    ├── criar-banco-de-dados.sql
    ├── atualizar-checkout-pagamentos.sql
    └── criar-tabela-orders.sql
```

## 🔧 Configuração Detalhada

### Configurações Disponíveis em `config.py`

#### Banco de Dados
```python
DATABASE_CONFIG = {
    "host": "localhost",
    "dbname": "sistema_usuarios",
    "user": "postgres",
    "password": "sua_senha"
}
```

#### PagBank (Gateway de Pagamento)
```python
PAGBANK_API_TOKEN = "seu-token"                    # Token do painel PagBank
PAGBANK_ENVIRONMENT = "sandbox"                    # "sandbox" ou "production"
PAGBANK_NOTIFICATION_URL = "http://..."            # URL do webhook
PAGBANK_SIMULATION_MODE = True                     # True para testes sem API real
```

#### Melhor Envio (Cálculo de Frete)
```python
MELHOR_ENVIO_TOKEN = "seu-token"                   # Token da API Melhor Envio
MELHOR_ENVIO_CEP_ORIGEM = "13219-052"              # CEP da loja
```

#### Administração
```python
ADMIN_EMAILS = ['admin@exemplo.com']              # Emails com acesso admin
```

### Variáveis de Ambiente

Todas as configurações podem ser sobrescritas por variáveis de ambiente:

```bash
# Banco de Dados
DB_HOST=localhost
DB_NAME=sistema_usuarios
DB_USER=postgres
DB_PASSWORD=sua_senha

# PagBank
PAGBANK_API_TOKEN=seu-token
PAGBANK_ENVIRONMENT=sandbox
PAGBANK_NOTIFICATION_URL=https://seudominio.com/api/webhook/pagbank
PAGBANK_SIMULATION_MODE=false

# Melhor Envio
MELHOR_ENVIO_TOKEN=seu-token
MELHOR_ENVIO_CEP_ORIGEM=13219-052

# Admin
ADMIN_EMAILS=admin1@exemplo.com,admin2@exemplo.com
```

## 📚 Documentação Adicional

- **`CONFIGURACAO_PAGBANK.md`**: Guia completo de configuração do PagBank
- **`VERIFICACAO_RAPIDA.md`**: Checklist de verificação do sistema

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
