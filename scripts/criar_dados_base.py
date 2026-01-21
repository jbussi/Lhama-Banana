"""
Script para criar dados base necessários antes de criar produtos
===============================================================
Cria categorias, tecidos, tamanhos e estampas iniciais
"""
import os
import sys
import psycopg2
import psycopg2.extras

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

# Carregar variaveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[AVISO] python-dotenv nao instalado. Usando variaveis de ambiente do sistema.")

# Configuracao do banco de dados
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'sistema_usuarios')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'far111111')


def get_db_connection():
    """Conecta ao banco de dados"""
    dsn = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
    return psycopg2.connect(dsn, client_encoding='UTF8')


def criar_categoria(cur, nome, descricao=None, ordem=0):
    """Cria categoria se não existir"""
    cur.execute("SELECT id FROM categorias WHERE nome = %s", (nome,))
    existing = cur.fetchone()
    
    if existing:
        print(f"  [OK] Categoria '{nome}' já existe (ID: {existing[0]})")
        return existing[0]
    
    # Verificar se campo descricao existe
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='categorias' AND column_name='descricao'
    """)
    tem_descricao = cur.fetchone() is not None
    
    if tem_descricao:
        cur.execute("""
            INSERT INTO categorias (nome, descricao, ordem_exibicao, ativo)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
        """, (nome, descricao, ordem))
    else:
        cur.execute("""
            INSERT INTO categorias (nome, ordem_exibicao, ativo)
            VALUES (%s, %s, TRUE)
            RETURNING id
        """, (nome, ordem))
    
    categoria_id = cur.fetchone()[0]
    print(f"  [OK] Categoria '{nome}' criada (ID: {categoria_id})")
    return categoria_id


def criar_tecido(cur, nome, descricao=None, ordem=0):
    """Cria tecido se não existir"""
    cur.execute("SELECT id FROM tecidos WHERE nome = %s", (nome,))
    existing = cur.fetchone()
    
    if existing:
        print(f"  [OK] Tecido '{nome}' já existe (ID: {existing[0]})")
        return existing[0]
    
    # Verificar se campo descricao existe
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='tecidos' AND column_name='descricao'
    """)
    tem_descricao = cur.fetchone() is not None
    
    if tem_descricao:
        cur.execute("""
            INSERT INTO tecidos (nome, descricao, ordem_exibicao, ativo)
            VALUES (%s, %s, %s, TRUE)
            RETURNING id
        """, (nome, descricao, ordem))
    else:
        cur.execute("""
            INSERT INTO tecidos (nome, ordem_exibicao, ativo)
            VALUES (%s, %s, TRUE)
            RETURNING id
        """, (nome, ordem))
    
    tecido_id = cur.fetchone()[0]
    print(f"  [OK] Tecido '{nome}' criado (ID: {tecido_id})")
    return tecido_id


def criar_tamanho(cur, nome, ordem=0):
    """Cria tamanho se não existir"""
    cur.execute("SELECT id FROM tamanho WHERE nome = %s", (nome,))
    existing = cur.fetchone()
    
    if existing:
        print(f"  [OK] Tamanho '{nome}' já existe (ID: {existing[0]})")
        return existing[0]
    
    cur.execute("""
        INSERT INTO tamanho (nome, ordem_exibicao, ativo)
        VALUES (%s, %s, TRUE)
        RETURNING id
    """, (nome, ordem))
    
    tamanho_id = cur.fetchone()[0]
    print(f"  [OK] Tamanho '{nome}' criado (ID: {tamanho_id})")
    return tamanho_id


def criar_estampa(cur, nome, categoria_id, imagem_url, custo_por_metro=0.0, tecido_id=None, ordem=0):
    """Cria estampa se não existir"""
    cur.execute("SELECT id FROM estampa WHERE nome = %s", (nome,))
    existing = cur.fetchone()
    
    if existing:
        print(f"  [OK] Estampa '{nome}' já existe (ID: {existing[0]})")
        return existing[0]
    
    cur.execute("""
        INSERT INTO estampa (nome, categoria_id, imagem_url, custo_por_metro, tecido_id, ordem_exibicao, ativo)
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        RETURNING id
    """, (nome, categoria_id, imagem_url, custo_por_metro, tecido_id, ordem))
    
    estampa_id = cur.fetchone()[0]
    print(f"  [OK] Estampa '{nome}' criada (ID: {estampa_id})")
    return estampa_id


def main():
    """Funcao principal"""
    print("=" * 60)
    print("CRIANDO DADOS BASE DO SISTEMA")
    print("=" * 60)
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # 1. Criar categorias
        print("\n1. Criando categorias...")
        cat_infantil = criar_categoria(cur, "Infantil", "Produtos para crianças", 1)
        cat_adulto = criar_categoria(cur, "Adulto", "Produtos para adultos", 2)
        cat_bebe = criar_categoria(cur, "Bebê", "Produtos para bebês", 0)
        
        # 2. Criar tecidos
        print("\n2. Criando tecidos...")
        tecido_algodao = criar_tecido(cur, "Algodão", "Algodão 100%", 1)
        tecido_malha = criar_tecido(cur, "Malha", "Tecido de malha", 2)
        tecido_misto = criar_tecido(cur, "Misto", "Algodão com poliéster", 3)
        
        # 3. Criar tamanhos
        print("\n3. Criando tamanhos...")
        tamanhos = [
            ("RN", 0), ("P", 1), ("M", 2), ("G", 3), ("GG", 4),
            ("0-3M", 10), ("3-6M", 11), ("6-12M", 12), ("12-24M", 13),
            ("Único", 20)
        ]
        
        tamanho_ids = {}
        for nome, ordem in tamanhos:
            tamanho_ids[nome] = criar_tamanho(cur, nome, ordem)
        
        # 4. Criar estampas básicas
        print("\n4. Criando estampas básicas...")
        estampas = [
            ("Sem Estampa", cat_infantil, "https://via.placeholder.com/300?text=Sem+Estampa", 0.0, None, 0),
            ("Lhama Básica", cat_infantil, "https://via.placeholder.com/300?text=Lhama", 0.0, None, 1),
        ]
        
        estampa_ids = {}
        for nome, cat_id, img_url, custo, tec_id, ordem in estampas:
            estampa_ids[nome] = criar_estampa(cur, nome, cat_id, img_url, custo, tec_id, ordem)
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("[OK] DADOS BASE CRIADOS COM SUCESSO!")
        print("=" * 60)
        
        print("\nResumo:")
        print(f"  - Categorias: {len([cat_infantil, cat_adulto, cat_bebe])}")
        print(f"  - Tecidos: {len([tecido_algodao, tecido_malha, tecido_misto])}")
        print(f"  - Tamanhos: {len(tamanhos)}")
        print(f"  - Estampas: {len(estampas)}")
        
        print("\nPróximo passo:")
        print("  - Você pode criar mais categorias, tecidos, tamanhos e estampas via API")
        print("  - Ou diretamente no banco de dados")
        print("  - Depois disso, você pode criar produtos")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO] Erro ao criar dados base: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
