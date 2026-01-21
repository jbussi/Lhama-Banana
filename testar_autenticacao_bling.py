#!/usr/bin/env python3
"""
Script para testar autenticação do Bling
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_api_service import get_valid_access_token, make_bling_api_request
from datetime import datetime

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar pool de conexões
init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🧪 Testando Autenticação Bling")
    print("=" * 80)
    
    # Teste 1: Verificar token no banco
    print("\n📝 TESTE 1: Verificando token no banco de dados...")
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT expires_at, updated_at, 
                   CASE WHEN expires_at > NOW() THEN 'VÁLIDO' ELSE 'EXPIRADO' END as status
            FROM bling_tokens
            WHERE id = 1
        """)
        
        token_info = cur.fetchone()
        
        if token_info:
            expires_at, updated_at, status = token_info
            print(f"   Status: {status}")
            print(f"   Expira em: {expires_at}")
            print(f"   Última atualização: {updated_at}")
        else:
            print("   ❌ Nenhum token encontrado no banco")
            print("   💡 É necessário autorizar primeiro via /api/bling/authorize")
            sys.exit(1)
    finally:
        cur.close()
    
    # Teste 2: Tentar obter token válido (pode tentar renovar)
    print("\n📝 TESTE 2: Obtendo token válido (pode tentar renovar automaticamente)...")
    try:
        token = get_valid_access_token()
        print(f"   ✅ Token obtido com sucesso: {token[:20]}...")
    except Exception as e:
        print(f"   ❌ Erro ao obter token: {e}")
        print("\n💡 SOLUÇÃO:")
        print("   1. Renove o token manualmente via navegador:")
        print("      https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=b2bc093daf984f6263de746701dde7b1b7d23cea&redirect_uri=https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/callback&scope=produtos%20pedidos%20nfe%20estoques%20contatos%20financeiro")
        print("   2. Ou aguarde o rate limiting passar e tente novamente")
        sys.exit(1)
    
    # Teste 3: Fazer requisição de teste à API do Bling
    print("\n📝 TESTE 3: Testando requisição à API do Bling...")
    try:
        # Tentar buscar uma situação (endpoint simples)
        response = make_bling_api_request('GET', '/situacoes/1')
        
        if response.status_code == 200:
            print(f"   ✅ Requisição bem-sucedida! Status: {response.status_code}")
            data = response.json()
            if data.get('data'):
                situacao = data['data']
                print(f"   📋 Situação encontrada: ID {situacao.get('id')} - {situacao.get('nome')}")
        elif response.status_code == 404:
            print(f"   ⚠️  Endpoint não encontrado (404) - mas autenticação funcionou!")
            print(f"   Isso é normal se a situação ID 1 não existir")
        elif response.status_code == 401:
            print(f"   ❌ Erro de autenticação (401)")
            print(f"   Token pode estar inválido ou expirado")
        else:
            print(f"   ⚠️  Status HTTP: {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Erro na requisição: {e}")
        import traceback
        traceback.print_exc()
    
    # Teste 4: Verificar token novamente após tentativas
    print("\n📝 TESTE 4: Verificando token após tentativas...")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT expires_at, updated_at,
                   CASE WHEN expires_at > NOW() THEN 'VÁLIDO' ELSE 'EXPIRADO' END as status
            FROM bling_tokens
            WHERE id = 1
        """)
        
        token_info_after = cur.fetchone()
        
        if token_info_after:
            expires_at, updated_at, status = token_info_after
            print(f"   Status: {status}")
            print(f"   Expira em: {expires_at}")
            print(f"   Última atualização: {updated_at}")
            
            # Comparar com antes
            if updated_at != token_info[1]:
                print(f"   ✅ Token foi atualizado durante os testes!")
            else:
                print(f"   ℹ️  Token não foi atualizado")
        cur.close()
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar token: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Teste concluído!")
    print("=" * 80)
