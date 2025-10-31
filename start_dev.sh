#!/bin/bash

# Script para iniciar a aplicação em modo de desenvolvimento

echo "🚀 Iniciando LhamaBanana em modo de desenvolvimento..."
echo "=================================================="

# Definir variáveis de ambiente
export FLASK_DEBUG=1
export FLASK_ENV=development

# Navegar para o diretório correto
cd "$(dirname "$0")"

echo "📁 Diretório: $(pwd)"
echo "🔧 Modo Debug: Ativado"
echo "🌐 Servidor: http://127.0.0.1:5000"
echo "=================================================="
echo "📋 Rotas disponíveis:"
echo "   • Home: http://127.0.0.1:5000/"
echo "   • Loja: http://127.0.0.1:5000/produtos/"
echo "   • Carrinho: http://127.0.0.1:5000/carrinho"
echo "   • Checkout: http://127.0.0.1:5000/checkout"
echo "   • Login: http://127.0.0.1:5000/auth/login"
echo "=================================================="
echo "💡 Pressione Ctrl+C para parar o servidor"
echo "=================================================="

# Executar aplicação
python app.py
