# 🔧 Correção do Problema key.json

## Problema

Se você está vendo o erro:
```
❌ ERRO: O caminho especificado é um diretório, não um arquivo: /app/key.json
```

Isso significa que há um **diretório** chamado `key.json` dentro de `Lhama-Banana/` que está conflitando com o arquivo `key.json` da raiz.

## Solução

### 1. Remover o diretório key.json (se existir)

**Windows PowerShell:**
```powershell
cd Lhama-Banana
if (Test-Path key.json -PathType Container) {
    Remove-Item -Recurse -Force key.json
    Write-Host "Diretório key.json removido"
}
```

**Linux/Mac:**
```bash
cd Lhama-Banana
if [ -d key.json ]; then
    rm -rf key.json
    echo "Diretório key.json removido"
fi
```

### 2. Verificar que o arquivo key.json existe na raiz

O arquivo `key.json` deve estar em:
```
LhamaBanana_visual_estatica_corrigida/
└── key.json  ← Aqui (raiz do workspace)
```

**NÃO** deve estar em:
```
Lhama-Banana/
└── key.json/  ← NÃO deve ser um diretório aqui
```

### 3. Reiniciar os containers

```bash
docker compose down
docker compose up -d
```

## Verificação

Após corrigir, o Flask deve iniciar sem o erro. Você verá:

```
✅ Firebase Admin SDK inicializado com sucesso!
```

Ao invés de:

```
❌ ERRO: O caminho especificado é um diretório...
```

