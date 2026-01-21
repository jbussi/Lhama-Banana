#!/usr/bin/env python3
"""
Script para sincronizar situações do Bling diretamente
Execute: python test_sync_situacoes.py
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.bling_situacao_service import sync_bling_situacoes_to_db, get_all_bling_situacoes
from blueprints.services.db import get_db, init_db_pool
import psycopg2.extras

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar pool de conexões
init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("=" * 80)
    print("🧪 Sincronizando Situações do Bling")
    print("=" * 80)
    
    # 1. Buscar situações do Bling
    print("\n📤 Buscando situações do Bling via API...")
    situacoes_bling = get_all_bling_situacoes()
    
    if not situacoes_bling:
        print("❌ Nenhuma situação encontrada no Bling")
        sys.exit(1)
    
    print(f"✅ Encontradas {len(situacoes_bling)} situações no Bling")
    
    # 2. Sincronizar para o banco
    print("\n💾 Sincronizando para o banco de dados...")
    result = sync_bling_situacoes_to_db()
    
    if result.get('success'):
        print(f"✅ Sincronização concluída!")
        print(f"   Total: {result.get('total')}")
        print(f"   Sincronizadas: {result.get('sincronizadas')}")
        print(f"   Atualizadas: {result.get('atualizadas')}")
    else:
        print(f"❌ Erro na sincronização: {result.get('error')}")
        sys.exit(1)
    
    # 3. Listar situações sincronizadas
    print("\n📋 Situações sincronizadas:")
    print("-" * 80)
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT bling_situacao_id, nome, cor, status_site, ativo
            FROM bling_situacoes
            ORDER BY nome
        """)
        
        situacoes = cur.fetchall()
        
        for situacao in situacoes:
            status = f"→ {situacao['status_site']}" if situacao['status_site'] else "(sem mapeamento)"
            print(f"ID: {situacao['bling_situacao_id']:3d} | Nome: {situacao['nome']:30s} | {status}")
            if situacao['cor']:
                print(f"      Cor: {situacao['cor']}")
        
        print("-" * 80)
        
        # Mostrar IDs importantes
        print("\n🎯 IDs importantes para mapeamento:")
        situacoes_importantes = [
            "Em aberto",
            "Em andamento",
            "Atendido",
            "Cancelado",
            "Venda Agenciada",
            "Em digitação",
            "Verificado",
            "Venda Atendimento Humano",
            "Logística"
        ]
        
        for nome in situacoes_importantes:
            sit = next((s for s in situacoes if s['nome'] == nome), None)
            if sit:
                print(f"   {nome:30s} : ID {sit['bling_situacao_id']}")
        
    finally:
        cur.close()
    
    print("\n✅ Teste concluído!")
    print("\n💡 Próximos passos:")
    print("   1. Mapear situações para status do site usando:")
    print("      POST /api/bling/situacoes/<id>/map")
    print("      Body: {\"status_site\": \"em_processamento\"}")
    print("   2. Testar webhook quando pedido mudar de situação no Bling")
