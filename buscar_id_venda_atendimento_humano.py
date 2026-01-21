#!/usr/bin/env python3
"""
Busca o ID real da situação "Venda Atendimento Humano" através de pedidos
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_api_service import make_bling_api_request
import psycopg2.extras

app = Flask(__name__)
app.config.from_object('config.Config')

init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🔍 Buscando ID da situação 'Venda Atendimento Humano' através de pedidos")
    print("=" * 80)
    
    try:
        # Buscar pedidos no Bling
        print("\n📡 Buscando pedidos no Bling...")
        response = make_bling_api_request('GET', '/pedidos/vendas', params={'limite': 100})
        
        if response.status_code == 200:
            data = response.json()
            pedidos = data.get('data', [])
            
            print(f"✅ Encontrados {len(pedidos)} pedidos\n")
            
            situacoes_encontradas = {}
            todas_situacoes = {}
            
            print("📋 Situações encontradas nos pedidos:\n")
            for pedido in pedidos:
                situacao = pedido.get('situacao', {})
                if situacao:
                    situacao_id = situacao.get('id')
                    situacao_nome = situacao.get('nome', '').strip()
                    
                    if situacao_id:
                        # Armazenar todas as situações encontradas
                        todas_situacoes[situacao_id] = situacao_nome
                        
                        # Normalizar nome para comparação
                        nome_lower = situacao_nome.lower() if situacao_nome else ''
                        
                        # Verificar se é "Venda Atendimento Humano" ou similar
                        if 'atendimento humano' in nome_lower or 'venda atendimento' in nome_lower:
                            situacoes_encontradas[situacao_id] = {
                                'id': situacao_id,
                                'nome': situacao_nome,
                                'pedido_id': pedido.get('id'),
                                'numero': pedido.get('numero')
                            }
                            print(f"   ✅ Pedido #{pedido.get('numero')}: Situação ID {situacao_id} - '{situacao_nome}'")
                        else:
                            nome_display = situacao_nome if situacao_nome else "(sem nome)"
                            print(f"   ℹ️  Pedido #{pedido.get('numero')}: Situação ID {situacao_id} - '{nome_display}'")
            
            print(f"\n📊 Resumo de todas as situações encontradas:")
            for situacao_id, nome in todas_situacoes.items():
                print(f"   ID {situacao_id}: {nome or '(sem nome)'}")
            
            if situacoes_encontradas:
                print(f"\n✅ Encontrada situação 'Venda Atendimento Humano':")
                for situacao_id, dados in situacoes_encontradas.items():
                    print(f"   ID: {dados['id']}")
                    print(f"   Nome: {dados['nome']}")
                    print(f"   Encontrada no pedido: #{dados['numero']}")
                
                # Atualizar no banco
                print("\n🔄 Atualizando no banco...")
                conn = get_db()
                cur = conn.cursor()
                
                try:
                    for situacao_id, dados in situacoes_encontradas.items():
                        cur.execute("""
                            UPDATE bling_situacoes
                            SET bling_situacao_id = %s,
                                atualizado_em = NOW()
                            WHERE nome = 'Venda Atendimento Humano'
                        """, (situacao_id,))
                        
                        if cur.rowcount > 0:
                            print(f"   ✅ Situação 'Venda Atendimento Humano' atualizada: ID temporário → {situacao_id}")
                        else:
                            print(f"   ⚠️  Nenhuma situação 'Venda Atendimento Humano' encontrada no banco para atualizar")
                    
                    conn.commit()
                    
                except Exception as e:
                    conn.rollback()
                    print(f"   ❌ Erro ao atualizar: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    cur.close()
            else:
                print("\n⚠️  Nenhum pedido com situação 'Venda Atendimento Humano' encontrado")
                
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ Processo concluído!")
    print("=" * 80)
