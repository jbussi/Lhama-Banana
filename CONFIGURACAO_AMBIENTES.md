# ⚙️ Configuração de Ambientes

O sistema suporta diferentes ambientes configuráveis via variável `ENV` no arquivo `.env`.

## 🌍 Ambientes Disponíveis

### Development (Desenvolvimento)
- **ENV=development**
- Debug ativado
- Hot reload habilitado
- Cache desabilitado
- Logs detalhados
- Permite continuar sem Firebase/DB (com avisos)

### Production (Produção)
- **ENV=production**
- Debug desabilitado
- Cache habilitado
- Logs mínimos
- Firebase e DB obrigatórios
- Simulação PagBank desabilitada

### Testing (Testes)
- **ENV=testing**
- Debug ativado
- Banco de dados de teste
- Configurações otimizadas para testes

## 📝 Como Configurar

### 1. Criar arquivo .env

```bash
# Windows
Copy-Item env.example .env

# Linux/Mac
cp env.example .env
```

### 2. Editar .env e definir ambiente

```bash
# Para desenvolvimento
ENV=development
FLASK_ENV=development
FLASK_DEBUG=1

# Para produção
ENV=production
FLASK_ENV=production
FLASK_DEBUG=0
```

## 🔧 Configurações por Ambiente

### Development
```bash
ENV=development
FLASK_ENV=development
FLASK_DEBUG=1
PAGBANK_SIMULATION_MODE=true
PAGBANK_ENVIRONMENT=sandbox
DB_HOST=postgres  # No Docker
# DB_HOST=localhost  # Local sem Docker
```

### Production
```bash
ENV=production
FLASK_ENV=production
FLASK_DEBUG=0
PAGBANK_SIMULATION_MODE=false
PAGBANK_ENVIRONMENT=production
PAGBANK_NOTIFICATION_URL=https://seudominio.com/api/webhook/pagbank
DB_HOST=postgres
NODE_ENV=production
```

### Testing
```bash
ENV=testing
FLASK_ENV=testing
FLASK_DEBUG=1
DB_NAME=sistema_usuarios_test
```

## 📋 Variáveis Importantes

### Obrigatórias
- `ENV`: Ambiente atual (development/production/testing)
- `DB_HOST`: Host do banco de dados
- `DB_NAME`: Nome do banco
- `DB_USER`: Usuário do banco
- `DB_PASSWORD`: Senha do banco

### Opcionais (com defaults)
- `SECRET_KEY`: Chave secreta do Flask
- `FIREBASE_ADMIN_SDK_PATH`: Caminho do key.json
- `PAGBANK_API_TOKEN`: Token do PagBank
- `MELHOR_ENVIO_TOKEN`: Token do Melhor Envio

## 🔄 Mudando de Ambiente

Para mudar de ambiente, edite o arquivo `.env`:

```bash
# Mudar para produção
ENV=production
FLASK_ENV=production
FLASK_DEBUG=0

# Reiniciar containers
docker compose restart flask
```

## ✅ Verificar Ambiente Atual

O ambiente atual é exibido no console ao iniciar a aplicação:

```
🔧 Modo de desenvolvimento ativado
🏭 Modo de produção ativado
🧪 Modo testing ativado
```



