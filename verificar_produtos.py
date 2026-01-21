"""
Script para verificar dados dos produtos criados
"""
import os
import sys
import psycopg2
import psycopg2.extras

# Carregar variáveis de ambiente
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
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

try:
    print("=" * 70)
    print("VERIFICANDO DADOS DOS PRODUTOS")
    print("=" * 70)
    print()
    
    cur.execute("""
        SELECT 
            p.id,
            p.codigo_sku,
            p.ncm,
            p.preco_venda,
            p.preco_promocional,
            p.custo,
            p.estoque,
            p.ativo,
            np.nome as nome_produto,
            c.nome as categoria,
            e.nome as estampa,
            t.nome as tamanho
        FROM produtos p
        JOIN nome_produto np ON p.nome_produto_id = np.id
        JOIN categorias c ON np.categoria_id = c.id
        JOIN estampa e ON p.estampa_id = e.id
        JOIN tamanho t ON p.tamanho_id = t.id
        WHERE p.id IN (10, 11, 12, 13, 14, 15)
        ORDER BY p.id
    """)
    
    produtos = cur.fetchall()
    
    for produto in produtos:
        print(f"Produto ID: {produto['id']}")
        print(f"  SKU: {produto['codigo_sku']}")
        print(f"  Nome: {produto['nome_produto']} - {produto['tamanho']}")
        print(f"  Categoria: {produto['categoria']}")
        print(f"  Estampa: {produto['estampa']}")
        print(f"  NCM: {produto['ncm'] or 'AUSENTE - ERRO!'}")
        print(f"  Preco Venda: R$ {produto['preco_venda']}")
        print(f"  Preco Promocional: R$ {produto['preco_promocional'] or 'N/A'}")
        print(f"  Custo: R$ {produto['custo']}")
        print(f"  Estoque: {produto['estoque']}")
        print(f"  Ativo: {produto['ativo']}")
        print()
        
        # Verificar se tem NCM
        if not produto['ncm']:
            print(f"  [ERRO] Produto {produto['id']} nao tem NCM! NCM e obrigatorio para Bling.")
        print()
    
    print("=" * 70)
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
