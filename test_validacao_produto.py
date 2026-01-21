"""
Teste de validação de produto antes de sincronizar
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

# Simular a query que get_product_for_bling_sync faz
conn = get_db_connection()
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

try:
    produto_id = 10
    print(f"Verificando dados do produto {produto_id}...")
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
            np.nome,
            np.descricao,
            np.descricao_curta,
            np.peso_kg,
            np.dimensoes_largura,
            np.dimensoes_altura,
            np.dimensoes_comprimento,
            c.nome as categoria_nome,
            e.nome as estampa_nome,
            t.nome as tamanho_nome
        FROM produtos p
        JOIN nome_produto np ON p.nome_produto_id = np.id
        JOIN categorias c ON np.categoria_id = c.id
        JOIN estampa e ON p.estampa_id = e.id
        JOIN tamanho t ON p.tamanho_id = t.id
        WHERE p.id = %s
    """, (produto_id,))
    
    produto = cur.fetchone()
    
    if not produto:
        print(f"[ERRO] Produto {produto_id} nao encontrado")
        sys.exit(1)
    
    print("Dados do produto:")
    print(f"  ID: {produto['id']}")
    print(f"  SKU: {produto['codigo_sku']}")
    print(f"  NCM: {produto['ncm']}")
    print(f"  Preco Venda: {produto['preco_venda']}")
    print(f"  Nome: {produto['nome']}")
    print()
    
    # Simular validação
    errors = []
    
    ncm = produto['ncm']
    if not ncm or len(str(ncm)) != 8:
        errors.append("NCM obrigatorio e deve ter 8 digitos")
    elif not str(ncm).isdigit():
        errors.append("NCM deve conter apenas digitos")
    
    if not produto['codigo_sku']:
        errors.append("SKU obrigatorio")
    
    preco = produto['preco_venda']
    if not preco or float(preco) <= 0:
        errors.append("Preco de venda deve ser maior que zero")
    
    if not produto['nome']:
        errors.append("Nome do produto obrigatorio")
    
    if errors:
        print("[ERRO] Validacao falhou:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("[OK] Produto valido para sincronizacao!")
    
except Exception as e:
    print(f"[ERRO] {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
