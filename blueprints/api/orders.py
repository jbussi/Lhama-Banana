from . import api_bp
from flask import jsonify, request, current_app
from ..services.auth_service import verify_firebase_token
from ..services.user_service import get_user_by_firebase_uid, get_user_orders
from ..services.order_service import get_order_by_token

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


@api_bp.route('/orders/<token>', methods=['GET'])
def get_order_by_public_token(token):
    """
    Retorna dados completos do pedido pelo token público.
    Usado na página de status do pedido.
    """
    try:
        order = get_order_by_token(token)
        
        if not order:
            return jsonify({
                "success": False,
                "erro": "Pedido não encontrado"
            }), 404
        
        # Estruturar dados do PIX se disponível
        if order.get('forma_pagamento') == 'PIX' or order.get('pix_qr_code_link') or order.get('pix_qr_code_text'):
            order['pix'] = {
                'qr_code_link': order.get('pix_qr_code_link', ''),
                'qr_code_image': order.get('pix_qr_code_image', ''),
                'qr_code_text': order.get('pix_qr_code_text', '')
            }
        
        # Estruturar dados do Boleto se disponível
        if order.get('forma_pagamento') == 'BOLETO' or order.get('boleto_link') or order.get('boleto_barcode'):
            order['boleto'] = {
                'link': order.get('boleto_link', ''),
                'barcode': order.get('boleto_barcode', ''),
                'expires_at': order.get('boleto_expires_at', '')
            }
        
        return jsonify({
            "success": True,
            "order": order
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar pedido por token: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "erro": "Erro ao buscar dados do pedido"
        }), 500


@api_bp.route('/orders/<token>/status', methods=['GET'])
def get_order_status_only(token):
    """
    Retorna apenas o status do pedido (para polling).
    Mais leve que o endpoint completo.
    """
    try:
        order = get_order_by_token(token)
        
        if not order:
            return jsonify({
                "success": False,
                "erro": "Pedido não encontrado"
            }), 404
        
        return jsonify({
            "success": True,
            "status": order.get('status', 'UNKNOWN')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar status do pedido: {e}")
        return jsonify({
            "success": False,
            "erro": "Erro ao buscar status do pedido"
        }), 500
