#!/usr/bin/env python3
"""
Verifica se a situação "Verificado" existe e está disponível no Bling
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_situacao_service import get_bling_situacao_by_id
from blueprints.services.bling_api_service import make_bling_api_request

app = Flask(__name__)
app.config.from_object('config.Config')

init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🔍 Verificando situação 'Verificado' no Bling")
    print("=" * 80)
    
    # Verificar situação ID 24 diretamente
    print("\n1. Buscando situação ID 24 diretamente...")
    try:
        situacao = get_bling_situacao_by_id(24)
        if situacao:
            print(f"   ✅ Situação encontrada:")
            print(f"      ID: {situacao.get('id')}")
            print(f"      Nome: {situacao.get('nome')}")
            print(f"      Cor: {situacao.get('cor')}")
        else:
            print(f"   ❌ Situação ID 24 não encontrada")
    except Exception as e:
        print(f"   ❌ Erro ao buscar: {e}")
    
    # Buscar pedidos para ver quais situações estão disponíveis
    print("\n2. Buscando pedidos para ver situações disponíveis...")
    try:
        response = make_bling_api_request('GET', '/pedidos/vendas', params={'limite': 10})
        if response.status_code == 200:
            data = response.json()
            pedidos = data.get('data', [])
            
            situacoes_encontradas = {}
            for pedido in pedidos:
                situacao = pedido.get('situacao', {})
                if situacao:
                    situacao_id = situacao.get('id')
                    situacao_nome = situacao.get('nome', '').strip()
                    if situacao_id:
                        situacoes_encontradas[situacao_id] = situacao_nome or '(sem nome)'
            
            print(f"   ✅ Situações encontradas nos pedidos:")
            for situacao_id, nome in sorted(situacoes_encontradas.items()):
                print(f"      ID {situacao_id}: {nome}")
    except Exception as e:
        print(f"   ❌ Erro ao buscar pedidos: {e}")
    
    # Tentar buscar informações sobre situações disponíveis
    print("\n3. Verificando se há endpoint para listar situações...")
    try:
        # Tentar endpoint alternativo
        response = make_bling_api_request('GET', '/situacoes-vendas')
        if response.status_code == 200:
            data = response.json()
            situacoes = data.get('data', [])
            print(f"   ✅ Encontradas {len(situacoes)} situações via endpoint /situacoes-vendas")
            for situacao in situacoes[:10]:  # Mostrar primeiras 10
                print(f"      ID {situacao.get('id')}: {situacao.get('nome')}")
        else:
            print(f"   ⚠️  Endpoint /situacoes-vendas retornou status {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Endpoint /situacoes-vendas não disponível: {e}")
    
    # Verificar no banco local
    print("\n4. Verificando no banco local...")
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT bling_situacao_id, nome, status_site, ativo
            FROM bling_situacoes
            WHERE nome = 'Verificado' OR bling_situacao_id = 24
        """)
        
        situacao_local = cur.fetchone()
        if situacao_local:
            print(f"   ✅ Situação no banco local:")
            print(f"      ID: {situacao_local[0]}")
            print(f"      Nome: {situacao_local[1]}")
            print(f"      Status Site: {situacao_local[2]}")
            print(f"      Ativo: {situacao_local[3]}")
        else:
            print(f"   ❌ Situação 'Verificado' não encontrada no banco local")
    except Exception as e:
        print(f"   ❌ Erro ao buscar no banco: {e}")
    finally:
        cur.close()
    
    print("\n" + "=" * 80)
    print("💡 POSSÍVEIS CAUSAS:")
    print("=" * 80)
    print("1. A situação 'Verificado' pode não estar habilitada para pedidos de venda")
    print("2. Pode haver uma regra de negócio no Bling que impede essa transição")
    print("3. A situação pode estar disponível apenas para outros tipos de documentos")
    print("4. Pode ser necessário configurar a situação no painel do Bling")
    print("5. O ID 24 pode não corresponder a 'Verificado' na sua conta Bling")
    print("\n💡 SOLUÇÕES:")
    print("1. Verificar no painel do Bling se a situação está habilitada")
    print("2. Verificar se há alguma regra de transição de status configurada")
    print("3. Tentar atualizar o pedido via API para ver se funciona")
    print("=" * 80)
