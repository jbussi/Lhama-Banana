# 🚀 Executar Ativação HTTPS via PowerShell

## 📋 Pré-requisitos

1. **OpenSSH Client instalado no Windows**
   - Windows 10/11: Já vem instalado (verificar em Settings > Apps > Optional Features)
   - Ou instale via: `Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0`

2. **Acesso SSH ao servidor**
   - IP do servidor ou domínio
   - Usuário SSH
   - Senha ou chave SSH

3. **Arquivo `.env` configurado no servidor** com:
   ```bash
   CERTBOT_EMAIL=seu-email@exemplo.com
   CERTBOT_DOMAIN=lhamabanana.com
   ```

## 🎯 Opção 1: Script Interativo (Recomendado)

Execute o script interativo que solicita todas as informações:

```powershell
cd Lhama-Banana
.\scripts\ativar-https-interativo.ps1
```

O script vai perguntar:
- IP do servidor
- Usuário SSH
- Caminho do projeto (ou usar padrão)
- Se quer usar chave SSH

## 🎯 Opção 2: Script com Parâmetros

Execute diretamente com parâmetros:

```powershell
cd Lhama-Banana
.\scripts\ativar-https.ps1 `
    -ServerIP "192.168.1.100" `
    -Username "root" `
    -ProjectPath "/opt/lhama-banana/Lhama-Banana"
```

### Com chave SSH:

```powershell
.\scripts\ativar-https.ps1 `
    -ServerIP "192.168.1.100" `
    -Username "root" `
    -ProjectPath "/opt/lhama-banana/Lhama-Banana" `
    -SSHKey "C:\Users\usuario\.ssh\id_rsa"
```

## 📝 Exemplo Completo

```powershell
# Navegar para o diretório do projeto
cd C:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\Lhama-Banana

# Executar script interativo
.\scripts\ativar-https-interativo.ps1
```

## 🔍 O que o Script Faz

1. **Verifica conexão SSH** com o servidor
2. **Conecta ao servidor** via SSH
3. **Executa no servidor**:
   - Verifica arquivo `.env`
   - Verifica se NGINX está rodando
   - Obtém certificados SSL do Let's Encrypt
   - Verifica certificados obtidos
   - Testa configuração do NGINX
   - Recarrega NGINX
   - Testa HTTPS

## ⚠️ Troubleshooting

### Erro: "SSH não está disponível"

**Solução**: Instale OpenSSH Client:
```powershell
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### Erro: "Não foi possível conectar ao servidor na porta 22"

**Causas**:
- Servidor não está acessível
- Porta 22 bloqueada
- IP/domínio incorreto

**Solução**:
```powershell
# Testar conexão
Test-NetConnection -ComputerName IP_DO_SERVIDOR -Port 22
```

### Erro: "Permission denied"

**Causas**:
- Credenciais incorretas
- Chave SSH incorreta
- Usuário sem permissões

**Solução**:
- Verifique usuário e senha
- Verifique caminho da chave SSH
- Teste conexão manual: `ssh usuario@ip`

### Erro: "CERTBOT_EMAIL não está definido"

**Solução**: Configure no arquivo `.env` do servidor:
```bash
CERTBOT_EMAIL=seu-email@exemplo.com
CERTBOT_DOMAIN=lhamabanana.com
```

### Erro: "Failed to obtain certificate"

**Causas**:
- Domínio não aponta para o servidor
- Porta 80 bloqueada
- NGINX não está acessível externamente

**Solução**:
1. Verifique DNS: `nslookup lhamabanana.com`
2. Verifique firewall (porta 80 deve estar aberta)
3. Verifique se NGINX está rodando: `docker-compose ps nginx`

## 🔐 Segurança

- **Não compartilhe** suas credenciais SSH
- **Use chaves SSH** em vez de senhas quando possível
- **Mantenha** o arquivo `.env` seguro no servidor

## 📊 Verificar Resultado

Após executar o script, verifique:

1. **HTTPS funcionando**:
   ```powershell
   Invoke-WebRequest -Uri "https://lhamabanana.com" -Method Head
   ```

2. **Redirecionamento HTTP → HTTPS**:
   ```powershell
   Invoke-WebRequest -Uri "http://lhamabanana.com" -Method Head
   ```
   Deve retornar `301 Moved Permanently`

3. **Certificado válido no navegador**:
   - Acesse `https://lhamabanana.com`
   - Verifique o cadeado verde

## 🆘 Ajuda Adicional

Se encontrar problemas:

1. **Ver logs do servidor**:
   ```powershell
   ssh usuario@ip "cd /opt/lhama-banana/Lhama-Banana && docker-compose logs certbot"
   ```

2. **Testar conexão manual**:
   ```powershell
   ssh usuario@ip
   ```

3. **Executar comandos manualmente no servidor**:
   ```bash
   cd /opt/lhama-banana/Lhama-Banana
   ./scripts/executar-https-servidor.sh
   ```
