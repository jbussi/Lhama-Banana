#!/usr/bin/env python3
"""
Busca as situações restantes: Logística e Venda Atendimento Humano
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
    print("🔍 Buscando situações restantes: Logística e Venda Atendimento Humano")
    print("=" * 80)
    
    # IDs para tentar (alguns podem ter restrições de permissão)
    ids_para_tentar = list(range(25, 100))  # IDs de 25 a 99
    
    situacoes_encontradas = {}
    
    print(f"\n📡 Buscando em {len(ids_para_tentar)} IDs...\n")
    
    for situacao_id in ids_para_tentar:
        try:
            time.sleep(0.5)  # Delay menor para ser mais rápido
            
            situacao = get_bling_situacao_by_id(situacao_id)
            
            if situacao:
                nome = situacao.get('nome', '').strip()
                cor = situacao.get('cor', '')
                
                # Verificar se é uma das que procuramos
                nome_lower = nome.lower()
                if 'logística' in nome_lower or 'logistica' in nome_lower or 'atendimento humano' in nome_lower:
                    situacoes_encontradas[situacao_id] = {
                        'id': situacao_id,
                        'nome': nome,
                        'cor': cor
                    }
                    print(f"   ✅ ID {situacao_id}: {nome}")
                else:
                    # Mostrar todas encontradas para debug
                    print(f"   ℹ️  ID {situacao_id}: {nome}")
                    
        except Exception as e:
            # Ignorar erros 404 e 403
            if '404' not in str(e) and '403' not in str(e) and 'not found' not in str(e).lower() and 'forbidden' not in str(e).lower():
                print(f"   ⚠️  ID {situacao_id}: Erro - {e}")
            continue
    
    print(f"\n✅ Total encontrado: {len(situacoes_encontradas)} situações relevantes")
    
    # Atualizar no banco se encontrou
    if situacoes_encontradas:
        print("\n🔄 Atualizando IDs no banco...\n")
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Função para normalizar nomes
            def normalizar_nome(nome):
                import unicodedata
                nome = unicodedata.normalize('NFD', nome)
                nome = ''.join(c for c in nome if unicodedata.category(c) != 'Mn')
                return nome.lower().strip()
            
            for situacao_id, dados in situacoes_encontradas.items():
                nome_bling = dados['nome']
                cor_real = dados.get('cor', '')
                nome_normalizado = normalizar_nome(nome_bling)
                
                # Buscar no banco
                cur.execute("""
                    SELECT id, nome, bling_situacao_id
                    FROM bling_situacoes
                    WHERE LOWER(REPLACE(REPLACE(nome, 'í', 'i'), 'á', 'a')) LIKE %s
                """, (f'%{nome_normalizado}%',))
                
                situacao_banco = cur.fetchone()
                
                if situacao_banco:
                    cur.execute("""
                        UPDATE bling_situacoes
                        SET bling_situacao_id = %s,
                            cor = COALESCE(NULLIF(%s, ''), cor),
                            atualizado_em = NOW()
                        WHERE id = %s
                    """, (situacao_id, cor_real, situacao_banco['id']))
                    
                    print(f"✅ {situacao_banco['nome']}: ID {situacao_banco['bling_situacao_id']} → {situacao_id}")
            
            conn.commit()
            
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
