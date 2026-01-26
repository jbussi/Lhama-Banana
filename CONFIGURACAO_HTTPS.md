# 🔒 Guia Completo: Configuração HTTPS/SSL - LhamaBanana

## 📋 Visão Geral

Este guia explica como configurar HTTPS/SSL usando Let's Encrypt (Certbot) para os domínios:
- **Site Principal**: `lhamabanana.com` e `www.lhamabanana.com`
- **API**: `api.lhamabanana.com`
- **Admin**: `admin.lhamabanana.com`

## ✅ Pré-requisitos

1. **Domínios apontando para o servidor**
   - `lhamabanana.com` → IP do servidor
   - `www.lhamabanana.com` → IP do servidor
   - `api.lhamabanana.com` → IP do servidor
   - `admin.lhamabanana.com` → IP do servidor

2. **Porta 80 aberta** (necessária para validação do Let's Encrypt)

3. **Variáveis de ambiente configuradas**:
   ```bash
   CERTBOT_EMAIL=seu-email@exemplo.com
   CERTBOT_DOMAIN=lhamabanana.com
   ```

## 🔧 Passo a Passo

### 1. Configurar Variáveis de Ambiente

No arquivo `.env` do servidor:

```bash
# Certbot (Let's Encrypt)
CERTBOT_EMAIL=seu-email@exemplo.com
CERTBOT_DOMAIN=lhamabanana.com
```

**Importante**: 
- Use um email válido (receberá notificações de renovação)
- Use o domínio principal (sem www)

### 2. Verificar se NGINX está Rodando

```bash
docker-compose ps nginx
```

Se não estiver rodando:
```bash
docker-compose up -d nginx
```

### 3. Obter Certificados SSL

#### Opção A: Usando Script Automático (Recomendado)

```bash
cd /opt/lhama-banana/Lhama-Banana
./scripts/setup-ssl.sh
```

#### Opção B: Manual

```bash
# Obter certificado para domínio principal
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email seu-email@exemplo.com \
    --agree-tos \
    --no-eff-email \
    -d lhamabanana.com \
    -d www.lhamabanana.com \
    --rsa-key-size 4096

# Obter certificado para API (se usar subdomínio separado)
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email seu-email@exemplo.com \
    --agree-tos \
    --no-eff-email \
    -d api.lhamabanana.com \
    --rsa-key-size 4096

# Obter certificado para Admin (se usar subdomínio separado)
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email seu-email@exemplo.com \
    --agree-tos \
    --no-eff-email \
    -d admin.lhamabanana.com \
    --rsa-key-size 4096
```

**Nota**: Para teste (sem limites do Let's Encrypt), adicione `--staging` antes de `certonly`.

### 4. Verificar Certificados Obtidos

```bash
# Listar certificados
docker-compose exec certbot ls -la /etc/letsencrypt/live/

# Verificar certificado específico
docker-compose exec certbot ls -la /etc/letsencrypt/live/lhamabanana.com/
```

Você deve ver:
- `fullchain.pem` - Certificado completo
- `privkey.pem` - Chave privada
- `chain.pem` - Cadeia de certificados

### 5. Configurar NGINX para HTTPS

#### 5.1. Descomentar Blocos HTTPS

Edite `nginx/nginx.conf` e descomente os blocos HTTPS:

1. **Site Principal** (linhas 249-345)
2. **API** (linhas 389-443)
3. **Admin** (linhas 491-561)

#### 5.2. Ajustar Caminhos dos Certificados

Os caminhos já estão corretos:
```nginx
ssl_certificate /etc/letsencrypt/live/lhamabanana.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/lhamabanana.com/privkey.pem;
ssl_trusted_certificate /etc/letsencrypt/live/lhamabanana.com/chain.pem;
```

**Se usar subdomínios separados**, ajuste:
- `api.lhamabanana.com` → `/etc/letsencrypt/live/api.lhamabanana.com/`
- `admin.lhamabanana.com` → `/etc/letsencrypt/live/admin.lhamabanana.com/`

#### 5.3. Adicionar Redirecionamento HTTP → HTTPS

No bloco HTTP (linha 185), adicione redirecionamento:

```nginx
server {
    listen 80;
    server_name lhamabanana.com www.lhamabanana.com;

    # Certbot challenge (manter para renovação)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirecionar tudo para HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}
```

### 6. Recarregar NGINX

```bash
# Testar configuração
docker-compose exec nginx nginx -t

# Se OK, recarregar
docker-compose exec nginx nginx -s reload

# Ou reiniciar container
docker-compose restart nginx
```

### 7. Verificar HTTPS

```bash
# Testar site principal
curl -I https://lhamabanana.com

# Verificar certificado
openssl s_client -connect lhamabanana.com:443 -servername lhamabanana.com
```

## 🔄 Renovação Automática

O Certbot já está configurado para renovar automaticamente (linha 151 do `docker-compose.yml`):

```yaml
entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```

**Como funciona**:
- Verifica certificados a cada 12 horas
- Renova automaticamente se estiver próximo do vencimento (30 dias)
- Recarrega NGINX após renovação

**Verificar renovações**:
```bash
docker-compose logs certbot | grep renew
```

## 🧪 Modo Staging (Teste)

Para testar sem limites do Let's Encrypt:

```bash
# No .env
CERTBOT_STAGING=1

# Ou no comando
docker-compose run --rm certbot certonly \
    --staging \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email seu-email@exemplo.com \
    --agree-tos \
    -d lhamabanana.com \
    -d www.lhamabanana.com
```

**Importante**: Certificados de staging não são confiáveis pelo navegador, mas permitem testar o processo.

## ⚠️ Troubleshooting

### Erro: "Failed to obtain certificate"

**Causas comuns**:
1. Domínio não aponta para o servidor
2. Porta 80 bloqueada
3. Firewall bloqueando Let's Encrypt

**Solução**:
```bash
# Verificar DNS
nslookup lhamabanana.com

# Verificar porta 80
curl -I http://lhamabanana.com/.well-known/acme-challenge/test

# Verificar logs
docker-compose logs certbot
```

### Erro: "Certificate already exists"

**Solução**:
```bash
# Remover certificado antigo
docker-compose exec certbot rm -rf /etc/letsencrypt/live/lhamabanana.com
docker-compose exec certbot rm -rf /etc/letsencrypt/archive/lhamabanana.com
docker-compose exec certbot rm -rf /etc/letsencrypt/renewal/lhamabanana.com.conf

# Obter novamente
docker-compose run --rm certbot certonly ...
```

### Erro: "nginx: [emerg] SSL certificate not found"

**Causa**: Certificado não existe ou caminho incorreto

**Solução**:
```bash
# Verificar se certificado existe
docker-compose exec certbot ls -la /etc/letsencrypt/live/

# Verificar caminho no nginx.conf
grep ssl_certificate nginx/nginx.conf
```

### Erro: "Too many requests"

**Causa**: Limite do Let's Encrypt (5 certificados por domínio por semana)

**Solução**:
- Use `--staging` para testes
- Aguarde 1 semana
- Use um domínio diferente para testes

## 📝 Checklist de Configuração

- [ ] Domínios apontando para o servidor
- [ ] Porta 80 aberta e acessível
- [ ] Variáveis `CERTBOT_EMAIL` e `CERTBOT_DOMAIN` configuradas
- [ ] NGINX rodando e acessível via HTTP
- [ ] Certificados obtidos com sucesso
- [ ] Blocos HTTPS descomentados no `nginx.conf`
- [ ] Caminhos dos certificados corretos
- [ ] Redirecionamento HTTP → HTTPS configurado
- [ ] NGINX recarregado sem erros
- [ ] HTTPS funcionando (testado no navegador)
- [ ] Renovação automática funcionando

## 🔐 Segurança Adicional

Após configurar HTTPS, considere:

1. **HSTS (HTTP Strict Transport Security)**
   - Já configurado nos blocos HTTPS
   - Força navegadores a usar sempre HTTPS

2. **Rate Limiting**
   - Descomentar `limit_req` nos blocos HTTPS
   - Proteção contra DDoS

3. **Bloquear Acesso por IP**
   - Descomentar bloco `default_server` que retorna 444
   - Força uso de domínio válido

4. **Headers de Segurança**
   - Já configurados nos blocos HTTPS
   - X-Frame-Options, CSP, etc.

## 📚 Referências

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/)
- [NGINX SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
