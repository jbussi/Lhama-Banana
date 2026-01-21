#!/usr/bin/env python3
"""
Script para sincronizar situações do Bling SEM tentar renovar token
Útil quando há rate limiting ou token já foi renovado manualmente
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.bling_situacao_service import sync_bling_situacoes_to_db, get_all_bling_situacoes
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_api_service import get_valid_access_token
import psycopg2.extras

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar pool de conexões
init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🔄 Sincronizando Situações do Bling (SEM renovar token)")
    print("=" * 80)
    
    # Passo 1: Verificar se token está válido
    print("\n📝 PASSO 1: Verificando token...")
    try:
        token = get_valid_access_token()
        print("✅ Token válido encontrado")
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
        print("\n💡 SOLUÇÃO:")
        print("   1. Aguarde 10-15 minutos para o rate limiting passar")
        print("   2. OU renove o token manualmente via navegador:")
        print("      https://www.bling.com.br/Api/v3/oauth/authorize?response_type=code&client_id=b2bc093daf984f6263de746701dde7b1b7d23cea&redirect_uri=https://efractory-burdenless-kathlene.ngrok-free.dev/api/bling/callback&scope=produtos%20pedidos%20nfe%20estoques%20contatos%20financeiro")
        print("   3. Depois execute este script novamente")
        sys.exit(1)
    
    # Passo 2: Buscar situações do Bling
    print("\n📝 PASSO 2: Buscando situações do Bling via API...")
    print("   ⚠️  Isso pode levar alguns minutos (tentando IDs de 1 a 50)...")
    
    situacoes_bling = get_all_bling_situacoes()
    
    if not situacoes_bling:
        print("⚠️  Nenhuma situação encontrada via busca automática.")
        print("   Isso pode ser normal se a API não permitir listagem.")
        print("   Vamos tentar sincronizar mesmo assim...")
    else:
        print(f"✅ Encontradas {len(situacoes_bling)} situações no Bling")
        for sit in situacoes_bling[:10]:  # Mostrar primeiras 10
            print(f"   - ID {sit.get('id')}: {sit.get('nome')}")
        if len(situacoes_bling) > 10:
            print(f"   ... e mais {len(situacoes_bling) - 10}")
    
    # Passo 3: Sincronizar para o banco
    print("\n📝 PASSO 3: Sincronizando situações para o banco de dados...")
    result = sync_bling_situacoes_to_db()
    
    if result.get('success'):
        print(f"✅ Sincronização concluída!")
        print(f"   Total: {result.get('total')}")
        print(f"   Sincronizadas: {result.get('sincronizadas')}")
        print(f"   Atualizadas: {result.get('atualizadas')}")
    else:
        print(f"⚠️  Sincronização parcial ou com erros:")
        print(f"   {result.get('error', 'Erro desconhecido')}")
    
    # Passo 4: Listar situações no banco
    print("\n📝 PASSO 4: Situações no banco de dados:")
    print("-" * 80)
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT bling_situacao_id, nome, cor, status_site, ativo
            FROM bling_situacoes
            ORDER BY bling_situacao_id
        """)
        
        situacoes = cur.fetchall()
        
        print(f"{'ID':<10} {'Nome':<35} {'Status Site':<25} {'Cor'}")
        print("-" * 80)
        
        for situacao in situacoes:
            id_str = str(situacao['bling_situacao_id'])
            nome = situacao['nome'][:35]
            status = situacao['status_site'] or "(sem mapeamento)"
            cor = situacao['cor'] or "-"
            
            # Marcar IDs temporários
            if situacao['bling_situacao_id'] > 100000 or situacao['bling_situacao_id'] < 0:
                id_str = f"{id_str} (temp)"
            
            print(f"{id_str:<10} {nome:<35} {status:<25} {cor}")
        
        print("-" * 80)
        
        # Verificar IDs temporários
        cur.execute("""
            SELECT COUNT(*) as total
            FROM bling_situacoes
            WHERE bling_situacao_id > 100000 OR bling_situacao_id < 0
        """)
        
        temp_count = cur.fetchone()['total']
        
        if temp_count > 0:
            print(f"\n⚠️  Ainda existem {temp_count} situações com IDs temporários.")
            print("   Execute: python update_situacoes_ids.py para tentar atualizar")
        else:
            print("\n✅ Todas as situações têm IDs reais do Bling!")
        
    finally:
        cur.close()
    
    print("\n" + "=" * 80)
    print("✅ Processo concluído!")
    print("=" * 80)
    print("\n💡 Próximos passos:")
    print("   1. Se ainda houver IDs temporários, execute:")
    print("      python update_situacoes_ids.py")
    print("   2. Mapear situações para status do site usando:")
    print("      POST /api/bling/situacoes/<id>/map")
    print("      Body: {\"status_site\": \"em_processamento\"}")
    print("   3. Testar webhook quando pedido mudar de situação no Bling")
