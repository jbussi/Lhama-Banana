from .db import get_db
from functools import wraps
from flask import session, redirect, url_for, flash, g

def get_user_by_firebase_uid(firebase_uid):
    """Busca os dados principais de um usuário pelo seu Firebase UID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, firebase_uid, nome, email, cpf, data_nascimento, criado_em, telefone
        FROM usuarios WHERE firebase_uid = %s
    """, (firebase_uid,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        # Retorna um dicionário para facilitar o acesso por nome da coluna
        # Adapte os índices conforme a ordem das colunas no seu SELECT
        return {
            'id': user_data[0],
            'firebase_uid': user_data[1],
            'nome': user_data[2],
            'email': user_data[3],
            'cpf': user_data[4],
            'data_nascimento': str(user_data[5]) if user_data[5] else None,
            'criado_em': str(user_data[6]),
            'telefone': user_data[7],
        }
    return None

def insert_new_user(firebase_uid, nome, email):
    """Insere um novo usuário na tabela 'usuarios'."""
    conn = get_db() # Obtém a conexão do pool
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (firebase_uid, nome, email) VALUES (%s, %s, %s) RETURNING id",
            (firebase_uid, nome, email)
        )
        new_user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return new_user_id
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao inserir novo usuário: {e}")
        return None

def update_user_profile_db(user_id, data):
    """Atualiza os dados de perfil de um usuário."""
    conn = get_db() # Obtém a conexão do pool
    cur = conn.cursor()
    try:
        cur = conn.cursor()
        # Construa a query dinamicamente para atualizar apenas campos presentes em 'data'
        updates = []
        params = []
        
        if 'nome' in data:
            updates.append("nome = %s")
            params.append(data['nome'])
        if 'email' in data: # Cuidado ao permitir atualização de email que é também UID no Firebase
            updates.append("email = %s")
            params.append(data['email'])
        if 'cpf' in data:
            updates.append("cpf = %s")
            params.append(data['cpf'])
        if 'data_nascimento' in data:
            updates.append("data_nascimento = %s")
            # Converta string para date object se necessário, ex: datetime.date.fromisoformat(data['data_nascimento'])
            params.append(data['data_nascimento']) 
        if 'telefone' in data:
            updates.append("telefone = %s")
            params.append(data['telefone'])

        if not updates: # Nenhuma atualização para fazer
            cur.close()
            return True

        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
        params.append(user_id)
        
        cur.execute(query, tuple(params))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao atualizar perfil do usuário {user_id}: {e}")
        return False

def login_required_and_load_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get('uid')
        if not uid:
            return redirect(url_for('auth.login_page')) # Sua rota de login HTML

        user_data = get_user_by_firebase_uid(uid) # Usa a função auxiliar
        if not user_data:
            session.pop('uid', None) # Limpa sessão se usuário não existe no DB
            return redirect(url_for('auth.login_page'))

        g.user = user_data # g.user agora é um dicionário com os dados principais

        # Busca dados relacionados e os adiciona a g.user
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador que verifica se o usuário tem permissão de administrador.
    Assume que `login_required_and_load_user` já foi aplicado e `g.user_db_data` está preenchido.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # g.user_db_data já deve estar preenchido por login_required_and_load_user
        if not hasattr(g, 'user_db_data') or g.user_db_data.get('role') != 'admin':
            flash("Acesso negado: Você não possui permissões de administrador.")
            # Você pode escolher redirecionar para uma página de acesso negado
            # ou simplesmente retornar um 404 (para não dar dicas sobre a existência da página)
            return redirect(url_for('home')) # Redireciona para a home
            # from flask import abort
            # abort(404) # Se quiser um 404 para esconder a página

        return f(*args, **kwargs)
    return decorated_function