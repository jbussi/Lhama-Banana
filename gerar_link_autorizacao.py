#!/usr/bin/env python3
"""
Script para gerar link direto de autorização do Bling
"""
import sys
import os
from urllib.parse import urlencode

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object(Config)

# URLs fixas do Bling
BLING_AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"

# Scopes necessários
BLING_SCOPES = [
    'produtos',      # Gerenciar produtos
    'pedidos',       # Gerenciar pedidos de venda
    'nfe',           # Emitir NF-e
    'estoques',      # Controlar estoque
    'contatos',      # Gerenciar clientes
    'financeiro'     # Contas a receber/pagar
]

# Obter credenciais
client_id = app.config.get('BLING_CLIENT_ID')
redirect_uri = app.config.get('BLING_REDIRECT_URI')

print("=" * 80)
print("🔗 Gerador de Link de Autorização Bling")
print("=" * 80)

if not client_id:
    print("\n❌ ERRO: BLING_CLIENT_ID não configurado")
    print("   Configure a variável de ambiente BLING_CLIENT_ID")
    sys.exit(1)

if not redirect_uri:
    print("\n❌ ERRO: BLING_REDIRECT_URI não configurado")
    print("   Configure a variável de ambiente BLING_REDIRECT_URI")
    sys.exit(1)

print(f"\n📋 Configuração:")
print(f"   Client ID: {client_id[:20]}...")
print(f"   Redirect URI: {redirect_uri}")

# Gerar state token simples (sem sessão)
import secrets
state = secrets.token_urlsafe(32)

# Parâmetros para autorização
params = {
    'response_type': 'code',
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'scope': ' '.join(BLING_SCOPES),
    'state': state
}

# Construir URL de autorização
auth_url = f"{BLING_AUTH_URL}?{urlencode(params)}"

print(f"\n✅ Link de autorização gerado:")
print("=" * 80)
print(auth_url)
print("=" * 80)

print(f"\n📝 Instruções:")
print(f"   1. Copie o link acima")
print(f"   2. Cole no navegador e pressione Enter")
print(f"   3. Faça login no Bling")
print(f"   4. Autorize a aplicação")
print(f"   5. Você será redirecionado automaticamente")

print(f"\n💡 State Token (para referência): {state[:16]}...")
print(f"\n⚠️  NOTA: O state token é gerado automaticamente pelo sistema.")
print(f"   Se você usar este link diretamente, o callback pode não validar o state.")
print(f"   Use o endpoint /api/bling/authorize quando possível.")
