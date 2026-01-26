# 🚀 Como Executar a Ativação de HTTPS

## ⚠️ IMPORTANTE
Este script **DEVE** ser executado **no servidor Linux** onde o Docker Compose está rodando, **NÃO** no Windows local.

## 📋 Pré-requisitos

1. **Acesso SSH ao servidor**
2. **Arquivo `.env` configurado** no servidor com:
   ```bash
   CERTBOT_EMAIL=seu-email@exemplo.com
   CERTBOT_DOMAIN=lhamabanana.com
   ```
3. **Domínios apontando para o servidor** (DNS configurado)
4. **Porta 80 aberta** e acessível

## 🔧 Passo a Passo

### 1. Conectar ao Servidor via SSH

```bash
ssh usuario@ip-do-servidor
```

### 2. Navegar até o Diretório do Projeto

```bash
cd /opt/lhama-banana/Lhama-Banana
# ou o caminho onde está o projeto no servidor
```

### 3. Verificar se o arquivo `.env` está configurado

```bash
cat .env | grep CERTBOT
```

Deve mostrar:
```
CERTBOT_EMAIL=seu-email@exemplo.com
CERTBOT_DOMAIN=lhamabanana.com
```

### 4. Verificar se os containers estão rodando

```bash
docker-compose ps
```

Certifique-se de que `nginx` está rodando.

### 5. Executar o Script de Ativação HTTPS

```bash
# Tornar o script executável (se necessário)
chmod +x scripts/ativar-https-completo.sh
chmod +x scripts/obter-certificados-ssl.sh

# Executar o script
./scripts/ativar-https-completo.sh
```

## 🔍 O que o Script Faz

1. **Obtém certificados SSL** do Let's Encrypt
2. **Verifica se os certificados foram criados**
3. **Testa a configuração do NGINX**
4. **Recarrega o NGINX** para aplicar as mudanças
5. **Testa o HTTPS** para verificar se está funcionando

## ⚠️ Possíveis Erros e Soluções

### Erro: "CERTBOT_EMAIL não está definido"
**Solução**: Configure no arquivo `.env`:
```bash
CERTBOT_EMAIL=seu-email@exemplo.com
```

### Erro: "CERTBOT_DOMAIN não está definido"
**Solução**: Configure no arquivo `.env`:
```bash
CERTBOT_DOMAIN=lhamabanana.com
```

### Erro: "Failed to obtain certificate"
**Causas possíveis**:
- Domínio não aponta para o servidor (verificar DNS)
- Porta 80 bloqueada (verificar firewall)
- NGINX não está rodando

**Solução**:
```bash
# Verificar DNS
nslookup lhamabanana.com

# Verificar se NGINX está rodando
docker-compose ps nginx

# Verificar logs
docker-compose logs certbot
```

### Erro: "nginx: [emerg] SSL certificate not found"
**Causa**: Certificado não foi obtido ou caminho incorreto

**Solução**:
```bash
# Verificar se certificado existe
docker-compose exec certbot ls -la /etc/letsencrypt/live/

# Se não existir, obter novamente
./scripts/obter-certificados-ssl.sh
```

## 📝 Comandos Manuais (se o script falhar)

Se preferir executar manualmente:

```bash
# 1. Obter certificado
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email seu-email@exemplo.com \
    --agree-tos \
    --no-eff-email \
    -d lhamabanana.com \
    -d www.lhamabanana.com \
    --rsa-key-size 4096

# 2. Verificar certificado
docker-compose exec certbot ls -la /etc/letsencrypt/live/lhamabanana.com/

# 3. Testar configuração NGINX
docker-compose exec nginx nginx -t

# 4. Recarregar NGINX
docker-compose exec nginx nginx -s reload

# 5. Testar HTTPS
curl -I https://lhamabanana.com
```

## ✅ Verificação Final

Após executar o script, verifique:

1. **HTTPS funcionando**:
   ```bash
   curl -I https://lhamabanana.com
   ```
   Deve retornar `200 OK` ou `301 Moved Permanently`

2. **Redirecionamento HTTP → HTTPS**:
   ```bash
   curl -I http://lhamabanana.com
   ```
   Deve retornar `301 Moved Permanently` com `Location: https://...`

3. **Certificado válido no navegador**:
   - Acesse `https://lhamabanana.com` no navegador
   - Verifique se o cadeado aparece (certificado válido)

## 🔄 Renovação Automática

Os certificados são renovados automaticamente pelo container `certbot` que roda em background. Verifique os logs:

```bash
docker-compose logs certbot | grep renew
```
