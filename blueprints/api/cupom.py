"""
API de Cupons de Desconto
"""
from flask import Blueprint, request, jsonify, session, current_app
from ..services import get_db
from ..services.auth_service import verify_firebase_token
from ..services.user_service import get_user_by_firebase_uid
from datetime import datetime
import re

cupom_api_bp = Blueprint('cupom_api', __name__, url_prefix='/api/cupom')

@cupom_api_bp.route('/validate', methods=['POST'])
def validate_cupom():
    """
    Valida e aplica um cupom de desconto.
    Requer autenticação do usuário.
    """
    try:
        data = request.get_json()
        if not data or 'codigo' not in data:
            return jsonify({"erro": "Código do cupom é obrigatório"}), 400
        
        codigo_cupom = data.get('codigo', '').strip().upper()
        if not codigo_cupom:
            return jsonify({"erro": "Código do cupom não pode estar vazio"}), 400
        
        # Verificar autenticação
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                "erro": "Autenticação obrigatória",
                "mensagem": "Para usar cupons de desconto, você precisa ter uma conta.",
                "requer_login": True
            }), 401
        
        id_token = auth_header.split(' ')[1]
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({
                "erro": "Token inválido ou expirado",
                "mensagem": "Para usar cupons de desconto, você precisa ter uma conta.",
                "requer_login": True
            }), 401
        
        firebase_uid = decoded_token['uid']
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({
                "erro": "Usuário não encontrado",
                "mensagem": "Para usar cupons de desconto, você precisa ter uma conta.",
                "requer_login": True
            }), 404
        
        user_id = user_data['id']
        user_cpf = user_data.get('cpf')
        
        # Buscar cupom no banco
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                id, codigo, tipo, valor, valor_minimo_pedido,
                validade_inicio, validade_fim, uso_maximo, uso_maximo_por_usuario,
                uso_atual, ativo, descricao
            FROM cupom
            WHERE codigo = %s AND ativo = TRUE
        """, (codigo_cupom,))
        
        cupom_data = cur.fetchone()
        
        if not cupom_data:
            cur.close()
            return jsonify({"erro": "Cupom inválido ou inativo"}), 400
        
        cupom_id, codigo, tipo, valor, valor_minimo, validade_inicio, validade_fim, \
        uso_maximo, uso_maximo_por_usuario, uso_atual, ativo, descricao = cupom_data
        
        # Validar validade
        now = datetime.now()
        if validade_inicio and now < validade_inicio:
            cur.close()
            return jsonify({"erro": "Este cupom ainda não está válido"}), 400
        
        if validade_fim and now > validade_fim:
            cur.close()
            return jsonify({"erro": "Este cupom expirou"}), 400
        
        # Validar uso máximo total
        if uso_maximo is not None and uso_atual >= uso_maximo:
            cur.close()
            return jsonify({"erro": "Este cupom atingiu o limite máximo de usos"}), 400
        
        # Validar se o usuário já usou este cupom
        cur.execute("""
            SELECT COUNT(*) 
            FROM cupom_usado 
            WHERE cupom_id = %s AND usuario_id = %s
        """, (cupom_id, user_id))
        
        uso_por_usuario = cur.fetchone()[0]
        if uso_por_usuario >= (uso_maximo_por_usuario or 1):
            cur.close()
            return jsonify({"erro": "Você já utilizou este cupom o número máximo de vezes permitido"}), 400
        
        # Validar se o CPF já usou este cupom (uma vez por CPF)
        if user_cpf:
            # Limpar CPF (remover formatação)
            cpf_limpo = re.sub(r'[^0-9]', '', user_cpf)
            
            cur.execute("""
                SELECT COUNT(*) 
                FROM cupom_usado cu
                JOIN usuarios u ON cu.usuario_id = u.id
                WHERE cu.cupom_id = %s AND u.cpf = %s
            """, (cupom_id, cpf_limpo))
            
            uso_por_cpf = cur.fetchone()[0]
            if uso_por_cpf > 0:
                cur.close()
                return jsonify({"erro": "Este cupom já foi utilizado por este CPF"}), 400
        
        # Obter valor total do carrinho (se fornecido)
        valor_total_carrinho = float(data.get('valor_total_carrinho', 0))
        
        # Validar valor mínimo do pedido
        if valor_minimo and valor_total_carrinho < float(valor_minimo):
            cur.close()
            return jsonify({
                "erro": f"Valor mínimo do pedido para este cupom é R$ {valor_minimo:.2f}",
                "valor_minimo": float(valor_minimo)
            }), 400
        
        # Calcular desconto
        if tipo == 'p':  # Percentual
            desconto = valor_total_carrinho * (float(valor) / 100)
        else:  # Valor fixo
            desconto = float(valor)
        
        # Garantir que o desconto não seja maior que o valor total
        if desconto > valor_total_carrinho:
            desconto = valor_total_carrinho
        
        cur.close()
        
        return jsonify({
            "success": True,
            "cupom": {
                "id": cupom_id,
                "codigo": codigo,
                "tipo": tipo,
                "valor": float(valor),
                "valor_minimo": float(valor_minimo) if valor_minimo else None,
                "descricao": descricao,
                "desconto_calculado": round(desconto, 2)
            },
            "desconto": round(desconto, 2)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao validar cupom: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({"erro": "Erro interno do servidor"}), 500



