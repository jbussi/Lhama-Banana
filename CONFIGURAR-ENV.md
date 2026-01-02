# ⚙️ Configuração do Arquivo .env

Para configurar o projeto, você precisa criar um arquivo `.env` na raiz do projeto.

## Método 1: Usando Script (Recomendado)

### Windows (PowerShell)
```powershell
.\setup-env.ps1
```

### Linux/Mac
```bash
chmod +x setup-env.sh
./setup-env.sh
```

## Método 2: Manual

Copie o arquivo `env.example` para `.env`:

### Windows (PowerShell)
```powershell
Copy-Item env.example .env
```

### Linux/Mac
```bash
cp env.example .env
```

## Configuração

O arquivo `.env` já está pré-configurado com valores funcionais. Você pode ajustar se necessário:

- **Tokens do PagBank e Melhor Envio**: Já estão configurados
- **Chaves do Strapi**: Valores padrão funcionais
- **Banco de dados**: Configurado para usar o PostgreSQL do Docker

## Próximo Passo

Após criar o `.env`, execute:

```bash
docker compose up -d
```

Isso irá subir todos os serviços (PostgreSQL, Flask e Strapi).

