#!/usr/bin/env python3
"""
Script para adicionar campo nome_normalizado na tabela transportadoras_bling
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from blueprints.services.db import get_db
import psycopg2

def add_nome_normalizado():
    """Adiciona campo nome_normalizado e índices"""
    app = create_app()
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # 1. Adicionar colunas
            print("1. Adicionando colunas nome_normalizado e fantasia_normalizado...")
            cur.execute("""
                ALTER TABLE transportadoras_bling
                ADD COLUMN IF NOT EXISTS nome_normalizado VARCHAR(255);
            """)
            cur.execute("""
                ALTER TABLE transportadoras_bling
                ADD COLUMN IF NOT EXISTS fantasia_normalizado VARCHAR(255);
            """)
            conn.commit()
            print("   ✅ Colunas adicionadas")
            
            # 2. Criar função de normalização
            print("2. Criando função de normalização...")
            cur.execute("""
                CREATE OR REPLACE FUNCTION normalizar_nome_transportadora(nome_texto TEXT)
                RETURNS TEXT AS $$
                BEGIN
                    IF nome_texto IS NULL THEN
                        RETURN NULL;
                    END IF;
                    
                    nome_texto := UPPER(nome_texto);
                    
                    nome_texto := translate(
                        nome_texto,
                        'ÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ',
                        'AAAAEEEIIIOOOOUUUC'
                    );
                    
                    nome_texto := trim(regexp_replace(nome_texto, '\s+', ' ', 'g'));
                    nome_texto := regexp_replace(nome_texto, '[^A-Z0-9 ]', '', 'g');
                    
                    RETURN nome_texto;
                END;
                $$ LANGUAGE plpgsql IMMUTABLE;
            """)
            conn.commit()
            print("   ✅ Função criada")
            
            # 3. Atualizar registros existentes
            print("3. Atualizando registros existentes...")
            cur.execute("""
                UPDATE transportadoras_bling
                SET 
                    nome_normalizado = normalizar_nome_transportadora(nome),
                    fantasia_normalizado = normalizar_nome_transportadora(fantasia)
                WHERE nome_normalizado IS NULL OR fantasia_normalizado IS NULL;
            """)
            conn.commit()
            print(f"   ✅ {cur.rowcount} registros atualizados")
            
            # 4. Criar índices
            print("4. Criando índices...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_nome_normalizado 
                ON transportadoras_bling(nome_normalizado) 
                WHERE situacao = 'A' AND nome_normalizado IS NOT NULL;
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_transportadoras_bling_fantasia_normalizado 
                ON transportadoras_bling(fantasia_normalizado) 
                WHERE situacao = 'A' AND fantasia_normalizado IS NOT NULL;
            """)
            conn.commit()
            print("   ✅ Índices criados")
            
            # 5. Criar trigger
            print("5. Criando trigger...")
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_transportadora_nome_normalizado()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.nome_normalizado := normalizar_nome_transportadora(NEW.nome);
                    NEW.fantasia_normalizado := normalizar_nome_transportadora(NEW.fantasia);
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            cur.execute("""
                DROP TRIGGER IF EXISTS trigger_update_transportadora_nome_normalizado ON transportadoras_bling;
            """)
            cur.execute("""
                CREATE TRIGGER trigger_update_transportadora_nome_normalizado
                BEFORE INSERT OR UPDATE OF nome, fantasia ON transportadoras_bling
                FOR EACH ROW
                EXECUTE FUNCTION update_transportadora_nome_normalizado();
            """)
            conn.commit()
            print("   ✅ Trigger criado")
            
            # 6. Verificar resultado
            cur.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(nome_normalizado) as com_nome_norm,
                       COUNT(fantasia_normalizado) as com_fantasia_norm
                FROM transportadoras_bling;
            """)
            result = cur.fetchone()
            print(f"\n📊 Resultado:")
            print(f"   Total de transportadoras: {result[0]}")
            print(f"   Com nome_normalizado: {result[1]}")
            print(f"   Com fantasia_normalizado: {result[2]}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            conn.rollback()
            import traceback
            traceback.print_exc()
        finally:
            cur.close()

if __name__ == '__main__':
    print("🔄 Adicionando campo nome_normalizado e índices...\n")
    add_nome_normalizado()
    print("\n✅ Concluído!")
