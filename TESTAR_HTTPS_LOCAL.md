# 🧪 Guia: Testar HTTPS Localmente

## ✅ Status Atual

### Containers Funcionando
- ✅ **Flask**: Rodando e saudável (Gunicorn funcionando)
- ✅ **PostgreSQL**: Rodando e saudável
- ✅ **NGINX**: Rodando e saudável (configuração OK)
- ✅ **Strapi**: Rodando e saudável
- ✅ **Certbot**: Rodando (aguardando certificados)

### HTTP Funcionando
- ✅ Health check: `http://localhost/health` → Status 200
- ✅ Site principal: `http://localhost` → Status 200

### HTTPS
- ⏳ **Aguardando certificados SSL** (blocos HTTPS comentados temporariamente)

## 🔧 Como Obter Certificados SSL Localmente

### Opção 1: Usar ngrok (Recomendado para testes)

1. **Instalar ngrok** (se ainda não tiver):
   ```powershell
   # Baixe de: https://ngrok.com/download
   # Ou via chocolatey: choco install ngrok
   ```

2. **Iniciar ngrok** expondo a porta 80:
   ```powershell
   ngrok http 80
   ```
   
   Você verá algo como:
   ```
   Forwarding  https://abc123.ngrok-free.dev -> http://localhost:80
   ```

3. **Configurar no `.env`**:
   ```bash
   CERTBOT_EMAIL=seu-email@exemplo.com
   CERTBOT_DOMAIN=abc123.ngrok-free.dev  # Use a URL HTTPS do ngrok
   ```

4. **Obter certificado SSL**:
   ```powershell
   cd Lhama-Banana
   .\scripts\obter-certificados-local.ps1
   ```

5. **Descomentar blocos HTTPS** no `nginx/nginx.conf`:
   - Linhas 207-302: Site Principal (HTTPS)
   - Linhas 334-388: API (HTTPS)
   - Linhas 419-466: Admin (HTTPS)

6. **Recarregar NGINX**:
   ```powershell
   docker-compose exec nginx nginx -s reload
   ```

7. **Testar HTTPS**:
   ```powershell
   # No PowerShell (pode mostrar aviso de certificado staging)
   Invoke-WebRequest -Uri "https://abc123.ngrok-free.dev" -SkipCertificateCheck
   ```

### Opção 2: Certificados Auto-Assinados (Apenas para testes locais)

Para testes rápidos sem ngrok, você pode criar certificados auto-assinados:

```powershell
# Criar diretório para certificados
docker-compose exec certbot mkdir -p /etc/letsencrypt/live/localhost

# Gerar certificado auto-assinado (dentro do container)
docker-compose exec certbot openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/letsencrypt/live/localhost/privkey.pem \
    -out /etc/letsencrypt/live/localhost/fullchain.pem \
    -subj "/CN=localhost"

# Copiar fullchain como chain
docker-compose exec certbot cp /etc/letsencrypt/live/localhost/fullchain.pem /etc/letsencrypt/live/localhost/chain.pem
```

**Nota**: Certificados auto-assinados mostrarão aviso no navegador.

## 📋 Checklist de Testes

- [x] Flask rodando e saudável
- [x] NGINX rodando e saudável
- [x] HTTP funcionando (localhost)
- [ ] ngrok configurado e rodando
- [ ] Certificados SSL obtidos
- [ ] Blocos HTTPS descomentados
- [ ] NGINX recarregado
- [ ] HTTPS testado e funcionando

## 🚀 Comandos Úteis

```powershell
# Ver status dos containers
docker-compose ps

# Ver logs do Flask
docker-compose logs flask --tail 50

# Ver logs do NGINX
docker-compose logs nginx --tail 50

# Testar configuração NGINX
docker-compose exec nginx nginx -t

# Recarregar NGINX
docker-compose exec nginx nginx -s reload

# Verificar certificados
docker-compose exec certbot ls -la /etc/letsencrypt/live/

# Testar HTTP
Invoke-WebRequest -Uri "http://localhost/health" -Method Head

# Testar HTTPS (após obter certificados)
Invoke-WebRequest -Uri "https://seu-dominio.ngrok-free.dev" -SkipCertificateCheck
```

## ⚠️ Importante

1. **Certificados Staging**: Os certificados obtidos com `--staging` são apenas para testes e mostrarão aviso no navegador.

2. **ngrok**: A URL do ngrok muda a cada reinício (no plano gratuito). Use um domínio fixo ou atualize o `.env` sempre que reiniciar.

3. **Produção**: Para produção, remova `--staging` e use o domínio real apontando para o servidor.

## 🎯 Próximos Passos

1. Configure ngrok e obtenha a URL HTTPS
2. Execute `.\scripts\obter-certificados-local.ps1`
3. Descomente os blocos HTTPS no `nginx/nginx.conf`
4. Recarregue o NGINX
5. Teste HTTPS no navegador
