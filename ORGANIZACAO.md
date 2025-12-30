# 📁 Organização do Projeto - LhamaBanana

## 📂 Estrutura de Arquivos

### ✅ Arquivos Essenciais (MANTIDOS)

```
Lhama-Banana/
├── app.py                          # ✅ Aplicação Flask principal
├── config.py                       # ✅ Configurações (EDITAR AQUI)
├── requirements.txt                # ✅ Dependências Python
├── run_migration_orders.py         # ✅ Script de migração SQL
├── README.md                       # ✅ Documentação principal
├── CONFIGURACAO_PAGBANK.md         # ✅ Guia PagBank
├── VERIFICACAO_RAPIDA.md           # ✅ Checklist
├── ORGANIZACAO.md                  # ✅ Este arquivo
└── blueprints/                      # ✅ Módulos da aplicação
```

### 🗑️ Arquivos Removidos (INUTILIZADOS)

- ❌ `config_dev.py` - Consolidado em `config.py`
- ❌ `readme.txt` - Substituído por `README.md`
- ❌ `CHANGELOG.md` - Documentação desatualizada
- ❌ `COMANDOS.md` - Informações no README
- ❌ `test_app.py` - Testes não utilizados
- ❌ `run_dev.bat` - Scripts desnecessários
- ❌ `clear_cache.ps1` - Scripts desnecessários
- ❌ `dev.ps1` - Scripts desnecessários
- ❌ `start_dev.sh` - Scripts desnecessários
- ❌ `run_dev.py` - Scripts desnecessários
- ❌ `static/_backup_checkout/` - Backup antigo

## 🔧 Configurações

### Arquivo Principal: `config.py`

**Todas as configurações estão centralizadas neste arquivo.**

#### Seções:
1. **SEGURANÇA** - Secret key
2. **FIREBASE** - Autenticação
3. **BANCO DE DADOS** - PostgreSQL
4. **PAGBANK** - Gateway de pagamento
5. **MELHOR ENVIO** - Cálculo de frete
6. **ADMINISTRAÇÃO** - Emails admin

#### Variáveis Removidas (não utilizadas):
- ❌ `PAGBANK_RETURN_URL` - Não utilizado no código
- ❌ `PAGBANK_STORE_ID` - Não utilizado no código
- ❌ Todas variáveis `PAGSEGURO_*` - Substituídas por `PAGBANK_*`

### Como Alterar Configurações

1. **Edite diretamente `config.py`** (recomendado para desenvolvimento)
2. **Use variáveis de ambiente** (recomendado para produção)

```bash
# Exemplo: Windows PowerShell
$env:PAGBANK_ENVIRONMENT="production"
$env:PAGBANK_API_TOKEN="seu-token-producao"

# Exemplo: Linux/Mac
export PAGBANK_ENVIRONMENT="production"
export PAGBANK_API_TOKEN="seu-token-producao"
```

## 📚 Documentação

### Arquivos de Documentação Mantidos:
- ✅ `README.md` - Documentação principal e guia de instalação
- ✅ `CONFIGURACAO_PAGBANK.md` - Guia detalhado do PagBank
- ✅ `VERIFICACAO_RAPIDA.md` - Checklist de verificação
- ✅ `ORGANIZACAO.md` - Este arquivo (estrutura do projeto)

## 🚀 Execução

### Comando Simples:
```bash
python app.py
```

A aplicação detecta automaticamente o modo de desenvolvimento baseado nas configurações.

## 📝 Notas

- Todas as configurações podem ser sobrescritas por variáveis de ambiente
- O arquivo `config.py` é auto-documentado com comentários
- Não há mais necessidade de múltiplos arquivos de configuração
- Scripts de desenvolvimento foram removidos (use `python app.py` diretamente)

