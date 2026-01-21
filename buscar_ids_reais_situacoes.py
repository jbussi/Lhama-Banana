#!/usr/bin/env python3
"""
Script para buscar IDs reais das situações do Bling e atualizar no banco
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_situacao_service import get_bling_situacao_by_id, get_all_bling_situacoes
from blueprints.services.bling_api_service import get_valid_access_token
import psycopg2.extras
import time

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar pool de conexões
init_db_pool(app.config['DATABASE_CONFIG'])

def buscar_e_atualizar_ids():
    """Busca IDs reais das situações e atualiza no banco"""
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
        
        print(f"\n📋 Encontradas {len(situacoes_banco)} situações no banco")
        print("🔍 Buscando IDs reais no Bling...\n")
        
        atualizadas = 0
        nao_encontradas = []
        
        # Tentar buscar IDs de 1 a 100 (faixa comum)
        ids_tentados = list(range(1, 101))
        situacoes_encontradas_bling = {}
        
        print("📡 Buscando situações no Bling (isso pode levar alguns minutos)...")
        print("   Aguardando 2 segundos entre requisições para evitar rate limiting...\n")
        
        # Buscar situações do Bling
        for idx, situacao_id in enumerate(ids_tentados):
            if idx > 0 and idx % 10 == 0:
                print(f"   Tentando ID {situacao_id}...")
            
            try:
                # Delay para evitar rate limiting
                if idx > 0:
                    time.sleep(2)
                
                situacao_bling = get_bling_situacao_by_id(situacao_id)
                
                if situacao_bling:
                    nome_bling = situacao_bling.get('nome', '').strip()
                    id_real = situacao_bling.get('id')
                    cor = situacao_bling.get('cor', '')
                    
                    if nome_bling:
                        situacoes_encontradas_bling[nome_bling.lower()] = {
                            'id': id_real,
                            'nome': nome_bling,
                            'cor': cor
                        }
                        print(f"   ✅ Encontrada: ID {id_real} - {nome_bling}")
                        
            except Exception as e:
                # ID não existe ou erro, continuar
                if '429' in str(e) or 'rate limit' in str(e).lower():
                    print(f"   ⚠️  Rate limiting detectado no ID {situacao_id}, aguardando 10 segundos...")
                    time.sleep(10)
                continue
        
        print(f"\n✅ Total de {len(situacoes_encontradas_bling)} situações encontradas no Bling")
        
        # Agora comparar e atualizar
        print("\n🔄 Atualizando IDs no banco...\n")
        
        for situacao_banco in situacoes_banco:
            nome_banco = situacao_banco['nome'].strip()
            id_temp = situacao_banco['bling_situacao_id']
            nome_lower = nome_banco.lower()
            
            # Buscar correspondência no Bling
            situacao_bling = situacoes_encontradas_bling.get(nome_lower)
            
            if situacao_bling:
                id_real = situacao_bling['id']
                cor_real = situacao_bling.get('cor', '')
                
                # Atualizar no banco
                cur.execute("""
                    UPDATE bling_situacoes
                    SET bling_situacao_id = %s,
                        cor = COALESCE(NULLIF(%s, ''), cor),
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (id_real, cor_real, situacao_banco['id']))
                
                atualizadas += 1
                print(f"✅ {nome_banco}: ID temporário {id_temp} → ID real {id_real}")
            else:
                nao_encontradas.append(nome_banco)
                print(f"⚠️  {nome_banco}: Não encontrado no Bling (mantendo ID temporário {id_temp})")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ Atualização concluída!")
        print(f"   Atualizadas: {atualizadas}")
        print(f"   Não encontradas: {len(nao_encontradas)}")
        if nao_encontradas:
            print(f"   Situações não encontradas: {', '.join(nao_encontradas)}")
        print("=" * 80)
        
        return {
            'atualizadas': atualizadas,
            'nao_encontradas': nao_encontradas
        }
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cur.close()


with app.app_context():
    print("=" * 80)
    print("🔄 Buscando IDs Reais das Situações do Bling")
    print("=" * 80)
    
    # Verificar token
    print("\n📝 Verificando autenticação...")
    try:
        token = get_valid_access_token()
        print("✅ Token válido encontrado")
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
        print("\n💡 SOLUÇÃO:")
        print("   1. Renove o token via navegador:")
        print("      https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=b2bc093daf984f6263de746701dde7b1b7d23cea&redirect_uri=https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/callback&scope=produtos%20pedidos%20nfe%20estoques%20contatos%20financeiro")
        sys.exit(1)
    
    # Buscar e atualizar IDs
    resultado = buscar_e_atualizar_ids()
    
    # Mostrar situação final
    print("\n📋 Situações após atualização:")
    print("-" * 80)
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT bling_situacao_id, nome, cor, status_site
            FROM bling_situacoes
            ORDER BY nome
        """)
        
        situacoes_finais = cur.fetchall()
        
        print(f"{'ID':<10} {'Nome':<35} {'Status Site':<25} {'Cor'}")
        print("-" * 80)
        
        for situacao in situacoes_finais:
            id_atual = situacao['bling_situacao_id']
            nome = situacao['nome'][:35]
            status = situacao['status_site'] or "(sem mapeamento)"
            cor = situacao['cor'] or "-"
            
            # Marcar IDs temporários
            if id_atual > 100000 or id_atual < 0:
                id_str = f"{id_atual} (temp)"
            else:
                id_str = str(id_atual)
            
            print(f"{id_str:<10} {nome:<35} {status:<25} {cor}")
        
        print("-" * 80)
        
        # Contar temporários restantes
        cur.execute("""
            SELECT COUNT(*) as total
            FROM bling_situacoes
            WHERE bling_situacao_id > 100000 OR bling_situacao_id < 0
        """)
        
        temp_count = cur.fetchone()['total']
        
        if temp_count > 0:
            print(f"\n⚠️  Ainda existem {temp_count} situações com IDs temporários.")
        else:
            print("\n✅ Todas as situações têm IDs reais do Bling!")
        
    finally:
        cur.close()
    
    print("\n✅ Processo concluído!")
