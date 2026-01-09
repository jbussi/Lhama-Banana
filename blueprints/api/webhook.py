"""
Webhook do PagBank - ÚNICA FONTE DE VERDADE DO STATUS DO PAGAMENTO
===================================================================

Este endpoint é a ÚNICA fonte de verdade para atualização do status de pagamento.

REGRAS ARQUITETURAIS:
- Toda mudança de estado do pagamento vem exclusivamente deste webhook
- O webhook é assíncrono, idempotente e confiável
- IDs do PagBank (charge_id, order_id) são usados para reconciliação
- Status finais possíveis: PAID, DECLINED, CANCELED, REFUNDED
- Este endpoint atualiza: tabela pagamentos, tabela vendas, tabela orders

IMPORTANTE:
- Nenhum outro código deve atualizar o status de pagamento
- A resposta do /orders no checkout NÃO confirma pagamento
- Frontend nunca valida pagamento, apenas faz polling do status
"""
from flask import Blueprint, request, jsonify, current_app
from ..services.order_service import get_order_by_venda_id, update_order_status, delete_order_token
from ..services import get_db
import psycopg2.extras
import json
import hmac

webhook_api_bp = Blueprint('webhook_api', __name__, url_prefix='/api/webhook')


def is_request_from_pagbank():
    """
    Verifica se a requisição veio do PagBank através do Authorization header.
    
    Verifica o token no header Authorization contra o token configurado.
    Usa comparação segura (hmac.compare_digest) para evitar timing attacks.
    
    Retorna:
        True se o Authorization token for válido, False caso contrário
    """
    # Verificar Authorization header
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        current_app.logger.warning("⚠️ Requisição sem Authorization header")
        return False
    
    # Obter token esperado
    # Opção A: Usar token específico para webhooks (recomendado)
    # Opção B: Usar o mesmo token da API como fallback
    webhook_token = current_app.config.get('PAGBANK_WEBHOOK_SECRET') or \
                   current_app.config.get('PAGBANK_API_TOKEN')
    
    if not webhook_token:
        current_app.logger.error("❌ PAGBANK_WEBHOOK_SECRET ou PAGBANK_API_TOKEN não configurado")
        return False
    
    # Extrair token do header (pode ser "Bearer <token>" ou apenas "<token>")
    if auth_header.startswith('Bearer '):
        received_token = auth_header[7:].strip()
    elif auth_header.startswith('Basic '):
        received_token = auth_header[6:].strip()
    else:
        received_token = auth_header.strip()
    
    # Comparação segura (evita timing attacks)
    if hmac.compare_digest(received_token, webhook_token):
        current_app.logger.info(f"✅ Validação por Authorization header: OK")
        return True
    else:
        current_app.logger.warning(f"⚠️ Authorization token não corresponde")
        return False


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


