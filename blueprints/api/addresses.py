from . import api_bp
from flask import jsonify, request
from ..services.auth_service import verify_firebase_token
from ..services.user_service import get_user_by_firebase_uid, create_user_address, update_user_address, delete_user_address, get_user_addresses

@api_bp.route('/addresses', methods=['GET'])
def get_addresses():
    """Retorna todos os endereços do usuário logado."""
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
        
        addresses = get_user_addresses(user_data['id'])
        return jsonify({"addresses": addresses}), 200
        
    except Exception as e:
        print(f"Erro ao buscar endereços: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@api_bp.route('/addresses', methods=['POST'])
def create_address():
    """Cria um novo endereço para o usuário logado."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    id_token = auth_header.split(' ')[1]
    data = request.get_json()
    
    try:
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token['uid']
        
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        # Validação básica
        required_fields = ['zipcode', 'street', 'number', 'neighborhood', 'city', 'state']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"erro": f"Campo obrigatório ausente: {field}"}), 400
        
        address_id, error = create_user_address(user_data['id'], data)
        if error:
            return jsonify({"erro": error}), 400
        
        # Retornar o endereço criado
        addresses = get_user_addresses(user_data['id'])
        new_address = next((a for a in addresses if a['id'] == address_id), None)
        
        if new_address:
            return jsonify({"mensagem": "Endereço criado com sucesso", "address": new_address}), 201
        else:
            return jsonify({"mensagem": "Endereço criado com sucesso", "address_id": address_id}), 201
        
    except Exception as e:
        print(f"Erro ao criar endereço: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@api_bp.route('/addresses/<int:address_id>', methods=['PUT'])
def update_address(address_id):
    """Atualiza um endereço do usuário logado."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    id_token = auth_header.split(' ')[1]
    data = request.get_json()
    
    try:
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token['uid']
        
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        success, error = update_user_address(user_data['id'], address_id, data)
        if error:
            return jsonify({"erro": error}), 400
        
        if not success:
            return jsonify({"erro": "Falha ao atualizar endereço"}), 500
        
        # Retornar o endereço atualizado
        addresses = get_user_addresses(user_data['id'])
        updated_address = next((a for a in addresses if a['id'] == address_id), None)
        
        return jsonify({"mensagem": "Endereço atualizado com sucesso", "address": updated_address}), 200
        
    except Exception as e:
        print(f"Erro ao atualizar endereço: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@api_bp.route('/addresses/<int:address_id>', methods=['DELETE'])
def delete_address(address_id):
    """Remove um endereço do usuário logado."""
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
        
        success, error = delete_user_address(user_data['id'], address_id)
        if error:
            return jsonify({"erro": error}), 400
        
        if not success:
            return jsonify({"erro": "Falha ao remover endereço"}), 500
        
        return jsonify({"mensagem": "Endereço removido com sucesso"}), 200
        
    except Exception as e:
        print(f"Erro ao remover endereço: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

