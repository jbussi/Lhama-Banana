#!/bin/bash
# Script para criar arquivo .env a partir do env.example

if [ -f .env ]; then
    echo "⚠️  Arquivo .env já existe. Deseja sobrescrever? (s/N)"
    read -r response
    if [[ ! "$response" =~ ^[Ss]$ ]]; then
        echo "Operação cancelada."
        exit 0
    fi
fi

cp env.example .env
echo "✅ Arquivo .env criado com sucesso!"
echo "📝 Edite o arquivo .env com suas configurações se necessário."

