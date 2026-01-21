#!/usr/bin/env python3
"""
Script para atualizar IDs reais das situações do Bling manualmente
Use quando descobrir os IDs reais via painel do Bling ou quando o rate limiting passar
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
import psycopg2.extras

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar pool de conexões
init_db_pool(app.config['DATABASE_CONFIG'])

# Mapeamento manual de nomes para IDs reais
# Preencha com os IDs que você descobrir no painel do Bling
MAPEAMENTO_IDS = {
    "Em aberto": None,  # Preencher com ID real
    "Atendido": None,
    "Cancelado": None,
    "Em andamento": None,
    "Venda Agenciada": None,
    "Em digitação": None,
    "Verificado": None,
    "Venda Atendimento Humano": None,
    "Logística": None,
}

def atualizar_id_por_nome(nome: str, id_real: int, cor: str = None):
    """Atualiza o ID de uma situação pelo nome"""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE bling_situacoes
            SET bling_situacao_id = %s,
                cor = COALESCE(%s, cor),
                atualizado_em = NOW()
            WHERE nome = %s
        """, (id_real, cor, nome))
        
        conn.commit()
        
        if cur.rowcount > 0:
            print(f"✅ {nome}: ID atualizado para {id_real}")
            return True
        else:
            print(f"⚠️  {nome}: Não encontrado no banco")
            return False
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao atualizar {nome}: {e}")
        return False
    finally:
        cur.close()

with app.app_context():
    print("=" * 80)
    print("🔄 Atualizar IDs Reais das Situações do Bling")
    print("=" * 80)
    
    # Mostrar situação atual
    print("\n📋 Situações atuais no banco:")
    print("-" * 80)
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT id, bling_situacao_id, nome, cor
            FROM bling_situacoes
            ORDER BY nome
        """)
        
        situacoes = cur.fetchall()
        
        print(f"{'Nome':<35} {'ID Atual':<15} {'Status'}")
        print("-" * 80)
        
        for situacao in situacoes:
            id_atual = situacao['bling_situacao_id']
            nome = situacao['nome']
            status = "Temporário" if (id_atual > 100000 or id_atual < 0) else "Real"
            print(f"{nome:<35} {id_atual:<15} {status}")
        
        print("-" * 80)
        
        # Verificar se há IDs para atualizar
        ids_para_atualizar = {k: v for k, v in MAPEAMENTO_IDS.items() if v is not None}
        
        if ids_para_atualizar:
            print(f"\n🔄 Atualizando {len(ids_para_atualizar)} IDs...")
            for nome, id_real in ids_para_atualizar.items():
                atualizar_id_por_nome(nome, id_real)
        else:
            print("\n💡 Para atualizar IDs:")
            print("   1. Edite este script e preencha o dicionário MAPEAMENTO_IDS")
            print("   2. Ou use a função atualizar_id_por_nome() diretamente")
            print("\n   Exemplo:")
            print("   atualizar_id_por_nome('Em andamento', 15, '#FF0000')")
        
        # Mostrar situação final
        print("\n📋 Situações após atualização:")
        print("-" * 80)
        
        cur.execute("""
            SELECT id, bling_situacao_id, nome, cor
            FROM bling_situacoes
            ORDER BY nome
        """)
        
        situacoes_finais = cur.fetchall()
        
        print(f"{'Nome':<35} {'ID':<15} {'Status'}")
        print("-" * 80)
        
        for situacao in situacoes_finais:
            id_atual = situacao['bling_situacao_id']
            nome = situacao['nome']
            status = "Temporário" if (id_atual > 100000 or id_atual < 0) else "Real"
            print(f"{nome:<35} {id_atual:<15} {status}")
        
        print("-" * 80)
        
    finally:
        cur.close()
    
    print("\n✅ Processo concluído!")
    print("\n💡 Como descobrir os IDs reais:")
    print("   1. Acesse o painel do Bling")
    print("   2. Vá em Configurações > Situações de Vendas")
    print("   3. Anote o ID de cada situação")
    print("   4. Edite este script e preencha MAPEAMENTO_IDS")
    print("   5. Execute novamente: python atualizar_ids_manuais.py")
