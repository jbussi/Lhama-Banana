"""
Script para criar produtos de teste para integração Bling
=========================================================
Cria múltiplos produtos com variações (categoria, estampa, tamanho)
para testar a sincronização completa com o Bling.
"""
import os
import sys
from datetime import datetime
import psycopg2
import psycopg2.extras

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[AVISO] python-dotenv não instalado. Usando variáveis de ambiente do sistema.")

# Configuração do banco de dados (mesma do config.py)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'sistema_usuarios')
DB_USER = os.environ.get('DB_USER', 'postgres')
# Tentar obter senha do .env, se não encontrar, usar padrão
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
if not DB_PASSWORD:
    # Tentar ler do .env diretamente
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('DB_PASSWORD='):
                    DB_PASSWORD = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    # Se ainda não encontrou, usar senha padrão do config.py
    if not DB_PASSWORD:
        DB_PASSWORD = 'far111111'

def get_db_connection():
    """Conecta ao banco de dados"""
    dsn = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
    return psycopg2.connect(dsn, client_encoding='UTF8')


def criar_dados_base_se_nao_existirem(cur, conn):
    """Cria categorias, estampas e tamanhos básicos se não existirem"""
    
    # 1. Criar categorias
    categorias = [
        ('Camisetas', 'Camisetas com estampas exclusivas'),
        ('Regatas', 'Regatas confortáveis'),
        ('Moletom', 'Moletons quentinhos')
    ]
    
    # Verificar colunas disponíveis na tabela categorias
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='categorias'
    """)
    colunas_categoria = [row[0] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
    
    categoria_ids = {}
    for nome, descricao in categorias:
        cur.execute("SELECT id FROM categorias WHERE nome = %s LIMIT 1", (nome,))
        row = cur.fetchone()
        if row:
            categoria_ids[nome] = row['id'] if isinstance(row, dict) else row[0]
        else:
            # Montar INSERT dinâmico baseado nas colunas existentes
            campos = ['nome']
            valores = [nome]
            
            if 'ativo' in colunas_categoria:
                campos.append('ativo')
                valores.append(True)
            
            if 'ordem_exibicao' in colunas_categoria:
                campos.append('ordem_exibicao')
                valores.append(len(categoria_ids))
            
            campos_sql = ', '.join(campos)
            placeholders = ', '.join(['%s'] * len(valores))
            
            cur.execute(f"""
                INSERT INTO categorias ({campos_sql})
                VALUES ({placeholders})
                RETURNING id
            """, valores)
            result = cur.fetchone()
            categoria_ids[nome] = result['id'] if isinstance(result, dict) else result[0]
            print(f"  [OK] Categoria '{nome}' criada (ID: {categoria_ids[nome]})")
    
    conn.commit()
    
    # 2. Criar tamanhos
    # Verificar colunas disponíveis na tabela tamanho
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='tamanho'
    """)
    colunas_tamanho = [row[0] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
    
    tamanhos = ['P', 'M', 'G', 'GG']
    tamanho_ids = {}
    for idx, nome in enumerate(tamanhos):
        cur.execute("SELECT id FROM tamanho WHERE nome = %s LIMIT 1", (nome,))
        row = cur.fetchone()
        if row:
            tamanho_ids[nome] = row['id'] if isinstance(row, dict) else row[0]
        else:
            campos = ['nome']
            valores = [nome]
            
            if 'ativo' in colunas_tamanho:
                campos.append('ativo')
                valores.append(True)
            
            if 'ordem_exibicao' in colunas_tamanho:
                campos.append('ordem_exibicao')
                valores.append(idx)
            
            campos_sql = ', '.join(campos)
            placeholders = ', '.join(['%s'] * len(valores))
            
            cur.execute(f"""
                INSERT INTO tamanho ({campos_sql})
                VALUES ({placeholders})
                RETURNING id
            """, valores)
            result = cur.fetchone()
            tamanho_ids[nome] = result['id'] if isinstance(result, dict) else result[0]
            print(f"  [OK] Tamanho '{nome}' criado (ID: {tamanho_ids[nome]})")
    
    conn.commit()
    
    # 3. Criar estampas (precisam de categoria_id e imagem_url)
    # Verificar colunas disponíveis na tabela estampa
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='estampa'
    """)
    colunas_estampa = [row[0] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
    
    estampas = [
        ('Sem Estampa', categoria_ids['Camisetas']),
        ('Lhama Feliz', categoria_ids['Camisetas']),
        ('Lhama Espacial', categoria_ids['Camisetas']),
        ('Lhama Surfista', categoria_ids['Regatas'])
    ]
    
    estampa_ids = {}
    for nome, cat_id in estampas:
        cur.execute("SELECT id FROM estampa WHERE nome = %s AND categoria_id = %s LIMIT 1", (nome, cat_id))
        row = cur.fetchone()
        if row:
            estampa_ids[nome] = row['id'] if isinstance(row, dict) else row[0]
        else:
            imagem_url = f"https://via.placeholder.com/300?text={nome.replace(' ', '+')}"
            
            campos = ['nome', 'categoria_id', 'imagem_url', 'custo_por_metro']
            valores = [nome, cat_id, imagem_url, 0.00]
            
            if 'ativo' in colunas_estampa:
                campos.append('ativo')
                valores.append(True)
            
            campos_sql = ', '.join(campos)
            placeholders = ', '.join(['%s'] * len(valores))
            
            cur.execute(f"""
                INSERT INTO estampa ({campos_sql})
                VALUES ({placeholders})
                RETURNING id
            """, valores)
            result = cur.fetchone()
            estampa_ids[nome] = result['id'] if isinstance(result, dict) else result[0]
            print(f"  [OK] Estampa '{nome}' criada (ID: {estampa_ids[nome]})")
    
    conn.commit()
    
    return categoria_ids, tamanho_ids, estampa_ids


def criar_nome_produto(cur, conn, nome, categoria_id):
    """Cria ou retorna nome_produto"""
    cur.execute("SELECT id FROM nome_produto WHERE nome = %s LIMIT 1", (nome,))
    row = cur.fetchone()
    if row:
        return row['id'] if isinstance(row, dict) else row[0]
    
    cur.execute("""
        INSERT INTO nome_produto (nome, categoria_id)
        VALUES (%s, %s)
        RETURNING id
    """, (nome, categoria_id))
    result = cur.fetchone()
    nome_produto_id = result['id'] if isinstance(result, dict) else result[0]
    conn.commit()
    return nome_produto_id


def criar_produto(cur, conn, produto_data):
    """Cria um produto de teste"""
    # Verificar se produto já existe pelo SKU
    cur.execute("SELECT id FROM produtos WHERE codigo_sku = %s LIMIT 1", (produto_data['sku'],))
    existing = cur.fetchone()
    if existing:
        produto_id = existing['id'] if isinstance(existing, dict) else existing[0]
        print(f"  ⚠ Produto {produto_data['sku']} já existe (ID: {produto_id})")
        return produto_id
    
    # Verificar colunas existentes
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='produtos'
        ORDER BY ordinal_position
    """)
    colunas = [row[0] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
    
    # Montar INSERT dinamicamente
    campos = ['nome_produto_id', 'estampa_id', 'tamanho_id', 'codigo_sku', 'preco_venda', 'custo', 'estoque']
    valores = [
        produto_data['nome_produto_id'],
        produto_data['estampa_id'],
        produto_data['tamanho_id'],
        produto_data['sku'],
        produto_data['preco_venda'],
        produto_data['custo'],
        produto_data['estoque']
    ]
    
    # Adicionar campos opcionais se existirem
    if 'ncm' in colunas and produto_data.get('ncm'):
        campos.append('ncm')
        valores.append(produto_data['ncm'])
    
    if 'preco_promocional' in colunas and produto_data.get('preco_promocional'):
        campos.append('preco_promocional')
        valores.append(produto_data['preco_promocional'])
    
    if 'ativo' in colunas:
        campos.append('ativo')
        valores.append(True)
    
    # Construir SQL
    campos_sql = ', '.join(campos)
    placeholders = ', '.join(['%s'] * len(valores))
    
    cur.execute(f"""
        INSERT INTO produtos ({campos_sql})
        VALUES ({placeholders})
        RETURNING id
    """, valores)
    
    result = cur.fetchone()
    produto_id = result['id'] if isinstance(result, dict) else result[0]
    conn.commit()
    
    print(f"  [OK] Produto criado: {produto_data['nome']} - {produto_data['tamanho']} | SKU: {produto_data['sku']} | ID: {produto_id}")
    
    return produto_id


def main():
    """Função principal"""
    print("=" * 70)
    print("CRIANDO PRODUTOS DE TESTE PARA INTEGRAÇÃO BLING")
    print("=" * 70)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # 1. Criar dados base
        print("\n1. Criando dados base (categorias, estampas, tamanhos)...")
        categoria_ids, tamanho_ids, estampa_ids = criar_dados_base_se_nao_existirem(cur, conn)
        
        # 2. Criar produtos de teste
        print("\n2. Criando produtos de teste...")
        
        produtos_teste = [
            {
                'nome': 'Camiseta Lhama Feliz',
                'categoria': 'Camisetas',
                'estampa': 'Lhama Feliz',
                'tamanho': 'M',
                'sku': 'CAM-LHF-M-001',
                'ncm': '61091000',
                'preco_venda': 89.90,
                'preco_promocional': 79.90,
                'custo': 45.00,
                'estoque': 50
            },
            {
                'nome': 'Camiseta Lhama Feliz',
                'categoria': 'Camisetas',
                'estampa': 'Lhama Feliz',
                'tamanho': 'G',
                'sku': 'CAM-LHF-G-001',
                'ncm': '61091000',
                'preco_venda': 89.90,
                'preco_promocional': 79.90,
                'custo': 45.00,
                'estoque': 30
            },
            {
                'nome': 'Camiseta Lhama Espacial',
                'categoria': 'Camisetas',
                'estampa': 'Lhama Espacial',
                'tamanho': 'M',
                'sku': 'CAM-LHE-M-001',
                'ncm': '61091000',
                'preco_venda': 95.00,
                'custo': 48.00,
                'estoque': 25
            },
            {
                'nome': 'Regata Lhama Surfista',
                'categoria': 'Regatas',
                'estampa': 'Lhama Surfista',
                'tamanho': 'M',
                'sku': 'REG-LHS-M-001',
                'ncm': '61092000',
                'preco_venda': 69.90,
                'preco_promocional': 59.90,
                'custo': 35.00,
                'estoque': 40
            },
            {
                'nome': 'Camiseta Sem Estampa',
                'categoria': 'Camisetas',
                'estampa': 'Sem Estampa',
                'tamanho': 'P',
                'sku': 'CAM-SEM-P-001',
                'ncm': '61091000',
                'preco_venda': 59.90,
                'custo': 30.00,
                'estoque': 20
            },
            {
                'nome': 'Camiseta Lhama Feliz',
                'categoria': 'Camisetas',
                'estampa': 'Lhama Feliz',
                'tamanho': 'GG',
                'sku': 'CAM-LHF-GG-001',
                'ncm': '61091000',
                'preco_venda': 89.90,
                'custo': 45.00,
                'estoque': 0  # Sem estoque para testar
            }
        ]
        
        produto_ids = []
        for produto_data in produtos_teste:
            # Criar nome_produto se necessário
            categoria_id = categoria_ids[produto_data['categoria']]
            nome_produto_id = criar_nome_produto(cur, conn, produto_data['nome'], categoria_id)
            
            # Criar produto
            produto_id = criar_produto(cur, conn, {
                'nome_produto_id': nome_produto_id,
                'estampa_id': estampa_ids[produto_data['estampa']],
                'tamanho_id': tamanho_ids[produto_data['tamanho']],
                'nome': produto_data['nome'],
                'tamanho': produto_data['tamanho'],
                'sku': produto_data['sku'],
                'ncm': produto_data['ncm'],
                'preco_venda': produto_data['preco_venda'],
                'preco_promocional': produto_data.get('preco_promocional'),
                'custo': produto_data['custo'],
                'estoque': produto_data['estoque']
            })
            produto_ids.append(produto_id)
        
        print("\n" + "=" * 70)
        print("[OK] PRODUTOS DE TESTE CRIADOS COM SUCESSO!")
        print("=" * 70)
        print(f"\nTotal de produtos criados: {len(produto_ids)}")
        print("\nProdutos criados:")
        for i, produto_id in enumerate(produto_ids, 1):
            produto = produtos_teste[i-1]
            print(f"  {i}. {produto['nome']} - {produto['tamanho']} (SKU: {produto['sku']}, ID: {produto_id})")
        
        print("\n" + "=" * 70)
        print("PRÓXIMOS PASSOS - TESTAR SINCRONIZAÇÃO COM BLING")
        print("=" * 70)
        print("\n1. Sincronizar um produto específico:")
        for produto_id in produto_ids[:2]:  # Mostrar apenas os 2 primeiros
            print(f"   POST /api/bling/produtos/sync/{produto_id}")
        
        print("\n2. Sincronizar todos os produtos:")
        print("   POST /api/bling/produtos/sync-all")
        
        print("\n3. Verificar status de sincronização:")
        print(f"   GET /api/bling/produtos/status/{produto_ids[0]}")
        
        print("\n4. Sincronizar estoque do Bling:")
        print("   POST /api/bling/estoque/sync-from-bling")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO] Erro ao criar produtos de teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
