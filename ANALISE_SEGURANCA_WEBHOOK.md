# 🔒 Análise de Segurança do Webhook PagBank

## 📋 Resumo Executivo

**Status Atual: ⚠️ SEGURANÇA INSUFICIENTE**

A implementação atual do webhook do PagBank possui vulnerabilidades críticas que permitem falsificação de requisições.

---

## 🚨 Problemas Identificados

### 1. **Verificação Apenas por Headers Falsificáveis**

O método atual (`is_request_from_pagbank()`) verifica apenas:

- ✅ `User-Agent` contendo "pagseguro" ou "pagbank" (fácil de falsificar)
- ✅ Headers customizados (`X-PagBank-Webhook`, etc.) (fácil de falsificar)
- ✅ `Referer` e `Origin` (fácil de falsificar)

**Vulnerabilidade**: Qualquer atacante pode fazer uma requisição POST para o endpoint com esses headers falsificados e o sistema aceitará como legítimo.

### 2. **Falta de Verificação Criptográfica**

Não há verificação de assinatura HMAC ou similar para garantir:
- ✅ Autenticidade (a requisição veio realmente do PagBank)
- ✅ Integridade (os dados não foram alterados)
- ✅ Não-repúdio (não pode ser negado que veio do PagBank)

### 3. **Falta de Whitelist de IPs**

Não há verificação se a requisição vem dos IPs oficiais do PagBank.

---

## 🔍 Método de Verificação Atual

**Arquivo**: `blueprints/api/webhook.py` (linhas 28-69)

```python
def is_request_from_pagbank():
    """
    Verifica se a requisição veio do PagBank através de headers.
    
    ⚠️ PROBLEMA: Headers podem ser facilmente falsificados!
    """
    # Verificar User-Agent
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'pagseguro' in user_agent or 'pagbank' in user_agent:
        return True
    
    # Verificar headers customizados
    possible_headers = ['X-PagBank-Webhook', ...]
    for header_name in possible_headers:
        if request.headers.get(header_name):
            return True
    
    # Verificar Referer/Origin
    # ...
```

**Problema**: Qualquer requisição com esses headers é aceita como legítima.

---

## ✅ Recomendações de Segurança

### 1. **Implementar Verificação de Assinatura HMAC**

O PagBank/PagSeguro provavelmente fornece uma chave secreta e uma assinatura no header `X-PagSeguro-Signature` ou similar.

**Como funciona**:
1. PagBank gera uma assinatura HMAC usando o corpo da requisição + chave secreta
2. PagBank envia a assinatura no header
3. Sistema recalcula a assinatura e compara

**Implementação necessária**:
```python
import hmac
import hashlib

def verify_pagbank_signature(request_body, signature, secret_key):
    expected_signature = hmac.new(
        secret_key.encode(),
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
```

### 2. **Implementar Whitelist de IPs**

Consultar a documentação do PagBank para obter os IPs oficiais e adicionar verificação:

```python
PAGBANK_ALLOWED_IPS = [
    '52.x.x.x',  # IPs do PagBank
    # ...
]
```

### 3. **Validar charge_id no Banco de Dados**

Já implementado ✅ - O sistema busca o pagamento pelo `charge_id` antes de processar, o que adiciona uma camada de proteção.

### 4. **Adicionar Rate Limiting**

Implementar rate limiting no endpoint para prevenir ataques de força bruta.

### 5. **Usar HTTPS Obrigatório**

Garantir que o webhook só aceite requisições HTTPS em produção.

---

## 🛠️ Implementação Recomendada

1. **Consultar Documentação Oficial do PagBank**
   - Verificar método exato de assinatura de webhooks
   - Obter chave secreta para verificação
   - Obter lista de IPs oficiais

2. **Implementar Verificação Multi-Camada**
   - Verificação de assinatura HMAC (prioritária)
   - Whitelist de IPs (complementar)
   - Validação de dados no banco (já implementada)

3. **Manter Logs Detalhados**
   - Registrar todas as tentativas de acesso
   - Alertar sobre tentativas suspeitas

---

## 📚 Referências

- [OWASP Webhook Security](https://owasp.org/www-community/vulnerabilities/Webhook_Security)
- [Best Practices for Webhook Security](https://www.cloudflare.com/learning/security/api/secure-webhooks/)

---

## ✅ Melhorias Implementadas

### Verificação Multi-Camada

Foi implementado um sistema de verificação em múltiplas camadas:

1. **Verificação de Authorization Header** (Prioridade Alta)
   - Valida token no header `Authorization`
   - Usa `PAGBANK_WEBHOOK_SECRET` ou `PAGBANK_API_TOKEN` como fallback
   - Comparação segura com `hmac.compare_digest()` (evita timing attacks)

2. **Verificação de Assinatura HMAC-SHA256** (Prioridade Alta)
   - Valida assinatura criptográfica nos headers:
     - `X-PagSeguro-Signature`
     - `X-PagBank-Signature`
     - `X-Webhook-Signature`
   - Calcula HMAC-SHA256 do corpo da requisição
   - Compara com a assinatura recebida

3. **Headers Customizados** (Camada Adicional)
   - `X-PagBank-Webhook`
   - `X-PagSeguro-Notification`
   - `X-PagBank-Notification`
   - `X-Webhook-Source`

4. **User-Agent / Origin** (Camada de Compatibilidade)
   - Mantido para retrocompatibilidade
   - Logs de warning quando usado como única validação

### Configuração Necessária

Para habilitar a verificação máxima de segurança, configure:

```bash
# Opção 1: Token específico para webhooks (RECOMENDADO)
export PAGBANK_WEBHOOK_SECRET="seu-token-secreto-webhook"

# Opção 2: Usar o mesmo token da API (fallback)
# O sistema usará PAGBANK_API_TOKEN automaticamente se PAGBANK_WEBHOOK_SECRET não estiver configurado
```

### Como Verificar se Está Funcionando

1. Verifique os logs quando receber um webhook
2. Procure por:
   - `✅ Validação por Authorization header: OK` - Validação por token
   - `✅ Validação por assinatura criptográfica HMAC-SHA256: OK` - Validação por assinatura
   - `⚠️ Validação apenas por User-Agent (menos seguro)` - Apenas validação básica

### Próximos Passos

1. **Verificar logs dos webhooks recebidos** para identificar qual método o PagBank usa
2. **Configurar `PAGBANK_WEBHOOK_SECRET`** com o token/chave apropriado
3. **Se o PagBank enviar assinatura**, verificar se está no formato esperado
4. **Em produção**, considerar desabilitar validação por User-Agent apenas se outras camadas estiverem funcionando

## ⚡ Status Atual

**MELHORADO**: Sistema agora possui múltiplas camadas de segurança

**Risco Atual**: ⚠️ **MÉDIO** (depende da configuração do token/assinatura)

**Ação Necessária**: Configurar `PAGBANK_WEBHOOK_SECRET` após verificar nos logs qual método o PagBank utiliza

