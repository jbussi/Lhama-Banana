#!/usr/bin/env python3
"""
Testa busca de situações com novo token
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_api_service import get_valid_access_token, make_bling_api_request
from blueprints.services.bling_situacao_service import get_bling_situacao_by_id

app = Flask(__name__)
app.config.from_object('config.Config')

init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🧪 Testando busca de situações com novo token")
    print("=" * 80)
    
    try:
        # Obter token
        print("\n1. Obtendo token...")
        token = get_valid_access_token()
        print(f"   ✅ Token obtido: {token[:30]}...")
        
        # Testar busca de situação ID 6
        print("\n2. Testando busca de situação ID 6...")
        try:
            situacao = get_bling_situacao_by_id(6)
            if situacao:
                print(f"   ✅ Encontrada: {situacao}")
            else:
                print("   ❌ Não encontrada")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
        
        # Testar busca de situação ID 1
        print("\n3. Testando busca de situação ID 1...")
        try:
            situacao = get_bling_situacao_by_id(1)
            if situacao:
                print(f"   ✅ Encontrada: {situacao}")
            else:
                print("   ❌ Não encontrada")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
        
        # Buscar pedidos para descobrir mais IDs
        print("\n4. Buscando pedidos para descobrir IDs de situações...")
        try:
            response = make_bling_api_request('GET', '/pedidos/vendas', params={'limite': 20})
            if response.status_code == 200:
                data = response.json()
                pedidos = data.get('data', [])
                
                situacoes_encontradas = {}
                for pedido in pedidos:
                    situacao = pedido.get('situacao', {})
                    if situacao:
                        situacao_id = situacao.get('id')
                        if situacao_id:
                            # Tentar buscar nome da situação
                            try:
                                situacao_detalhada = get_bling_situacao_by_id(situacao_id)
                                if situacao_detalhada:
                                    nome = situacao_detalhada.get('nome', '')
                                    situacoes_encontradas[situacao_id] = nome
                                    print(f"   ✅ ID {situacao_id}: {nome}")
                            except Exception as e:
                                print(f"   ⚠️  ID {situacao_id}: Erro ao buscar nome - {e}")
                
                print(f"\n   Total de situações únicas encontradas: {len(situacoes_encontradas)}")
            else:
                print(f"   ❌ Erro HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("✅ Teste concluído!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
