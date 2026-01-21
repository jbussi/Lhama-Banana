#!/usr/bin/env python3
"""
Script para renovar token via endpoint da API Flask
"""
import requests
import json

# Endpoint da API Flask
url = "http://localhost:5000/api/bling/refresh-token"

print("=" * 80)
print("🔄 Renovando Token Bling via Endpoint da API")
print("=" * 80)
print(f"\n📡 Chamando: POST {url}")

try:
    response = requests.post(url, timeout=30)
    
    print(f"\n📊 Status: HTTP {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Token renovado com sucesso!")
        print(f"\n📋 Detalhes:")
        print(f"   Expira em: {data.get('expires_at', 'N/A')}")
        print(f"   Expira em (segundos): {data.get('expires_in', 'N/A')}")
        print(f"\n💡 Agora você pode executar:")
        print(f"   docker-compose exec -T flask python renovar_token_e_sincronizar.py")
    elif response.status_code == 401:
        print("❌ Não autorizado. É necessário estar autenticado como admin.")
        print("   O endpoint requer autenticação admin.")
    elif response.status_code == 400:
        data = response.json()
        print(f"❌ Erro: {data.get('error', 'Erro desconhecido')}")
        if 'authorize_url' in data:
            print(f"\n💡 Solução: Renove manualmente via navegador:")
            print(f"   {data.get('authorize_url')}")
    elif response.status_code == 429:
        print("⚠️  Rate limiting ainda ativo.")
        print("   Aguarde mais alguns minutos ou renove manualmente via navegador:")
        print("   http://localhost:5000/api/bling/authorize")
    elif response.status_code == 500:
        data = response.json()
        print(f"❌ Erro interno: {data.get('error', 'Erro desconhecido')}")
        if 'expires_at' in data:
            print(f"   Token expira em: {data.get('expires_at')}")
    else:
        print(f"❌ Resposta inesperada:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text[:500])
            
except requests.exceptions.ConnectionError:
    print("❌ Erro: Não foi possível conectar ao servidor Flask.")
    print("   Verifique se o servidor está rodando em http://localhost:5000")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
