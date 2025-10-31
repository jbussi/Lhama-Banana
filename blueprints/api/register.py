from . import api_bp
from flask import request, jsonify
from ..services import get_db
from firebase_admin import auth

@api_bp.route('/register_user', methods=["POST"])
def register_api():
    # método POST:
    data = request.get_json()
    
    if not data:
        print("Erro: Dados JSON não recebidos")
        return jsonify({"erro": "Dados não recebidos"}), 400
    
    id_token = data.get("id_token")  # Token JWT enviado pelo frontend
    username = data.get("username")

    if not id_token:
        print("Erro: Token não fornecido")
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    if not username:
        print("Erro: Username não fornecido")
        return jsonify({"erro": "Nome de usuário é obrigatório"}), 400

    try:
        # Verifica e decodifica o token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token['email']
        
        print(f"Token verificado com sucesso. UID: {uid}, Email: {email}")
        
        # Agora insere no banco com o uid validado
        conn = get_db() # Obtém a conexão do pool
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (firebase_uid, nome, email) VALUES (%s, %s, %s)",
            (uid, username, email)
        )
        conn.commit()
        cur.close()
        
        print(f"Usuário {username} criado com sucesso no banco")

        return jsonify({"mensagem": "Conta criada com sucesso"}), 200

    except auth.InvalidIdTokenError as e:
        print(f"Token inválido: {e}")
        return jsonify({"erro": "Token inválido"}), 401
    except auth.ExpiredIdTokenError as e:
        print(f"Token expirado: {e}")
        return jsonify({"erro": "Token expirado"}), 401
    except Exception as e:
        print(f"Erro ao salvar usuário no banco: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro interno ao salvar usuário: {str(e)}"}), 500