#!/usr/bin/env python3
"""
Script para atualizar IDs reais das situações do Bling
Execute após renovar o token: python update_situacoes_ids.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, current_app
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_situacao_service import get_bling_situacao_by_id
import psycopg2.extras

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar pool de conexões
init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🔄 Atualizando IDs Reais das Situações do Bling")
    print("=" * 80)
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar todas as situações sem ID real (IDs temporários são > 100000)
        cur.execute("""
            SELECT id, bling_situacao_id, nome
            FROM bling_situacoes
            WHERE bling_situacao_id > 100000 OR bling_situacao_id < 0
            ORDER BY nome
        """)
        
        situacoes_temp = cur.fetchall()
        
        if not situacoes_temp:
            print("✅ Todas as situações já têm IDs reais do Bling")
            sys.exit(0)
        
        print(f"\n📋 Encontradas {len(situacoes_temp)} situações com IDs temporários")
        print("🔍 Tentando descobrir IDs reais...\n")
        
        atualizadas = 0
        nao_encontradas = []
        
        # Tentar buscar IDs de 1 a 100 (faixa comum de situações)
        ids_tentados = list(range(1, 101))
        
        for situacao_temp in situacoes_temp:
            nome_buscado = situacao_temp['nome']
            id_temp = situacao_temp['bling_situacao_id']
            
            encontrado = False
            
            for situacao_id in ids_tentados:
                try:
                    situacao_bling = get_bling_situacao_by_id(situacao_id)
                    
                    if situacao_bling and situacao_bling.get('nome') == nome_buscado:
                        # Encontrou! Atualizar ID
                        id_real = situacao_bling['id']
                        cor_real = situacao_bling.get('cor', '')
                        
                        cur.execute("""
                            UPDATE bling_situacoes
                            SET bling_situacao_id = %s,
                                cor = %s,
                                atualizado_em = NOW()
                            WHERE id = %s
                        """, (id_real, cor_real, situacao_temp['id']))
                        
                        atualizadas += 1
                        encontrado = True
                        print(f"✅ {nome_buscado}: ID temporário {id_temp} → ID real {id_real}")
                        break
                        
                except Exception as e:
                    # ID não existe ou erro, continuar
                    continue
            
            if not encontrado:
                nao_encontradas.append(nome_buscado)
                print(f"⚠️  {nome_buscado}: Não encontrado (mantendo ID temporário {id_temp})")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ Atualização concluída!")
        print(f"   Atualizadas: {atualizadas}")
        print(f"   Não encontradas: {len(nao_encontradas)}")
        if nao_encontradas:
            print(f"   Situações não encontradas: {', '.join(nao_encontradas)}")
        print("=" * 80)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
