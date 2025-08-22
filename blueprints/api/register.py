from . import api_bp
from flask import request, jsonify
from ..services import get_db
from firebase_admin import auth

@api_bp.route('/register_user', methods=["POST"])
def register_api():
    # método POST:
    data = request.get_json()
    id_token = data.get("id_token")  # Token JWT enviado pelo frontend
    username = data.get("username")

    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401

    try:
        # Verifica e decodifica o token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token['email']
        # Agora insere no banco com o uid validado
        conn = get_db() # Obtém a conexão do pool
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (firebase_uid, nome, email) VALUES (%s, %s, %s)",
            (uid, username, email)
        )
        conn.commit()
        cur.close()

        return jsonify({"mensagem": "Conta criada com sucesso"}), 200

    except auth.InvalidIdTokenError:
        return jsonify({"erro": "Token inválido"}), 401
    except auth.ExpiredIdTokenError:
        return jsonify({"erro": "Token expirado"}), 401
    except Exception as e:
        print(f"Erro ao salvar usuário no banco: {e}")
        return jsonify({"erro": "Erro interno ao salvar usuário"}), 500