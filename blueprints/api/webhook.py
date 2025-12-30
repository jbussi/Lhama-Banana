"""
Webhook para receber notificações do PagBank sobre atualizações de pagamento
"""
from flask import Blueprint, request, jsonify, current_app
from ..services.order_service import get_order_by_venda_id, update_order_status, delete_order_token
from ..services import get_db
import psycopg2.extras
import json

webhook_api_bp = Blueprint('webhook_api', __name__, url_prefix='/api/webhook')


def map_pagbank_status_to_order_status(pagbank_status: str, payment_type: str) -> str:
    """
    Mapeia o status do PagBank para o status do pedido no sistema.
    
    Args:
        pagbank_status: Status retornado pelo PagBank
        payment_type: Tipo de pagamento (PIX, BOLETO, CREDIT_CARD)
        
    Returns:
        Status do pedido no formato do sistema
    """
    status_mapping = {
        'WAITING': 'PENDENTE',
        'PENDING': 'PENDENTE',
        'IN_ANALYSIS': 'PENDENTE',
        'PAID': 'PAGO',
        'AUTHORIZED': 'PAGO',
        'APPROVED': 'APROVADO',
        'DECLINED': 'CANCELADO',
        'CANCELLED': 'CANCELADO',
        'REFUNDED': 'CANCELADO',
        'CHARGEBACK': 'CANCELADO',
        'EXPIRED': 'EXPIRADO'
    }
    
    return status_mapping.get(pagbank_status.upper(), 'PENDENTE')


@webhook_api_bp.route('/pagbank', methods=['POST'])
def pagbank_webhook():
    """
    Webhook para receber notificações do PagBank sobre atualizações de pagamento.
    
    POST /api/webhook/pagbank
    
    O PagBank envia notificações quando há mudanças no status de um pagamento.
    """
    try:
        # Log da requisição recebida
        current_app.logger.info("Webhook PagBank recebido")
        current_app.logger.debug(f"Headers: {dict(request.headers)}")
        current_app.logger.debug(f"Body: {request.get_data(as_text=True)}")
        
        # Obter dados do webhook
        data = request.get_json()
        
        if not data:
            current_app.logger.warning("Webhook PagBank sem dados JSON")
            return jsonify({"erro": "Dados não fornecidos"}), 400
        
        # Extrair informações do webhook
        # A estrutura pode variar, então vamos tentar diferentes formatos
        charge_id = None
        reference_id = None
        status = None
        payment_method_type = None
        
        # Tentar extrair de diferentes estruturas possíveis
        if 'charges' in data and len(data['charges']) > 0:
            charge = data['charges'][0]
            charge_id = charge.get('id')
            reference_id = charge.get('reference_id')
            status = charge.get('status')
            payment_method = charge.get('payment_method', {})
            payment_method_type = payment_method.get('type', '').upper()
        elif 'charge' in data:
            charge = data['charge']
            charge_id = charge.get('id')
            reference_id = charge.get('reference_id')
            status = charge.get('status')
            payment_method = charge.get('payment_method', {})
            payment_method_type = payment_method.get('type', '').upper()
        else:
            # Tentar estrutura alternativa
            charge_id = data.get('id')
            reference_id = data.get('reference_id')
            status = data.get('status')
            payment_method = data.get('payment_method', {})
            if isinstance(payment_method, dict):
                payment_method_type = payment_method.get('type', '').upper()
            else:
                payment_method_type = str(payment_method).upper()
        
        if not charge_id or not status:
            current_app.logger.warning(f"Webhook PagBank com dados incompletos: {data}")
            return jsonify({"erro": "Dados incompletos"}), 400
        
        current_app.logger.info(f"Processando webhook: charge_id={charge_id}, status={status}, reference_id={reference_id}")
        
        # Buscar o pagamento no banco pelo transaction_id
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    p.id,
                    p.venda_id,
                    p.status_pagamento,
                    p.forma_pagamento_tipo,
                    v.codigo_pedido,
                    v.status_pedido
                FROM pagamentos p
                JOIN vendas v ON p.venda_id = v.id
                WHERE p.pagbank_transaction_id = %s
                   OR p.pagbank_order_id = %s
                ORDER BY p.criado_em DESC
                LIMIT 1
            """, (charge_id, charge_id))
            
            payment = cur.fetchone()
            
            if not payment:
                current_app.logger.warning(f"Pagamento não encontrado para charge_id: {charge_id}")
                # Retornar 200 para não fazer o PagBank reenviar
                return jsonify({"message": "Pagamento não encontrado"}), 200
            
            venda_id = payment['venda_id']
            current_status = payment['status_pagamento']
            
            # Atualizar status do pagamento
            cur.execute("""
                UPDATE pagamentos
                SET status_pagamento = %s,
                    atualizado_em = NOW(),
                    json_resposta_api = jsonb_set(
                        COALESCE(json_resposta_api, '{}'::jsonb),
                        '{webhook_updates}'::text[],
                        COALESCE(json_resposta_api->'webhook_updates', '[]'::jsonb) || 
                        jsonb_build_array(jsonb_build_object(
                            'timestamp', NOW()::text,
                            'status', %s,
                            'data', %s::jsonb
                        ))
                    )
                WHERE id = %s
            """, (status, status, json.dumps(data), payment['id']))
            
            conn.commit()
            
            # Buscar order relacionado
            order = get_order_by_venda_id(venda_id)
            
            if order:
                # Mapear status do PagBank para status do pedido
                new_order_status = map_pagbank_status_to_order_status(status, payment_method_type)
                
                # Atualizar status do pedido
                update_order_status(order['public_token'], new_order_status)
                
                # Se o pedido foi entregue, remover o token público
                if new_order_status == 'ENTREGUE':
                    delete_order_token(order['public_token'])
                    current_app.logger.info(f"Token público removido do pedido {order['id']} (entregue)")
                
                current_app.logger.info(f"Status do pedido {order['id']} atualizado para {new_order_status}")
            
            # Atualizar status da venda também
            venda_status_map = {
                'PAID': 'processando_envio',
                'AUTHORIZED': 'processando_envio',
                'APPROVED': 'processando_envio',
                'DECLINED': 'cancelado_pelo_vendedor',
                'CANCELLED': 'cancelado_pelo_vendedor',
                'REFUNDED': 'cancelado_pelo_vendedor',
                'EXPIRED': 'cancelado_pelo_vendedor'
            }
            
            new_venda_status = venda_status_map.get(status.upper())
            if new_venda_status:
                cur.execute("""
                    UPDATE vendas
                    SET status_pedido = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (new_venda_status, venda_id))
                conn.commit()
            
            current_app.logger.info(f"Webhook processado com sucesso: venda_id={venda_id}, status={status}")
            
            return jsonify({
                "success": True,
                "message": "Webhook processado com sucesso"
            }), 200
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao processar webhook: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            # Retornar 200 para não fazer o PagBank reenviar em caso de erro interno
            return jsonify({
                "erro": "Erro ao processar webhook",
                "message": str(e) if current_app.config.get('DEBUG', False) else "Erro interno"
            }), 200
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro no webhook PagBank: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        # Retornar 200 para não fazer o PagBank reenviar
        return jsonify({
            "erro": "Erro ao processar webhook",
            "message": str(e) if current_app.config.get('DEBUG', False) else "Erro interno"
        }), 200

