from .db import get_db
from flask import request, jsonify, g

def get_or_create_cart(user_id=None, session_id=None):
    """
    Obtém o carrinho de um usuário logado ou de uma sessão anônima.
    Cria um novo carrinho se não existir.
    Retorna o ID do carrinho no DB.
    """
    conn = get_db()
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
