# 🔧 Configuração do PagBank - Guia Completo

Este documento explica como configurar as URLs do PagBank e como o sistema funciona para os diferentes métodos de pagamento.

## 📍 Onde Configurar

### 1. Arquivo de Configuração Principal: `config.py`

Todas as configurações do PagBank estão no arquivo `Lhama-Banana/config.py`:

```python
# URLs da API PagBank
PAGBANK_SANDBOX_API_URL = "https://sandbox.pagseguro.uol.com.br/orders"
PAGBANK_PRODUCTION_API_URL = "https://api.pagbank.com.br/orders"

# Ambiente: 'sandbox' ou 'production'
PAGBANK_ENVIRONMENT = os.environ.get('PAGBANK_ENVIRONMENT', 'sandbox')

# URL do Webhook (onde o PagBank enviará notificações)
PAGBANK_NOTIFICATION_URL = os.environ.get(
    'PAGBANK_NOTIFICATION_URL', 
    'http://localhost:5000/api/webhook/pagbank'  # ⚠️ ATUALIZAR PARA PRODUÇÃO
)

# Token de autenticação
PAGBANK_API_TOKEN = os.environ.get('PAGBANK_API_TOKEN', 'seu-token-aqui')

# Modo de simulação (para testes sem API real)
PAGBANK_SIMULATION_MODE = os.environ.get('PAGBANK_SIMULATION_MODE', 'true').lower() == 'true'
```

### 2. Variáveis de Ambiente (Recomendado para Produção)

Você pode sobrescrever as configurações usando variáveis de ambiente:

```bash
# Windows PowerShell
$env:PAGBANK_ENVIRONMENT="production"
$env:PAGBANK_API_TOKEN="seu-token-de-producao"
$env:PAGBANK_NOTIFICATION_URL="https://seudominio.com.br/api/webhook/pagbank"
$env:PAGBANK_SIMULATION_MODE="false"

# Linux/Mac
export PAGBANK_ENVIRONMENT="production"
export PAGBANK_API_TOKEN="seu-token-de-producao"
export PAGBANK_NOTIFICATION_URL="https://seudominio.com.br/api/webhook/pagbank"
export PAGBANK_SIMULATION_MODE="false"
```

## 🔄 Como Funciona para Cada Método de Pagamento

### **PIX (Pagamento Instantâneo)**

1. **Checkout:**
   - Cliente seleciona PIX no checkout
   - Sistema cria payload com `payment_method: { type: "PIX" }`
   - Envia para PagBank: `POST /orders`

2. **Resposta do PagBank:**
   - PagBank retorna QR Code (imagem e código text)
   - Sistema salva no banco: `pagbank_qrcode_link`, `pagbank_qrcode_image`
   - Código PIX text é extraído do JSON e salvo

3. **Redirecionamento:**
   - Cliente é redirecionado para `/pagamento/pix?token=...`
   - Página exibe QR Code e código PIX copiável
   - Polling automático a cada 5 segundos verifica status

4. **Webhook:**
   - Quando cliente paga, PagBank envia notificação para `/api/webhook/pagbank`
   - Sistema atualiza status: `PENDENTE` → `PAGO` → `APROVADO`
   - Página detecta mudança e redireciona para status

### **Boleto Bancário**

1. **Checkout:**
   - Cliente seleciona Boleto no checkout
   - Sistema cria payload com `payment_method: { type: "BOLETO" }`
   - Define vencimento (padrão: 3 dias)

2. **Resposta do PagBank:**
   - PagBank retorna link do boleto e código de barras
   - Sistema salva: `pagbank_boleto_link`, `pagbank_barcode_data`

3. **Redirecionamento:**
   - Cliente é redirecionado para `/pagamento/boleto?token=...`
   - Página exibe código de barras e botões para visualizar/baixar
   - Polling automático a cada 5 segundos

4. **Webhook:**
   - Quando boleto é pago (pode levar até 3 dias), PagBank notifica
   - Sistema atualiza status automaticamente

### **Cartão de Crédito**

1. **Checkout:**
   - Cliente seleciona Cartão e preenche dados
   - Sistema cria payload com dados do cartão ou token
   - Envia para PagBank

2. **Resposta do PagBank:**
   - PagBank processa imediatamente
   - Retorna status: `PAID`, `AUTHORIZED`, `DECLINED`, etc.

3. **Redirecionamento:**
   - Cliente é redirecionado diretamente para `/status-pedido?token=...`
   - Não precisa de página intermediária (pagamento é instantâneo)

