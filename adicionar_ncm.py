"""
Script para adicionar coluna NCM e atualizar produtos
"""
import os
import sys
import psycopg2
import psycopg2.extras

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'sistema_usuarios')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'far111111')

def get_db_connection():
    dsn = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
    return psycopg2.connect(dsn, client_encoding='UTF8')

conn = get_db_connection()
cur = conn.cursor()

try:
    print("Verificando se coluna NCM existe...")
    
    # Verificar se coluna existe
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'produtos' AND column_name = 'ncm'
    """)
    
    if cur.fetchone():
        print("[OK] Coluna NCM ja existe")
    else:
        print("Adicionando coluna NCM...")
        cur.execute("""
            ALTER TABLE produtos 
            ADD COLUMN ncm VARCHAR(8)
        """)
        conn.commit()
        print("[OK] Coluna NCM adicionada com sucesso!")
    
    # Atualizar produtos de teste
    print("\nAtualizando produtos de teste com NCM...")
    
    cur.execute("""
        UPDATE produtos 
        SET ncm = '61091000'
        WHERE codigo_sku LIKE 'CAM-%' 
        AND (ncm IS NULL OR ncm = '')
    """)
    print(f"  [OK] {cur.rowcount} camisetas atualizadas com NCM 61091000")
    
    cur.execute("""
        UPDATE produtos 
        SET ncm = '61092000'
        WHERE codigo_sku LIKE 'REG-%' 
        AND (ncm IS NULL OR ncm = '')
    """)
    print(f"  [OK] {cur.rowcount} regatas atualizadas com NCM 61092000")
    
    conn.commit()
    
    # Verificar produtos atualizados
    print("\nVerificando produtos atualizados...")
    cur.execute("""
        SELECT id, codigo_sku, ncm 
        FROM produtos 
        WHERE id IN (10, 11, 12, 13, 14, 15)
        ORDER BY id
    """)
    
    produtos = cur.fetchall()
    for produto in produtos:
        print(f"  Produto {produto[0]} (SKU: {produto[1]}): NCM = {produto[2] or 'AUSENTE'}")
    
    print("\n[OK] Processo concluido!")
    
except Exception as e:
    conn.rollback()
    print(f"[ERRO] Erro: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
