# 🚀 Comandos Essenciais - LhamaBanana

## 📁 **Navegação**
```bash
# Ir para o diretório do projeto
cd /media/joao/B95C-F78A/Projects/lhama_banana/LhamaBanana_visual_estatica_corrigida/Lhama-Banana

# Ver estrutura do projeto
ls -la
tree -I '__pycache__'  # Se tree estiver instalado
```

## 🚀 **Executar Aplicação**

### **Desenvolvimento (Recomendado)**
```bash
# Método 1: Simples
DEV_MODE=1 python app.py

# Método 2: Script Python
python run_dev.py

# Método 3: Script Shell
./start_dev.sh

# Método 4: Com variáveis de ambiente
FLASK_DEBUG=1 FLASK_ENV=development python app.py
```

### **Produção**
```bash
python app.py
```

## 🧪 **Testes**
```bash
# Executar todos os testes
python test_app.py

# Testar imports específicos
python -c "from app import create_app; print('OK')"

# Testar com timeout
timeout 5 python app.py
```

## 📦 **Dependências**
```bash
# Instalar dependências
pip install -r requirements.txt

# Verificar dependências instaladas
pip list | grep -E "(Flask|psycopg2|firebase)"

# Atualizar dependências
pip install --upgrade -r requirements.txt
```

## 🗄️ **Banco de Dados**
```bash
# Iniciar PostgreSQL (Ubuntu/Debian)
sudo systemctl start postgresql

# Verificar status
sudo systemctl status postgresql

# Conectar ao banco
psql -U postgres -d sistema_usuarios
```

## 🔧 **Desenvolvimento**
```bash
# Ver logs em tempo real
tail -f logs/app.log

# Verificar portas em uso
netstat -tlnp | grep :5000
netstat -tlnp | grep :80

# Matar processo na porta 5000
sudo lsof -ti:5000 | xargs kill -9
```

## 📊 **Monitoramento**
```bash
# Ver processos Python
ps aux | grep python

# Ver uso de memória
free -h

# Ver espaço em disco
df -h
```

## 🔄 **Git (Se usando)**
```bash
# Status do repositório
git status

# Adicionar arquivos
git add .

# Commit
git commit -m "Implementação do sistema de checkout"

# Push
git push origin main
```

## 🗂️ **Backup**
```bash
# Criar backup completo
tar -czf LhamaBanana_backup_$(date +%Y%m%d_%H%M%S).tar.gz LhamaBanana_visual_estatica_corrigida/

# Restaurar backup
tar -xzf LhamaBanana_backup_YYYYMMDD_HHMMSS.tar.gz
```

## 🌐 **URLs Importantes**
```bash
# Acessar no navegador
http://127.0.0.1:5000/                    # Home
http://127.0.0.1:5000/checkout            # Checkout
http://127.0.0.1:5000/carrinho            # Carrinho
http://127.0.0.1:5000/produtos/           # Loja
http://127.0.0.1:5000/auth/login          # Login

# APIs
curl -X POST http://127.0.0.1:5000/api/shipping/calculate \
  -H "Content-Type: application/json" \
  -d '{"cep": "01234567"}'
```

## 🐛 **Debug**
```bash
# Ver logs do Flask
export FLASK_DEBUG=1
python app.py

# Verificar configurações
python -c "from app import create_app; app = create_app(); print(app.config)"

# Testar conexão com banco
python -c "from blueprints.services import get_db; print('DB OK')"
```

## 📱 **Testes de API**
```bash
# Testar API de frete
curl -X POST http://127.0.0.1:5000/api/shipping/calculate \
  -H "Content-Type: application/json" \
  -d '{"cep": "01234567"}'

# Testar API de checkout (exemplo)
curl -X POST http://127.0.0.1:5000/api/checkout/process \
  -H "Content-Type: application/json" \
  -d '{"shipping_info": {...}, "payment_method": "PIX"}'
```

## 🔒 **Segurança**
```bash
# Verificar permissões
ls -la key.json
chmod 600 key.json  # Apenas owner pode ler

# Verificar variáveis de ambiente
env | grep FLASK
env | grep DEV
```

## 📋 **Checklist de Inicialização**
```bash
# 1. Verificar dependências
pip list | grep Flask

# 2. Verificar arquivo key.json
ls -la key.json

# 3. Verificar configurações
python -c "from config_dev import ConfigDev; print('Config OK')"

# 4. Executar testes
python test_app.py

# 5. Iniciar aplicação
DEV_MODE=1 python app.py
```

---
**💡 Dica**: Salve este arquivo para referência rápida!

