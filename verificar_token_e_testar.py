#!/usr/bin/env python3
"""
Verifica token e testa busca de situações
"""
import requests
import json

base_url = "http://localhost:5000"

print("=" * 80)
print("🔍 Verificando token e testando busca de situações")
print("=" * 80)

# 1. Verificar token atual
print("\n1. Verificando token atual...")
try:
    response = requests.get(f"{base_url}/api/bling/tokens")
    if response.status_code == 200:
        data = response.json()
        print(f"   Autorizado: {data.get('authorized')}")
        print(f"   Token preview: {data.get('access_token_preview')}")
        print(f"   Última atualização: {data.get('updated_at')}")
        print(f"   Expira em: {data.get('expires_at')}")
    else:
        print(f"   Erro: {response.status_code}")
except Exception as e:
    print(f"   Erro: {e}")

# 2. Testar autenticação
print("\n2. Testando autenticação...")
try:
    response = requests.get(f"{base_url}/api/bling/test-auth")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Autenticado: {data.get('authenticated')}")
        print(f"   Mensagem: {data.get('message')}")
    else:
        data = response.json()
        print(f"   ❌ Erro: {data.get('error')}")
except Exception as e:
    print(f"   Erro: {e}")

# 3. Buscar situações
print("\n3. Buscando situações...")
try:
    response = requests.post(f"{base_url}/api/bling/situacoes/sync-ids", json={})
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Sucesso: {data.get('message')}")
        print(f"   Atualizadas: {data.get('atualizadas')}")
        print(f"   Não encontradas: {len(data.get('nao_encontradas', []))}")
        print(f"   Total encontradas no Bling: {data.get('total_encontradas_bling')}")
        
        if data.get('situacoes_encontradas'):
            print("\n   Situações encontradas:")
            for sit in data.get('situacoes_encontradas', []):
                print(f"      - ID {sit.get('id')}: {sit.get('nome')}")
    else:
        data = response.json()
        print(f"   ❌ Erro: {data.get('error')}")
except Exception as e:
    print(f"   Erro: {e}")

print("\n" + "=" * 80)
