from flask import Blueprint, request, jsonify, current_app
from ..services.shipping_service import shipping_service
from ..services import get_db, get_cart_owner_info, get_or_create_cart
import json

shipping_api_bp = Blueprint('shipping_api', __name__)

@shipping_api_bp.route('/calculate', methods=['POST'])
def calculate_shipping():
    """
    Calcula opções de frete para um CEP de destino
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Dados da requisição ausentes"}), 400
            
        cep_destino = data.get('cep')
        if not cep_destino:
            return jsonify({"erro": "CEP de destino é obrigatório"}), 400
            
        # Obter informações do carrinho para calcular peso e dimensões
        error_response, user_id, session_id = get_cart_owner_info()
        if error_response:
            return error_response
            
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Obter o ID do carrinho
            cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
            if not cart_id:
                return jsonify({"erro": "Não foi possível identificar o carrinho"}), 500
                
            # Buscar itens do carrinho para calcular peso total
            cur.execute("""
                SELECT 
                    ci.quantidade,
                    p.codigo_sku,
                    np.nome AS product_name
                FROM carrinho_itens ci
                JOIN produtos p ON ci.produto_id = p.id
                JOIN nome_produto np ON p.nome_produto_id = np.id
                WHERE ci.carrinho_id = %s
            """, (cart_id,))
            
            cart_items = cur.fetchall()
            
            if not cart_items:
                return jsonify({"erro": "Carrinho vazio"}), 400
                
            # Calcular peso total (simulado - em produção usar peso real dos produtos)
            peso_total = len(cart_items) * 0.5  # 500g por item (simulado)
            
            # Calcular valor total
            cur.execute("""
                SELECT SUM(ci.quantidade * ci.preco_unitario_no_momento) as total
                FROM carrinho_itens ci
                WHERE ci.carrinho_id = %s
            """, (cart_id,))
            
            valor_total = cur.fetchone()[0] or 0.0
            
            # Dimensões padrão (em produção, usar dimensões reais dos produtos)
            dimensoes = {
                'altura': 10,  # cm
                'largura': 20,  # cm
                'comprimento': 30  # cm
            }
            
            # Calcular opções de frete
            shipping_options = shipping_service.calculate_shipping(
                cep_destino=cep_destino,
                peso_total=peso_total,
                valor_total=valor_total,
                dimensoes=dimensoes
            )
            
            if not shipping_options:
                return jsonify({"erro": "Não foi possível calcular o frete para este CEP"}), 400
                
            return jsonify({
                "success": True,
                "cep": cep_destino,
                "peso_total": peso_total,
                "valor_total": valor_total,
                "shipping_options": shipping_options
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Erro ao calcular frete: {e}")
            return jsonify({"erro": "Erro interno ao calcular frete"}), 500
        finally:
            if cur:
                cur.close()
                
    except Exception as e:
        current_app.logger.error(f"Erro na API de frete: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@shipping_api_bp.route('/validate-cep', methods=['POST'])
def validate_cep():
    """
    Valida e busca informações de um CEP
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Dados da requisição ausentes"}), 400
            
        cep = data.get('cep')
        if not cep:
            return jsonify({"erro": "CEP é obrigatório"}), 400
            
        # Validar formato do CEP
        cep_clean = cep.replace('-', '').replace(' ', '')
        if len(cep_clean) != 8 or not cep_clean.isdigit():
            return jsonify({"erro": "CEP inválido"}), 400
            
        # Buscar informações do CEP
        cep_info = shipping_service._get_cep_info(cep_clean)
        
        if not cep_info:
            return jsonify({"erro": "CEP não encontrado"}), 404
            
        return jsonify({
            "success": True,
            "cep": cep_clean,
            "logradouro": cep_info.get('logradouro', ''),
            "bairro": cep_info.get('bairro', ''),
            "localidade": cep_info.get('localidade', ''),
            "uf": cep_info.get('uf', ''),
            "ibge": cep_info.get('ibge', ''),
            "gia": cep_info.get('gia', ''),
            "ddd": cep_info.get('ddd', ''),
            "siafi": cep_info.get('siafi', '')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao validar CEP: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500
