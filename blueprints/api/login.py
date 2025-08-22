from . import api_bp
from flask import request, jsonify, session
from firebase_admin import auth
from ..services import get_db

@api_bp.route('/login_user', methods=["POST"])
def login_api():
        # método POST:
    data = request.get_json()
    id_token = data.get("id_token") # pode ser None se não enviado
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401


    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']        
        conn = get_db() # Obtém a conexão do pool
        cur = conn.cursor()
        # Buscar dados do usuário
        cur.execute("""
            SELECT id, nome, email, cpf, data_nascimento, criado_em, telefone
            FROM usuarios WHERE firebase_uid = %s
        """, (uid,))
        user = cur.fetchone()

        if user is None:
            cur.close()
            return jsonify({"erro": "Usuário não encontrado em seu sistema. Por favor, registre-se."}), 404

        cur.close()

        session['uid'] = uid
        return jsonify({"mensagem": "Login efetuado com sucesso"}), 200
    except Exception as e:
        print("Erro ao consultar usuário:", e)
        return jsonify({"erro": "Erro interno do servidor ao efetuar login"}), 500