@webhook_api_bp.route('/pagbank', methods=['GET', 'POST'])
def pagbank_webhook():
    """
    Webhook para receber notificações do PagBank sobre atualizações de pagamento.
    
    GET /api/webhook/pagbank - Validação de acessibilidade (retorna 200 OK)
    POST /api/webhook/pagbank - Recebe notificações do PagBank
    
    O PagBank pode fazer uma requisição GET para validar se a URL está acessível.
    """
    # Se for GET, apenas retornar 200 OK para validação
    if request.method == 'GET':
        current_app.logger.info("Webhook PagBank - Validação de acessibilidade (GET)")
        return jsonify({
            "status": "ok",
            "message": "Webhook endpoint está acessível"
        }), 200
    
    # Validar origem da requisição através de headers
    if not is_request_from_pagbank():
        client_ip = request.remote_addr
        # Obter IP real mesmo atrás de proxy
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            client_ip = request.headers.get('X-Real-IP')
        
        current_app.logger.error("=" * 80)
        current_app.logger.error("🚨 ACESSO NEGADO AO WEBHOOK PAGBANK")
        current_app.logger.error("=" * 80)
        current_app.logger.error(f"IP de origem: {client_ip}")
        current_app.logger.error(f"User-Agent: {request.headers.get('User-Agent', 'N/A')}")
        current_app.logger.error(f"Todos os headers: {dict(request.headers)}")
        current_app.logger.error(f"Body (primeiros 500 chars): {request.get_data(as_text=True)[:500]}")
        current_app.logger.error("=" * 80)
        
        # Negar acesso em qualquer ambiente
        return jsonify({
            "erro": "Acesso negado",
            "message": "Requisição não autorizada"
        }), 403
    
    # Se for POST e passar validação, processar notificação
    try:
        # Log da requisição recebida
        current_app.logger.info("=" * 80)
        current_app.logger.info("🔔 WEBHOOK PAGBANK RECEBIDO (VALIDADO)")
        current_app.logger.info("=" * 80)
        current_app.logger.info(f"Headers: {dict(request.headers)}")
        current_app.logger.info(f"Body (primeiros 500 chars): {request.get_data(as_text=True)[:500]}")
        
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
        
        # Normalizar status para maiúsculas
        status = status.upper() if status else None
        
        current_app.logger.info(f"Processando webhook: charge_id={charge_id}, status={status}, reference_id={reference_id}")
        current_app.logger.info(f"Payload completo do webhook: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # Buscar o pagamento no banco pelo transaction_id
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Verificar e criar colunas necessárias se não existirem
            columns_to_check = ['criado_em', 'atualizado_em', 'pago_em']
            
            for column_name in columns_to_check:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'pagamentos' 
                    AND column_name = %s
                """, (column_name,))
                has_column = cur.fetchone() is not None
                
                if not has_column:
                    current_app.logger.info(f"Coluna {column_name} não existe na tabela pagamentos. Criando...")
                    try:
                        if column_name == 'pago_em':
                            # pago_em não tem DEFAULT, pode ser NULL
                            cur.execute("ALTER TABLE pagamentos ADD COLUMN pago_em TIMESTAMP")
                        else:
                            # criado_em e atualizado_em têm DEFAULT NOW()
                            cur.execute(f"ALTER TABLE pagamentos ADD COLUMN {column_name} TIMESTAMP DEFAULT NOW()")
                        conn.commit()
                        current_app.logger.info(f"Coluna {column_name} criada com sucesso")
                    except Exception as alter_error:
                        conn.rollback()
                        current_app.logger.warning(f"Erro ao criar coluna {column_name} (pode já existir): {alter_error}")
                        # Continuar mesmo com erro - pode ser que a coluna já exista
            
            # Buscar pagamento pelo charge_id (prioritário), order_id ou transaction_id
            # O webhook do PagBank envia o charge_id, que é o mais específico
            # Verificar novamente se criado_em existe após possível criação
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pagamentos' 
                AND column_name = 'criado_em'
            """)
            has_criado_em_after = cur.fetchone() is not None
            
            # Verificar se pago_em existe
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pagamentos' 
                AND column_name = 'pago_em'
            """)
            has_pago_em = cur.fetchone() is not None
            
            # Construir ORDER BY dinamicamente baseado na existência da coluna
            if has_criado_em_after:
                order_by_clause = "p.criado_em DESC NULLS LAST, p.id DESC"
            else:
                order_by_clause = "p.id DESC"
            
            cur.execute(f"""
                SELECT 
                    p.id,
                    p.venda_id,
                    p.status_pagamento,
                    p.forma_pagamento_tipo,
                    v.codigo_pedido,
                    v.status_pedido
                FROM pagamentos p
                JOIN vendas v ON p.venda_id = v.id
                WHERE p.pagbank_charge_id = %s
                   OR p.pagbank_order_id = %s
                   OR p.pagbank_transaction_id = %s
                ORDER BY 
                    CASE 
                        WHEN p.pagbank_charge_id = %s THEN 1  -- Prioridade para charge_id
                        WHEN p.pagbank_order_id = %s THEN 2
                        ELSE 3
                    END,
                    {order_by_clause}
                LIMIT 1
            """, (charge_id, charge_id, charge_id, charge_id, charge_id))
            
            payment = cur.fetchone()
            
            if not payment:
                # Tentar buscar também pelo order_id se charge_id não funcionou
                current_app.logger.warning(f"Pagamento não encontrado para charge_id: {charge_id}. Tentando buscar por order_id...")
                
                # Se o webhook veio com order_id, tentar buscar por ele
                order_id_from_webhook = data.get('id') or (data.get('charges', [{}])[0].get('id') if data.get('charges') else None)
                if order_id_from_webhook:
                    # Usar mesma lógica de ordenação baseada na existência da coluna
                    if has_criado_em_after:
                        order_by_clause_alt = "p.criado_em DESC NULLS LAST, p.id DESC"
                    else:
                        order_by_clause_alt = "p.id DESC"
                    
                    cur.execute(f"""
                        SELECT 
                            p.id,
                            p.venda_id,
                            p.status_pagamento,
                            p.forma_pagamento_tipo,
                            v.codigo_pedido,
                            v.status_pedido
                        FROM pagamentos p
                        JOIN vendas v ON p.venda_id = v.id
                        WHERE p.pagbank_order_id = %s
                           OR p.pagbank_transaction_id = %s
                        ORDER BY {order_by_clause_alt}
                        LIMIT 1
                    """, (order_id_from_webhook, order_id_from_webhook))
                    payment = cur.fetchone()
                
                if not payment:
                    current_app.logger.error(f"Pagamento não encontrado para charge_id: {charge_id}, order_id: {order_id_from_webhook}")
                    current_app.logger.error(f"Tentando buscar todos os pagamentos recentes para debug...")
                    # Usar mesma lógica de ordenação
                    if has_criado_em_after:
                        debug_order_by = "criado_em DESC NULLS LAST, id DESC"
                    else:
                        debug_order_by = "id DESC"
                    
                    cur.execute(f"""
                        SELECT id, pagbank_charge_id, pagbank_order_id, pagbank_transaction_id, status_pagamento, 
                               CASE WHEN EXISTS (
                                   SELECT 1 FROM information_schema.columns 
                                   WHERE table_name = 'pagamentos' AND column_name = 'criado_em'
                               ) THEN criado_em ELSE NULL END as criado_em
                        FROM pagamentos
                        ORDER BY {debug_order_by}
                        LIMIT 5
                    """)
                    recent_payments = cur.fetchall()
                    for p in recent_payments:
                        current_app.logger.error(f"  - Pagamento ID {p[0]}: charge_id={p[1]}, order_id={p[2]}, transaction_id={p[3]}, status={p[4]}, criado_em={p[5]}")
                    
                    # Retornar 200 para não fazer o PagBank reenviar
                    return jsonify({"message": "Pagamento não encontrado"}), 200
                else:
                    current_app.logger.info(f"Pagamento encontrado pelo order_id: {order_id_from_webhook}")
            
            venda_id = payment['venda_id']
            current_status = payment['status_pagamento']
            
            # Normalizar status para maiúsculas (PagBank pode enviar em diferentes formatos)
            status_upper = status.upper()
            
            current_app.logger.info(f"Atualizando pagamento {payment['id']}: {current_status} -> {status_upper}")
            
            # Verificar se deve atualizar pago_em (se a coluna existir e o pagamento foi pago)
            should_update_pago_em = (has_pago_em and 
                                    status_upper in ['PAID', 'AUTHORIZED', 'APPROVED'] and 
                                    current_status not in ['PAID', 'AUTHORIZED', 'APPROVED'])
            
            if should_update_pago_em:
                current_app.logger.info(f"Pagamento {payment['id']} foi pago! Atualizando pago_em")
            
            # Construir query de UPDATE dinamicamente baseado nas colunas existentes
            update_fields = ["status_pagamento = %s"]
            update_params = [status_upper]
            
            # Adicionar atualizado_em se existir
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pagamentos' 
                AND column_name = 'atualizado_em'
            """)
            if cur.fetchone():
                update_fields.append("atualizado_em = NOW()")
            
            # Adicionar pago_em se existir e se o pagamento foi pago
            if should_update_pago_em:
                update_fields.append("pago_em = NOW()")
            
            # Adicionar json_resposta_api
            update_fields.append("""
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
            """)
            update_params.extend([status_upper, json.dumps(data), payment['id']])
            
            # Executar UPDATE
            update_query = f"""
                UPDATE pagamentos
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            cur.execute(update_query, tuple(update_params))
            
            conn.commit()
            current_app.logger.info(f"Status do pagamento {payment['id']} atualizado com sucesso para {status_upper}")
            
            # Buscar order relacionado
            order = get_order_by_venda_id(venda_id)
            new_order_status = None
            
            if order:
                # Mapear status do PagBank para status do pedido
                old_order_status = order.get('status', 'UNKNOWN')
                new_order_status = map_pagbank_status_to_order_status(status, payment_method_type)
                
                current_app.logger.info(f"Atualizando order {order['id']} (token: {order['public_token']}): {old_order_status} -> {new_order_status}")
                
                # Atualizar status do pedido
                updated = update_order_status(order['public_token'], new_order_status)
                
                if updated:
                    current_app.logger.info(f"✅ Status do pedido {order['id']} atualizado com sucesso para {new_order_status}")
                else:
                    current_app.logger.error(f"❌ Falha ao atualizar status do pedido {order['id']}")
                
                # Se o pedido foi entregue, remover o token público
                if new_order_status == 'ENTREGUE':
                    delete_order_token(order['public_token'])
                    current_app.logger.info(f"Token público removido do pedido {order['id']} (entregue)")
            else:
                current_app.logger.warning(f"Order não encontrado para venda_id: {venda_id}")
            
            # Criar pedido no Bling quando pagamento for confirmado
            if status_upper in ['PAID', 'AUTHORIZED', 'APPROVED']:
                try:
                    from ..services.bling_order_service import sync_order_to_bling
                    current_app.logger.info(f"💰 Pagamento confirmado. Criando pedido no Bling para venda {venda_id}...")
                    
                    result = sync_order_to_bling(venda_id)
                    
                    if result.get('success'):
                        current_app.logger.info(f"✅ Pedido criado no Bling: {result.get('bling_pedido_id')}")
                    else:
                        current_app.logger.warning(
                            f"⚠️ Falha ao criar pedido no Bling: {result.get('error')}. "
                            f"Pedido pode ser sincronizado manualmente depois."
                        )
                except Exception as bling_error:
                    # Não falhar o webhook por erro no Bling
                    current_app.logger.error(
                        f"❌ Erro ao criar pedido no Bling: {bling_error}. "
                        f"Webhook continuará processando normalmente."
                    )
            
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
                
                # Se status mudou para processando_envio, verificar se precisa emitir NFe e criar etiqueta
                if new_venda_status == 'processando_envio':
                    # 1. Sincronizar estoque com Bling (estoque já foi decrementado na criação do pedido)
                    try:
                        from ..services.bling_stock_service import update_stock_after_sale
                        stock_result = update_stock_after_sale(venda_id, sync_to_bling=True)
                        if stock_result.get('success'):
                            current_app.logger.info(f"✅ Estoque sincronizado com Bling após confirmação de pagamento (venda {venda_id})")
                        else:
                            current_app.logger.warning(f"⚠️ Falha ao sincronizar estoque com Bling (venda {venda_id}): {stock_result.get('error')}")
                    except Exception as stock_error:
                        current_app.logger.error(f"❌ Erro ao sincronizar estoque com Bling (venda {venda_id}): {stock_error}")
                        import traceback
                        current_app.logger.error(traceback.format_exc())
                        # Não falhar o webhook por erro na sincronização de estoque
                    
                    # 2. Criar etiqueta automaticamente
                    try:
                        from ..api.labels import create_label_automatically
                        etiqueta_id = create_label_automatically(venda_id)
                        if etiqueta_id:
                            current_app.logger.info(f"✅ Etiqueta {etiqueta_id} criada automaticamente para venda {venda_id}")
                        else:
                            current_app.logger.warning(f"⚠️ Etiqueta não criada para venda {venda_id} (pode já existir ou erro na criação)")
                    except Exception as label_error:
                        current_app.logger.error(f"❌ Erro ao criar etiqueta automaticamente para venda {venda_id}: {label_error}")
                        import traceback
                        current_app.logger.error(traceback.format_exc())
                        # Não falhar o webhook por erro na criação da etiqueta
                    
                    # 3. Criar conta a receber no Bling
                    try:
                        from ..services.bling_financial_service import sync_payment_to_financial
                        financial_result = sync_payment_to_financial(venda_id)
                        if financial_result.get('success'):
                            current_app.logger.info(f"✅ Conta(s) a receber criada(s) no Bling para venda {venda_id}")
                        else:
                            current_app.logger.warning(f"⚠️ Falha ao criar conta a receber no Bling (venda {venda_id}): {financial_result.get('error')}")
                    except Exception as financial_error:
                        current_app.logger.error(f"❌ Erro ao criar conta a receber no Bling (venda {venda_id}): {financial_error}")
                        import traceback
                        current_app.logger.error(traceback.format_exc())
                        # Não falhar o webhook por erro na criação de conta a receber
                    
                    # 4. Verificar se precisa emitir NFe
                    try:
                        from ..services.nfe_service import check_and_emit_nfe
                        nfe_result = check_and_emit_nfe(venda_id)
                        if nfe_result:
                            current_app.logger.info(f"✅ NFe registrada para venda {venda_id}: {nfe_result}")
                    except Exception as nfe_error:
                        current_app.logger.error(f"❌ Erro ao processar NFe para venda {venda_id}: {nfe_error}")
                        # Não falhar o webhook por erro na NFe
            
            current_app.logger.info("=" * 80)
            current_app.logger.info(f"✅ WEBHOOK PROCESSADO COM SUCESSO")
            current_app.logger.info(f"   Venda ID: {venda_id}")
            current_app.logger.info(f"   Status PagBank: {status}")
            current_app.logger.info(f"   Status Pagamento: {status_upper}")
            current_app.logger.info(f"   Status Order: {new_order_status if order else 'N/A'}")
            current_app.logger.info("=" * 80)
            
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

