from .db import get_db
from flask import request, jsonify, g

def ensure_carrinhos_table_exists(conn):
    """
    Garante que as tabelas carrinhos e carrinho_itens existam.
    Cria-as se não existirem.
    """
    cur = conn.cursor()
    try:
        # Verifica se a tabela carrinhos existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'carrinhos'
            );
        """)
        carrinhos_exists = cur.fetchone()[0]
        
        # Verifica se a tabela carrinho_itens existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'carrinho_itens'
            );
        """)
        carrinho_itens_exists = cur.fetchone()[0]
        
        if not carrinhos_exists or not carrinho_itens_exists:
            print("Criando tabelas de carrinho...")
            
            # Cria a tabela carrinhos se não existir
            if not carrinhos_exists:
                print("  - Criando tabela 'carrinhos'...")
                cur.execute("""
                    CREATE TABLE carrinhos (
                        id SERIAL PRIMARY KEY,
                        usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                        session_id VARCHAR(255) UNIQUE,
                        criado_em TIMESTAMP DEFAULT NOW(),
                        atualizado_em TIMESTAMP DEFAULT NOW(),
                        expira_em TIMESTAMP,
                        UNIQUE (usuario_id)
                    );
                """)
            
            # Cria a tabela carrinho_itens se não existir
            if not carrinho_itens_exists:
                print("  - Criando tabela 'carrinho_itens'...")
                cur.execute("""
                    CREATE TABLE carrinho_itens (
                        id SERIAL PRIMARY KEY,
                        carrinho_id INTEGER REFERENCES carrinhos(id) ON DELETE CASCADE,
                        produto_id INTEGER REFERENCES produtos(id) ON DELETE RESTRICT,
                        quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                        preco_unitario_no_momento DECIMAL(10, 2) NOT NULL,
                        adicionado_em TIMESTAMP DEFAULT NOW(),
                        UNIQUE (carrinho_id, produto_id)
                    );
                """)
            
            # Cria a função update_timestamp se não existir
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_timestamp()
                RETURNS TRIGGER AS $$
                BEGIN
                   NEW.atualizado_em = NOW();
                   RETURN NEW;
                END;
                $$ language plpgsql;
            """)
            
            # Cria os triggers
            cur.execute("""
                DROP TRIGGER IF EXISTS trg_carrinhos_update_timestamp ON carrinhos;
                CREATE TRIGGER trg_carrinhos_update_timestamp 
                    BEFORE UPDATE ON carrinhos 
                    FOR EACH ROW 
                    EXECUTE FUNCTION update_timestamp();
            """)
            
            cur.execute("""
                DROP TRIGGER IF EXISTS trg_carrinho_itens_update_timestamp ON carrinho_itens;
                CREATE TRIGGER trg_carrinho_itens_update_timestamp 
                    BEFORE UPDATE ON carrinho_itens 
                    FOR EACH ROW 
                    EXECUTE FUNCTION update_timestamp();
            """)
            
            conn.commit()
            print("✓ Tabelas 'carrinhos' e 'carrinho_itens' criadas com sucesso.")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar tabelas de carrinho: {e}")
        raise
    finally:
        if cur:
            cur.close()

def get_or_create_cart(user_id=None, session_id=None):
    """
    Obtém o carrinho de um usuário logado ou de uma sessão anônima.
    Cria um novo carrinho se não existir.
    Retorna o ID do carrinho no DB.
    """
    conn = get_db()
    
    # Garante que as tabelas existam antes de usar
    try:
        ensure_carrinhos_table_exists(conn)
    except Exception as e:
        print(f"Erro ao garantir existência das tabelas: {e}")
        # Continua mesmo se houver erro, pode ser que as tabelas já existam
    
    cur = conn.cursor()
    carrinho_id = None

    try:
        if user_id:
            # Lembre-se que usuario_id na tabela carrinhos agora referencia usuarios(id), que é INTEGER
            cur.execute("SELECT id FROM carrinhos WHERE usuario_id = %s", (user_id,))
            result = cur.fetchone()
            if result:
                carrinho_id = result[0]
            else:
                cur.execute("INSERT INTO carrinhos (usuario_id) VALUES (%s) RETURNING id", (user_id,))
                carrinho_id = cur.fetchone()[0]
                conn.commit()
        elif session_id:
            cur.execute("SELECT id FROM carrinhos WHERE session_id = %s", (session_id,))
            result = cur.fetchone()
            if result:
                carrinho_id = result[0]
            else:
                cur.execute("INSERT INTO carrinhos (session_id) VALUES (%s) RETURNING id", (session_id,))
                carrinho_id = cur.fetchone()[0]
                conn.commit()
        else:
            # Isso não deve acontecer se get_cart_owner_info for bem-sucedido
            raise ValueError("user_id ou session_id deve ser fornecido para get_or_create_cart.")

    except Exception as e:
        conn.rollback() # Garante rollback em caso de erro na criação/busca
        print(f"Erro ao obter/criar carrinho: {e}")
        raise # Re-lança a exceção para que o endpoint a capture
    finally:
        if cur: cur.close()
    return carrinho_id

def get_cart_owner_info():
    """
    Determina o identificador do carrinho para a requisição atual.
    Prioriza usuário logado sobre sessão anônima.
    Retorna (erro_response, user_id, session_id). Se erro_response não for None, use-o.
    """
    user_id = None
    session_id_from_header = request.headers.get('X-Session-ID') # Frontend envia este header

    # 1. Verifica se o usuário está logado
    # g.user_db_data é populado pelo decorador @login_required_and_load_user
    if hasattr(g, 'user_db_data') and g.user_db_data and g.user_db_data.get('id'):
        user_id = g.user_db_data['id']
        # Se logado, o session_id anônimo é ignorado para as operações de cart
        # (será usado apenas na mesclagem, se aplicável)
        return None, user_id, None
    
    # 2. Se não está logado, tenta usar o session_id do header
    if session_id_from_header:
        return None, None, session_id_from_header
    
    # 3. Se nem logado nem session_id, é um erro
    return jsonify({"erro": "Autenticação necessária ou ID de sessão anônima ausente."}), None, None
