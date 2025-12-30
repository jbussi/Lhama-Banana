"""
API para gerenciar pedidos (orders) com token público
"""
from flask import Blueprint, request, jsonify, current_app
from ..services.order_service import get_order_by_token, update_order_status
from ..services import get_db
import psycopg2.extras

orders_api_bp = Blueprint('orders_api', __name__, url_prefix='/api/orders')


@orders_api_bp.route('/<string:token>', methods=['GET'])
def get_order_by_token_api(token):
    """
    Retorna os dados de um pedido pelo token público.
    
    GET /api/orders/<token>
    
    Returns:
        JSON com dados do pedido ou erro 404 se não encontrado
    """
    try:
        order = get_order_by_token(token)
        
        if not order:
            return jsonify({
                "erro": "Pedido não encontrado",
                "message": "O token fornecido não corresponde a nenhum pedido válido"
            }), 404
        
        # Se o pedido foi entregue, o token deve ser removido
        # Mas ainda permitimos a consulta uma última vez
        if order.get('status') == 'ENTREGUE':
            # Verificar se o token ainda existe (não foi removido)
            # Se foi removido, retornar erro
            if not order.get('public_token'):
                return jsonify({
                    "erro": "Pedido não disponível",
                    "message": "Este pedido foi finalizado e não está mais disponível para consulta"
                }), 404
        
        # Preparar resposta
        response_data = {
            "success": True,
            "order": {
                "id": order.get('id'),
                "codigo_pedido": order.get('codigo_pedido'),
                "status": order.get('status'),
                "valor": order.get('valor'),
                "criado_em": order.get('criado_em'),
                "atualizado_em": order.get('atualizado_em'),
                "data_venda": order.get('data_venda'),
                "status_pagamento": order.get('status_pagamento'),
                "forma_pagamento": order.get('forma_pagamento'),
                # Dados específicos de pagamento
                "pix": {
                    "qr_code_link": order.get('pix_qr_code_link'),
                    "qr_code_image": order.get('pix_qr_code_image'),
                    "qr_code_text": order.get('pix_qr_code_text')
                } if order.get('forma_pagamento') == 'PIX' else None,
                "boleto": {
                    "link": order.get('boleto_link'),
                    "barcode": order.get('boleto_barcode'),
                    "expires_at": order.get('boleto_expires_at')
                } if order.get('forma_pagamento') == 'BOLETO' else None
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar pedido por token: {e}")
        return jsonify({
            "erro": "Erro interno ao buscar pedido",
            "message": str(e) if current_app.config.get('DEBUG', False) else "Erro interno do servidor"
        }), 500


@orders_api_bp.route('/<string:token>/status', methods=['GET'])
def get_order_status_api(token):
    """
    Retorna apenas o status de um pedido pelo token público.
    Endpoint mais leve para polling.
    
    GET /api/orders/<token>/status
    
    Returns:
        JSON com status do pedido
    """
    try:
        order = get_order_by_token(token)
        
        if not order:
            return jsonify({
                "erro": "Pedido não encontrado"
            }), 404
        
        return jsonify({
            "success": True,
            "status": order.get('status'),
            "atualizado_em": order.get('atualizado_em')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar status do pedido: {e}")
        return jsonify({
            "erro": "Erro interno ao buscar status"
        }), 500

