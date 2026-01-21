#!/usr/bin/env python3
"""
Busca todas as situações do Bling tentando IDs sequenciais
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_situacao_service import get_bling_situacao_by_id
import psycopg2.extras

app = Flask(__name__)
app.config.from_object('config.Config')

init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🔍 Buscando todas as situações do Bling")
    print("=" * 80)
    
    situacoes_encontradas = {}
    
    # Tentar IDs de 1 a 50
    print("\n📡 Buscando situações (IDs 1-50)...")
    print("   Aguardando 1 segundo entre requisições para evitar rate limiting...\n")
    
    for situacao_id in range(1, 51):
        try:
            time.sleep(1)  # Delay para evitar rate limiting
            
            situacao = get_bling_situacao_by_id(situacao_id)
            
            if situacao:
                nome = situacao.get('nome', '').strip()
                cor = situacao.get('cor', '')
                situacoes_encontradas[situacao_id] = {
                    'id': situacao_id,
                    'nome': nome,
                    'cor': cor
                }
                print(f"   ✅ ID {situacao_id:2d}: {nome}")
        except Exception as e:
            # Erro esperado para IDs que não existem
            if '404' not in str(e) and 'not found' not in str(e).lower():
                print(f"   ⚠️  ID {situacao_id:2d}: Erro - {e}")
            continue
    
    print(f"\n✅ Total encontrado: {len(situacoes_encontradas)} situações")
    
    # Agora atualizar no banco
    if situacoes_encontradas:
        print("\n🔄 Atualizando IDs no banco...\n")
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Buscar todas as situações no banco
            cur.execute("""
                SELECT id, bling_situacao_id, nome
                FROM bling_situacoes
                ORDER BY nome
            """)
            
            situacoes_banco = cur.fetchall()
            
            atualizadas = 0
            
            # Função para normalizar nomes
            def normalizar_nome(nome):
                import unicodedata
                nome = unicodedata.normalize('NFD', nome)
                nome = ''.join(c for c in nome if unicodedata.category(c) != 'Mn')
                return nome.lower().strip()
            
            # Criar dicionário de situações encontradas por nome normalizado
            situacoes_por_nome = {}
            for dados in situacoes_encontradas.values():
                nome_normalizado = normalizar_nome(dados['nome'])
                situacoes_por_nome[nome_normalizado] = dados
            
            for situacao_banco in situacoes_banco:
                nome_banco = situacao_banco['nome'].strip()
                id_temp = situacao_banco['bling_situacao_id']
                nome_normalizado = normalizar_nome(nome_banco)
                
                situacao_bling = situacoes_por_nome.get(nome_normalizado)
                
                if situacao_bling:
                    id_real = situacao_bling['id']
                    cor_real = situacao_bling.get('cor', '')
                    
                    cur.execute("""
                        UPDATE bling_situacoes
                        SET bling_situacao_id = %s,
                            cor = COALESCE(NULLIF(%s, ''), cor),
                            atualizado_em = NOW()
                        WHERE id = %s
                    """, (id_real, cor_real, situacao_banco['id']))
                    
                    atualizadas += 1
                    print(f"✅ {nome_banco}: ID {id_temp} → {id_real}")
                else:
                    print(f"⚠️  {nome_banco}: Não encontrado (mantendo ID temporário {id_temp})")
            
            conn.commit()
            
            print(f"\n✅ {atualizadas} situações atualizadas!")
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ Erro ao atualizar: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cur.close()
    
    print("\n" + "=" * 80)
    print("✅ Processo concluído!")
    print("=" * 80)
