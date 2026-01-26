from flask import Blueprint, request, jsonify, current_app
from ..services.shipping_service import shipping_service
from ..services import get_db, get_cart_owner_info, get_or_create_cart
import json
import psycopg2.extras

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
        cur = None
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Obter o ID do carrinho
            cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
            if not cart_id:
                return jsonify({"erro": "Não foi possível identificar o carrinho"}), 500
                
            # Buscar itens do carrinho com peso e dimensões dos produtos
            cur.execute("""
                SELECT 
                    ci.quantidade,
                    p.codigo_sku,
                    p.peso_kg,
                    p.dimensoes_largura,
                    p.dimensoes_altura,
                    p.dimensoes_comprimento,
                    np.nome AS product_name
                FROM carrinho_itens ci
                JOIN produtos p ON ci.produto_id = p.id
                JOIN nome_produto np ON p.nome_produto_id = np.id
                WHERE ci.carrinho_id = %s
            """, (cart_id,))
            
            cart_items = cur.fetchall()
            
            if not cart_items:
                return jsonify({"erro": "Carrinho vazio"}), 400
            
            # Calcular peso total somando peso de cada item
            peso_total = 0.0
            max_altura = 0.0
            max_largura = 0.0
            soma_comprimento = 0.0
            
            for item in cart_items:
                quantidade = item['quantidade']
                peso_item = float(item['peso_kg'] or 0)
                peso_total += peso_item * quantidade
                
                # Para dimensões, usar a maior altura e largura, e somar comprimentos
                altura_item = float(item['dimensoes_altura'] or 0)
                largura_item = float(item['dimensoes_largura'] or 0)
                comprimento_item = float(item['dimensoes_comprimento'] or 0)
                
                if altura_item > max_altura:
                    max_altura = altura_item
                if largura_item > max_largura:
                    max_largura = largura_item
                soma_comprimento += comprimento_item * quantidade
            
            # Se não houver dimensões, usar valores padrão mínimos
            if peso_total == 0:
                peso_total = 0.3  # Mínimo de 300g
            if max_altura == 0:
                max_altura = 10
            if max_largura == 0:
                max_largura = 20
            if soma_comprimento == 0:
                soma_comprimento = 30
            
            dimensoes = {
                'altura': max_altura,
                'largura': max_largura,
                'comprimento': soma_comprimento
            }
            
            # Calcular valor total
            cur.execute("""
                SELECT SUM(ci.quantidade * ci.preco_unitario_no_momento) as total
                FROM carrinho_itens ci
                WHERE ci.carrinho_id = %s
            """, (cart_id,))
            
            valor_total = cur.fetchone()[0] or 0.0
            
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
            import traceback
            traceback.print_exc()
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
