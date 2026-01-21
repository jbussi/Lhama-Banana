#!/usr/bin/env python3
"""
Script para inserir situações do Bling manualmente no banco
Execute: python insert_situacoes_manual.py
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

# Situações conhecidas (sem IDs ainda - serão atualizados depois)
situacoes_conhecidas = [
    {"nome": "Em aberto", "cor": "#E9DC40"},
    {"nome": "Atendido", "cor": None},
    {"nome": "Cancelado", "cor": None},
    {"nome": "Em andamento", "cor": None},
    {"nome": "Venda Agenciada", "cor": None},
    {"nome": "Em digitação", "cor": None},
    {"nome": "Verificado", "cor": None},
    {"nome": "Venda Atendimento Humano", "cor": None},
    {"nome": "Logística", "cor": None},
]

with app.app_context():
    print("=" * 80)
    print("📝 Inserindo Situações do Bling Manualmente")
    print("=" * 80)
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        inseridas = 0
        atualizadas = 0
        
        for situacao in situacoes_conhecidas:
            nome = situacao['nome']
            cor = situacao.get('cor', '')
            
            # Verificar se já existe pelo nome
            cur.execute("""
                SELECT id, bling_situacao_id, nome
                FROM bling_situacoes
                WHERE nome = %s
            """, (nome,))
            
            existente = cur.fetchone()
            
            if existente:
                print(f"✅ Situação já existe: {nome} (ID Bling: {existente['bling_situacao_id']})")
                atualizadas += 1
            else:
                # Inserir com ID temporário único baseado no hash do nome
                # Isso permite inserir sem conhecer o ID real do Bling ainda
                import hashlib
                temp_id = abs(int(hashlib.md5(nome.encode()).hexdigest()[:8], 16)) % 1000000
                
                # Tentar inserir, se já existir esse ID temporário, usar próximo disponível
                max_tentativas = 10
                inserido = False
                
                for tentativa in range(max_tentativas):
                    try:
                        cur.execute("""
                            INSERT INTO bling_situacoes 
                            (bling_situacao_id, nome, cor, id_herdado, ativo, status_site)
                            VALUES (%s, %s, %s, 0, TRUE, NULL)
                        """, (temp_id + tentativa, nome, cor))
                        
                        inseridas += 1
                        print(f"✅ Situação inserida: {nome} (ID temporário: {temp_id + tentativa})")
                        inserido = True
                        break
                    except psycopg2.IntegrityError:
                        # ID já existe, tentar próximo
                        continue
                
                if not inserido:
                    print(f"⚠️  Não foi possível inserir: {nome} (muitos conflitos de ID)")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ Concluído!")
        print(f"   Inseridas: {inseridas}")
        print(f"   Já existiam: {atualizadas}")
        print("=" * 80)
        
        print("\n💡 Próximos passos:")
        print("   1. Renovar token do Bling: GET /api/bling/authorize")
        print("   2. Buscar IDs reais das situações via API do Bling")
        print("   3. Atualizar bling_situacao_id na tabela bling_situacoes")
        print("   4. Mapear cada situação para status do site")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
