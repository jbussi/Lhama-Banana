from . import api_bp
from flask import jsonify, request, g
from ..services import login_required_and_load_user, get_user_by_firebase_uid, update_user_profile_db
from firebase_admin import auth

# Rota API para obter os dados do perfil do usuário logado (GET JSON)
@api_bp.route('/user_data', methods=["GET"])
@login_required_and_load_user # Garante que o usuário está logado e g.user está populado
def get_user_profile_data_api():
    # g.user já está populado pelo decorator com todos os dados (principais, endereços, vendas)
    return jsonify(g.user)

@api_bp.route('/user_data', methods=["PUT"]) # ou POST, mas PUT é mais semântico para atualização
def update_user_profile_api():
    data = request.get_json()
    id_token = request.headers.get("Authorization").split("Bearer ")[1] # Pega o token do header

    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401

    try:
        decoded_token = auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        
        # Busque o usuário pelo firebase_uid para obter o id interno do seu DB
        user_in_db = get_user_by_firebase_uid(firebase_uid)
        if not user_in_db:
            return jsonify({"erro": "Usuário não encontrado em seu sistema."}), 404
        
        user_id_db = user_in_db['id']

        # Limpa dados que não devem ser atualizados via essa rota ou que são gerados pelo Firebase
        data_to_update = {k: v for k, v in data.items() if k in ['nome', 'email', 'cpf', 'data_nascimento', 'telefone']}
        
        if update_user_profile_db(user_id_db, data_to_update):
            return jsonify({"mensagem": "Perfil atualizado com sucesso"}), 200
        else:
            return jsonify({"erro": "Falha ao atualizar perfil no banco de dados"}), 500
    except auth.InvalidIdTokenError:
        return jsonify({"erro": "Token inválido ou expirado"}), 401
    except Exception as e:
        print(f"Erro ao atualizar perfil: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500