4. **Webhook:**
   - PagBank pode enviar webhook confirmando pagamento
   - Sistema atualiza status se necessário

## 🔗 URLs Importantes

### **URL da API (Requisições do Sistema → PagBank)**

- **Sandbox:** `https://sandbox.pagseguro.uol.com.br/orders`
- **Produção:** `https://api.pagbank.com.br/orders`

**Configurar em:** `config.py` → `PAGBANK_SANDBOX_API_URL` / `PAGBANK_PRODUCTION_API_URL`

### **URL do Webhook (PagBank → Sistema)**

- **Desenvolvimento:** `http://localhost:5000/api/webhook/pagbank`
- **Produção:** `https://seudominio.com.br/api/webhook/pagbank`

**⚠️ IMPORTANTE:**
- A URL do webhook DEVE ser acessível publicamente (não pode ser localhost em produção)
- Configure no painel do PagBank para enviar notificações para esta URL
- O endpoint já está implementado: `POST /api/webhook/pagbank`

**Configurar em:** `config.py` → `PAGBANK_NOTIFICATION_URL`

## 🎯 Fluxo Completo por Método

### **PIX:**
```
Checkout → API PagBank → Resposta com QR Code → 
Página PIX (polling 5s) → Cliente paga → 
Webhook atualiza status → Página detecta → Redireciona para Status
```

### **Boleto:**
```
Checkout → API PagBank → Resposta com Boleto → 
Página Boleto (polling 5s) → Cliente paga (até 3 dias) → 
Webhook atualiza status → Página detecta → Redireciona para Status
```

### **Cartão:**
```
Checkout → API PagBank → Processamento imediato → 
Resposta com status → Redireciona direto para Status
```

## ⚙️ Configuração no Painel do PagBank

1. **Acesse o painel do desenvolvedor do PagBank**
2. **Configure o Webhook:**
   - Vá em "Configurações" → "Webhooks"
   - Adicione a URL: `https://seudominio.com.br/api/webhook/pagbank`
   - Selecione os eventos: `PAYMENT.*` (todos os eventos de pagamento)

3. **Obtenha o Token:**
   - Vá em "Credenciais" → "API Token"
   - Copie o token e configure em `PAGBANK_API_TOKEN`

## 🧪 Modo de Simulação

O sistema tem um modo de simulação que permite testar sem chamar a API real:

- **Ativado por padrão** em desenvolvimento
- Gera respostas mockadas para PIX, Boleto e Cartão
- Útil para testar o fluxo completo sem custos

**Para desativar (usar API real):**
```python
PAGBANK_SIMULATION_MODE = False
# ou
export PAGBANK_SIMULATION_MODE="false"
```

## 📝 Checklist para Produção

- [ ] Atualizar `PAGBANK_ENVIRONMENT` para `"production"`
- [ ] Configurar `PAGBANK_API_TOKEN` com token de produção
- [ ] Atualizar `PAGBANK_NOTIFICATION_URL` para URL pública (HTTPS)
- [ ] Configurar webhook no painel do PagBank
- [ ] Desativar `PAGBANK_SIMULATION_MODE`
- [ ] Testar webhook com ferramenta de teste do PagBank
- [ ] Verificar logs para confirmar recebimento de webhooks

## 🔍 Verificação Rápida

Para verificar se está tudo configurado:

1. **Verificar configurações atuais:**
   ```python
   # No código ou console Python
   from config import Config
   print(f"Ambiente: {Config.PAGBANK_ENVIRONMENT}")
   print(f"API URL: {Config.PAGBANK_SANDBOX_API_URL if Config.PAGBANK_ENVIRONMENT == 'sandbox' else Config.PAGBANK_PRODUCTION_API_URL}")
   print(f"Webhook URL: {Config.PAGBANK_NOTIFICATION_URL}")
   print(f"Simulação: {Config.PAGBANK_SIMULATION_MODE}")
   ```

2. **Testar webhook localmente:**
   - Use ngrok ou similar para expor `localhost:5000`
   - Configure URL temporária no PagBank
   - Faça um teste de pagamento

## 🚨 Importante

- **Webhook em produção DEVE usar HTTPS**
- **URL do webhook deve ser acessível publicamente**
- **Configure no painel do PagBank para enviar notificações**
- **O sistema funciona para os 3 métodos simultaneamente** - cada pedido escolhe um método, mas o sistema suporta todos

