"""
API endpoints para integração com PagBank
Especialmente para validação de cartões (dados sensíveis isolados aqui)

NOTA: O endpoint /cards do PagBank retorna 403 (Cloudflare).
Como o PagBank aceita dados do cartão diretamente no payload do pedido,
este endpoint apenas valida os dados e retorna um identificador seguro.
Os dados serão enviados diretamente ao PagBank no momento do checkout.
"""
import hashlib
import hmac
import time
import datetime
from flask import Blueprint, request, jsonify, current_app, session

pagbank_api_bp = Blueprint('pagbank_api', __name__, url_prefix='/api/pagbank')

# Armazenamento temporário em memória (apenas durante a sessão)
# Em produção, considere usar Redis com TTL curto
_card_data_cache = {}


@pagbank_api_bp.route('/validate-card', methods=['POST'])
def validate_card_endpoint():
    """
    Endpoint isolado para validar dados do cartão.
    Este é o ÚNICO lugar onde dados completos do cartão são recebidos.
    Valida os dados e retorna um identificador seguro que será usado no checkout.
    
    POST /api/pagbank/validate-card
    Body: {
        "card_number": "4539620659922097",
        "card_exp_month": "12",
        "card_exp_year": "2030",
        "card_cvv": "123",
        "card_holder_name": "João Silva",
        "card_holder_cpf_cnpj": "54160265880"
    }
    
    Retorna: {
        "success": true,
        "card_id": "hash_seguro_identificador"
    }
    """
    current_app.logger.info("[PagBank] Endpoint /validate-card chamado")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Dados não fornecidos"}), 400
        
        # Validar campos obrigatórios
        required_fields = ['card_number', 'card_exp_month', 'card_exp_year', 'card_cvv', 'card_holder_name', 'card_holder_cpf_cnpj']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                "erro": "Campos obrigatórios ausentes",
                "campos_faltando": missing_fields
            }), 400
        
        # Validar formato básico do cartão
        card_number = data.get('card_number', '').replace(' ', '').replace('-', '')
        if len(card_number) < 13 or len(card_number) > 19:
            return jsonify({
                "erro": "Número do cartão inválido"
            }), 400
        
        # Validar CVV
        card_cvv = data.get('card_cvv', '').strip()
        if len(card_cvv) < 3 or len(card_cvv) > 4:
            return jsonify({
                "erro": "CVV inválido"
            }), 400
        
        # Preparar dados do cartão (normalizados)
        card_data = {
            'card_number': card_number,
            'card_exp_month': data.get('card_exp_month', '').strip().zfill(2),
            'card_exp_year': data.get('card_exp_year', '').strip(),
            'card_cvv': card_cvv,
            'card_holder_name': data.get('card_holder_name', '').strip(),
            'card_holder_cpf_cnpj': data.get('card_holder_cpf_cnpj', '').replace('.', '').replace('-', '').replace('/', '').strip()
        }
        
        # Converter ano para 4 dígitos se necessário
        if len(card_data['card_exp_year']) == 2:
            current_year_prefix = str(datetime.datetime.now().year)[:2]
            card_data['card_exp_year'] = current_year_prefix + card_data['card_exp_year']
        
        # Gerar identificador seguro único baseado em hash
        # Usa timestamp + dados do cartão (sem CVV) para criar hash único
        secret = current_app.config.get('SECRET_KEY', 'default-secret-key')
        hash_input = f"{card_data['card_number']}{card_data['card_exp_month']}{card_data['card_exp_year']}{time.time()}{secret}"
        card_id = hashlib.sha256(hash_input.encode()).hexdigest()[:32]
        
        # Armazenar temporariamente (apenas durante esta requisição/sessão)
        # Os dados serão usados imediatamente no checkout e depois descartados
        _card_data_cache[card_id] = {
            'data': card_data,
            'timestamp': time.time(),
            'session_id': session.get('session_id', 'anonymous')
        }
        
        # Limpar cache antigo (mais de 5 minutos)
        current_time = time.time()
        keys_to_remove = [k for k, v in _card_data_cache.items() if current_time - v['timestamp'] > 300]
        for k in keys_to_remove:
            _card_data_cache.pop(k, None)
        
        current_app.logger.info(f"[PagBank] Dados do cartão validados e armazenados temporariamente (ID: {card_id[:8]}...)")
        
        # Retornar APENAS o identificador (sem dados sensíveis)
        return jsonify({
            "success": True,
            "card_id": card_id
        }), 200
            
    except Exception as e:
        current_app.logger.error(f"[PagBank] Erro inesperado no endpoint de validação: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "erro": "Erro interno do servidor. Tente novamente mais tarde."
        }), 500


def get_card_data_by_id(card_id: str):
    """
    Recupera dados do cartão pelo ID (apenas para uso interno no checkout).
    Remove os dados do cache após recuperar (uso único).
    """
    if card_id in _card_data_cache:
        data = _card_data_cache.pop(card_id)  # Remove após uso (uso único)
        return data['data']
    return None

