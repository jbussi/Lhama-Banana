#!/bin/bash
# Script para corrigir problema do key.json
# Remove diretório key.json se existir dentro de Lhama-Banana

echo "Verificando key.json..."

KEY_JSON_PATH="./key.json"

if [ -e "$KEY_JSON_PATH" ]; then
    if [ -d "$KEY_JSON_PATH" ]; then
        echo "⚠️  Diretório key.json encontrado. Removendo..."
        rm -rf "$KEY_JSON_PATH"
        echo "✅ Diretório key.json removido!"
    else
        echo "✅ key.json é um arquivo (correto)"
    fi
else
    echo "ℹ️  key.json não encontrado em Lhama-Banana/ (isso é normal)"
fi

# Verificar se existe na raiz
ROOT_KEY_JSON="../key.json"
if [ -e "$ROOT_KEY_JSON" ]; then
    if [ -f "$ROOT_KEY_JSON" ]; then
        echo "✅ Arquivo key.json encontrado na raiz do workspace"
    else
        echo "❌ ERRO: key.json na raiz também é um diretório!"
    fi
else
    echo "⚠️  ATENÇÃO: key.json não encontrado na raiz do workspace"
    echo "   Coloque o arquivo key.json na raiz do workspace (mesmo nível de Lhama-Banana/)"
fi

echo ""
echo "Concluído!"

