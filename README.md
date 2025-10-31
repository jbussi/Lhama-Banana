# 🦙 LhamaBanana - E-commerce Platform

Uma plataforma de e-commerce moderna construída com Flask, PostgreSQL e Firebase.

## 🚀 **Funcionalidades Implementadas**

### ✅ **Sistema de Checkout Completo**
- **Processamento de Pedidos** com validação de estoque
- **Integração PagSeguro** (PIX, Cartão de Crédito, Boleto)
- **Cálculo de Frete** em tempo real
- **Página de Confirmação** com QR Code e links de pagamento

### ✅ **Sistema de Frete Inteligente**
- **Validação de CEP** via ViaCEP
- **Múltiplas Modalidades**: PAC, SEDEX, Frete Grátis
- **Cálculo Dinâmico** baseado em peso, distância e valor

### ✅ **Autenticação e Usuários**
- **Firebase Authentication** integrado
- **Sistema de Perfis** de usuário
- **Carrinho Persistente** por sessão

## 🛠️ **Tecnologias Utilizadas**

- **Backend**: Flask (Python)
- **Banco de Dados**: PostgreSQL
- **Autenticação**: Firebase Admin SDK
- **Pagamentos**: PagSeguro API
- **Frontend**: HTML5, CSS3, JavaScript
- **Frete**: ViaCEP API

## 📦 **Instalação**

### **1. Clonar o Repositório**
```bash
git clone <seu-repositorio>
cd LhamaBanana_visual_estatica_corrigida/Lhama-Banana
```

### **2. Instalar Dependências**
```bash
pip install -r requirements.txt
```

### **3. Configurar Variáveis de Ambiente**
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas configurações
nano .env
```

### **4. Configurar Firebase**
- Coloque o arquivo `key.json` na raiz do projeto
- Configure as credenciais do Firebase

## 🚀 **Execução**

### **Modo de Desenvolvimento**
```bash
# Método 1: Simples
DEV_MODE=1 python app.py

# Método 2: Script Python
python run_dev.py

# Método 3: Script Shell
./start_dev.sh
```

### **Modo de Produção**
```bash
python app.py
```

## 🌐 **URLs da Aplicação**

### **Páginas Principais**
- **Home**: http://127.0.0.1:5000/
- **Loja**: http://127.0.0.1:5000/produtos/
- **Carrinho**: http://127.0.0.1:5000/carrinho
- **Checkout**: http://127.0.0.1:5000/checkout
- **Login**: http://127.0.0.1:5000/auth/login

### **APIs**
- **Checkout**: `POST /api/checkout/process`
- **Frete**: `POST /api/shipping/calculate`
- **Validação CEP**: `POST /api/shipping/validate-cep`
- **Status Pedido**: `GET /api/checkout/status/<codigo>`

## 📁 **Estrutura do Projeto**

```
Lhama-Banana/
├── app.py                          # Aplicação principal
├── config.py                       # Configurações de produção
├── config_dev.py                   # Configurações de desenvolvimento
├── requirements.txt                # Dependências Python
├── run_dev.py                      # Script de desenvolvimento
├── start_dev.sh                    # Script shell
├── test_app.py                     # Testes da aplicação
├── blueprints/                     # Módulos da aplicação
│   ├── api/                        # APIs REST
│   │   ├── checkout.py             # API de checkout
│   │   └── shipping.py             # API de frete
│   ├── main/                       # Rotas principais
│   │   ├── checkout.py             # Página de checkout
│   │   └── order_confirmation.py   # Confirmação de pedido
│   └── services/                   # Lógica de negócio
│       ├── checkout_service.py     # Serviços de checkout
│       └── shipping_service.py     # Serviços de frete
├── templates/                      # Templates HTML
│   ├── checkout.html               # Página de checkout
│   └── order_confirmation.html     # Confirmação de pedido
├── static/                         # Arquivos estáticos
│   ├── css/                        # Estilos CSS
│   └── js/                         # JavaScript
└── plataform_config/               # Configurações da plataforma
```

## 🔧 **Configuração**

### **Variáveis de Ambiente**
```bash
# Desenvolvimento
FLASK_DEBUG=1
FLASK_ENV=development
DEV_MODE=1

# Produção
FLASK_ENV=production
```

### **Configurações do Banco**
```python
DATABASE_CONFIG = {
    "host": "localhost",
    "dbname": "sistema_usuarios",
    "user": "postgres",
    "password": "sua_senha"
}
```

### **Configurações PagSeguro**
```python
PAGSEGURO_SANDBOX_API_TOKEN = "seu_token_sandbox"
PAGSEGURO_SANDBOX_CHECKOUT_URL = "https://sandbox.api.pagseguro.com/checkouts"
```

## 🧪 **Testes**

### **Executar Testes**
```bash
python test_app.py
```

### **Testes Disponíveis**
- ✅ Teste de imports
- ✅ Teste de criação da aplicação
- ✅ Teste de configuração
- ✅ Teste de rotas

## 📊 **Status do Projeto**

| Funcionalidade | Status | Descrição |
|----------------|--------|-----------|
| ✅ Checkout | 100% | Sistema completo implementado |
| ✅ Frete | 100% | Cálculo dinâmico funcionando |
| ✅ Pagamentos | 100% | PagSeguro integrado |
| ⏳ Admin Panel | 0% | Pendente de implementação |
| ⏳ Design | 0% | Melhorias visuais pendentes |
| ⏳ 2FA | 0% | Autenticação admin pendente |

## 🎯 **Próximas Implementações**

1. **Painel Administrativo**
   - Dashboard com insights
   - Gestão de produtos
   - Controle de estoque
   - Relatórios de vendas

2. **Melhorias de Design**
   - Interface moderna
   - Responsividade
   - Animações
   - UX/UI aprimorada

3. **Segurança**
   - 2FA para administradores
   - Validações avançadas
   - Logs de auditoria

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 **Suporte**

Para suporte, entre em contato através de:
- Email: suporte@lhamabanana.com
- Issues: GitHub Issues

---

**Desenvolvido com ❤️ para o e-commerce moderno**

