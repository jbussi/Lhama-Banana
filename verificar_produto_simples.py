"""Verificar se produto existe no banco"""
import os
import sys
import psycopg2

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'sistema_usuarios')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'far111111')

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cur = conn.cursor()

try:
    # Verificar se produto existe
    cur.execute("SELECT id, codigo_sku, ncm FROM produtos WHERE id = 10")
    row = cur.fetchone()
    
    if row:
        print(f"Produto encontrado: ID={row[0]}, SKU={row[1]}, NCM={row[2]}")
    else:
        print("Produto 10 NAO encontrado!")
        # Listar produtos existentes
        cur.execute("SELECT id, codigo_sku FROM produtos ORDER BY id LIMIT 10")
        produtos = cur.fetchall()
        print(f"\nProdutos existentes (primeiros 10):")
        for p in produtos:
            print(f"  ID: {p[0]}, SKU: {p[1]}")
    
    # Verificar se nome_produto existe para produto 10
    cur.execute("""
        SELECT p.id, p.nome_produto_id, np.nome 
        FROM produtos p
        LEFT JOIN nome_produto np ON p.nome_produto_id = np.id
        WHERE p.id = 10
    """)
    row = cur.fetchone()
    if row:
        print(f"\nProduto com nome_produto: ID={row[0]}, nome_produto_id={row[1]}, nome={row[2]}")
    else:
        print("\nProduto 10 nao encontrado na query com JOIN")
        
except Exception as e:
    print(f"Erro: {e}")
finally:
    cur.close()
    conn.close()
