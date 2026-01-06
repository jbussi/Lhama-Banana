from . import api_bp
from flask import jsonify, request
from ..services.auth_service import verify_firebase_token
from ..services.user_service import get_user_by_firebase_uid, get_user_orders

@api_bp.route('/orders', methods=['GET'])
def get_orders():
    """Retorna todos os pedidos do usuário logado."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    id_token = auth_header.split(' ')[1]
    
    try:
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token['uid']
        
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        orders = get_user_orders(user_data['id'])
        return jsonify({"orders": orders}), 200
        
    except Exception as e:
        print(f"Erro ao buscar pedidos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor"}), 500
