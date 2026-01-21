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
import requests

webhook_api_bp = Blueprint('webhook_api', __name__, url_prefix='/api/webhook')


def is_request_from_pagbank():
    """
    Verifica se a requisição veio do PagBank através de múltiplos métodos.
    
    Métodos de validação (em ordem de prioridade):
    1. Authorization header (se configurado)
    2. Headers customizados do PagBank (X-Product-Origin, X-Product-Id)
    3. IPs conhecidos da AWS (onde PagBank hospeda seus serviços)
    4. Desabilitar validação em desenvolvimento (se configurado)
    
    Retorna:
        True se a requisição for válida, False caso contrário
    """
    # Opção 1: Verificar Authorization header (se configurado)
    auth_header = request.headers.get('Authorization', '')
    webhook_token = current_app.config.get('PAGBANK_WEBHOOK_SECRET') or \
                   current_app.config.get('PAGBANK_API_TOKEN')
    
    if auth_header and webhook_token:
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
    
    # Opção 2: Verificar headers customizados do PagBank
    # O PagBank envia X-Product-Origin: ORDER e X-Product-Id
    x_product_origin = request.headers.get('X-Product-Origin', '')
    x_product_id = request.headers.get('X-Product-Id', '')
    
    if x_product_origin == 'ORDER' and x_product_id:
        current_app.logger.info(f"✅ Validação por headers PagBank: X-Product-Origin=ORDER, X-Product-Id={x_product_id[:20]}...")
        return True
    
    # Opção 3: Verificar IPs conhecidos da AWS (onde PagBank hospeda)
    # IPs observados: 3.215.116.19, 3.209.2.41 (parecem ser AWS)
    client_ip = request.remote_addr
    if request.headers.get('X-Forwarded-For'):
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    
    # Verificar se o IP começa com 3.x.x.x (AWS IP range comum)
    # Nota: Isso é uma validação básica. Em produção, use uma whitelist específica
    if client_ip and client_ip.startswith('3.'):
        # Verificar também se tem User-Agent Go-http-client (usado pelo PagBank)
        user_agent = request.headers.get('User-Agent', '')
        if 'Go-http-client' in user_agent:
            current_app.logger.info(f"✅ Validação por IP AWS e User-Agent: IP={client_ip}, UA={user_agent}")
            return True
    
    # Opção 4: Desabilitar validação em desenvolvimento (apenas se explicitamente configurado)
    disable_validation = current_app.config.get('PAGBANK_WEBHOOK_DISABLE_VALIDATION', False)
    if disable_validation and current_app.config.get('ENV') == 'development':
        current_app.logger.warning("⚠️ Validação de webhook DESABILITADA em desenvolvimento")
        return True
    
    # Se nenhuma validação passou
    current_app.logger.warning("⚠️ Requisição não passou em nenhuma validação")
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
        
        # Obter dados do webhook - aceitar tanto JSON quanto form data
        content_type = request.headers.get('Content-Type', '')
        data = None
        
        if 'application/json' in content_type:
            # Formato JSON (novo formato do PagBank)
            data = request.get_json()
        elif 'application/x-www-form-urlencoded' in content_type:
            # Formato form data (formato antigo do PagSeguro/PagBank)
            form_data = request.form
            notification_code = form_data.get('notificationCode')
            notification_type = form_data.get('notificationType')
            
            current_app.logger.info(f"Webhook recebido em formato form data: notificationCode={notification_code}, notificationType={notification_type}")
            
            # Se temos notificationCode, precisamos buscar os dados da transação na API do PagBank
            if notification_code:
                try:
                    # Buscar transação usando o notificationCode na API do PagBank
                    api_token = current_app.config.get('PAGBANK_API_TOKEN')
                    if not api_token:
                        current_app.logger.error("PAGBANK_API_TOKEN não configurado para buscar transação")
                        return jsonify({"erro": "Configuração incompleta"}), 500
                    
                    # Determinar URL da API baseado no ambiente
                    env = current_app.config.get('PAGBANK_ENVIRONMENT', 'sandbox')
                    if env == 'production':
                        base_url = current_app.config.get('PAGBANK_PRODUCTION_API_URL', 'https://api.pagseguro.com/orders')
                    else:
                        base_url = current_app.config.get('PAGBANK_SANDBOX_API_URL', 'https://sandbox.api.pagseguro.com/orders')
                    
                    # O notificationCode pode ser um order_id ou charge_id
                    # Vamos tentar buscar como order_id primeiro
                    order_url = f"{base_url}/{notification_code}"
                    
                    headers = {
                        'Authorization': f'Bearer {api_token}',
                        'Accept': 'application/json'
                    }
                    
                    current_app.logger.info(f"Buscando transação na API: {order_url}")
                    response = requests.get(order_url, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        current_app.logger.info(f"Transação encontrada na API: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                        # Continuar processamento com os dados obtidos - não retornar aqui!
                    elif response.status_code == 404:
                        current_app.logger.warning(f"Transação não encontrada na API (404). Tentando buscar no banco pelo notificationCode...")
                        # Tentar buscar no banco pelo notificationCode como order_id ou charge_id
                        conn_temp = get_db()
                        cur_temp = conn_temp.cursor(cursor_factory=psycopg2.extras.DictCursor)
                        try:
                            cur_temp.execute("""
                                SELECT p.id, p.venda_id, p.status_pagamento, p.pagbank_order_id, p.pagbank_charge_id
                                FROM pagamentos p
                                WHERE p.pagbank_order_id = %s OR p.pagbank_charge_id = %s
                                LIMIT 1
                            """, (notification_code, notification_code))
                            payment = cur_temp.fetchone()
                            if payment:
                                current_app.logger.info(f"Pagamento encontrado no banco pelo notificationCode: {payment['id']}")
                                # Se encontrou no banco, aceitar a notificação mas não processar agora
                                # O PagBank pode enviar os dados completos em outra requisição
                                return jsonify({
                                    "status": "ok",
                                    "message": "Notificação recebida, pagamento encontrado no banco"
                                }), 200
                            else:
                                current_app.logger.warning(f"Pagamento não encontrado nem na API nem no banco para notificationCode: {notification_code}")
                                return jsonify({
                                    "status": "ok",
                                    "message": "Notificação recebida, mas pagamento não encontrado"
                                }), 200
                        finally:
                            cur_temp.close()
                    else:
                        current_app.logger.error(f"Erro ao buscar transação na API: {response.status_code} - {response.text[:200]}")
                        # Aceitar a notificação para não bloquear o PagBank, mas logar o erro
                        return jsonify({
                            "status": "ok",
                            "message": "Notificação recebida, mas erro ao buscar transação"
                        }), 200
                except Exception as e:
                    current_app.logger.error(f"Erro ao processar notificationCode: {e}")
                    import traceback
                    current_app.logger.error(f"Traceback: {traceback.format_exc()}")
                    # Aceitar a notificação mesmo com erro para não bloquear o PagBank
                    return jsonify({
                        "status": "ok",
                        "message": "Notificação recebida"
                    }), 200
            else:
                current_app.logger.warning("Webhook form data sem notificationCode")
                return jsonify({"erro": "Dados incompletos"}), 400
        
        if not data:
            current_app.logger.warning("Webhook PagBank sem dados válidos")
            return jsonify({"erro": "Dados não fornecidos"}), 400
        
        # Extrair informações do webhook
        # A estrutura pode variar, então vamos tentar diferentes formatos
        charge_id = None
        order_id = None
        reference_id = None
        status = None
        payment_method_type = None
        
        current_app.logger.info(f"Estrutura dos dados recebidos: {list(data.keys()) if isinstance(data, dict) else 'Não é dict'}")
        
        # Tentar extrair de diferentes estruturas possíveis
        if 'charges' in data and len(data['charges']) > 0:
            # Estrutura com array de charges (resposta da API ao buscar order)
            charge = data['charges'][0]
            charge_id = charge.get('id')
            reference_id = charge.get('reference_id')
            status = charge.get('status')
            payment_method = charge.get('payment_method', {})
            payment_method_type = payment_method.get('type', '').upper()
            current_app.logger.info(f"Extraído de charges[0]: charge_id={charge_id}, status={status}, type={payment_method_type}")
        elif 'charge' in data:
            # Estrutura com objeto charge único
            charge = data['charge']
            charge_id = charge.get('id')
            reference_id = charge.get('reference_id')
            status = charge.get('status')
            payment_method = charge.get('payment_method', {})
            payment_method_type = payment_method.get('type', '').upper()
            current_app.logger.info(f"Extraído de charge: charge_id={charge_id}, status={status}, type={payment_method_type}")
        else:
            # Tentar estrutura alternativa (pode ser que venha direto no nível raiz)
            charge_id = data.get('id')
            order_id = data.get('id')  # Pode ser order_id também
            reference_id = data.get('reference_id')
            status = data.get('status')
            payment_method = data.get('payment_method', {})
            if isinstance(payment_method, dict):
                payment_method_type = payment_method.get('type', '').upper()
            else:
                payment_method_type = str(payment_method).upper()
            current_app.logger.info(f"Extraído do nível raiz: id={charge_id}, status={status}, type={payment_method_type}")
        
        # Se não encontrou charge_id mas tem order_id, tentar buscar charges dentro do order
        if not charge_id and order_id and 'charges' not in data:
            # Pode ser que a resposta tenha uma estrutura diferente
            if isinstance(data, dict):
                # Procurar por qualquer campo que possa conter o charge_id
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict) and 'id' in value[0]:
                            charge_id = value[0].get('id')
                            status = value[0].get('status')
                            current_app.logger.info(f"Encontrado charge_id em {key}: {charge_id}")
                            break
        
        # Se ainda não tem charge_id mas tem order_id, usar order_id para buscar
        if not charge_id and order_id:
            current_app.logger.info(f"Não encontrou charge_id, mas tem order_id: {order_id}. Usando order_id para buscar pagamento.")
            charge_id = order_id  # Usar order_id como fallback
        
        if not charge_id:
            current_app.logger.error(f"Webhook PagBank sem charge_id ou order_id. Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)[:1000]}")
            return jsonify({"erro": "Dados incompletos: falta charge_id ou order_id"}), 400
        
        if not status:
            current_app.logger.warning(f"Webhook PagBank sem status. Dados: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
            # Tentar buscar status no banco se não tiver nos dados
            # Por enquanto, vamos assumir que precisa buscar na API novamente
            return jsonify({"erro": "Dados incompletos: falta status"}), 400
        
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
            
            # Buscar pagamento usando charge_id, order_id ou transaction_id
            # O charge_id pode ser o ID da cobrança ou o order_id dependendo do formato da notificação
            cur.execute(f"""
                SELECT 
                    p.id,
                    p.venda_id,
                    p.status_pagamento,
                    p.forma_pagamento_tipo,
                    p.pagbank_charge_id,
                    p.pagbank_order_id,
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
            
            current_app.logger.info(f"Buscando pagamento com charge_id/order_id: {charge_id}")
            
            payment = cur.fetchone()
            
            if payment:
                current_app.logger.info(f"✅ Pagamento encontrado: id={payment['id']}, venda_id={payment['venda_id']}, status_atual={payment['status_pagamento']}, tipo={payment['forma_pagamento_tipo']}")
            else:
                # Tentar buscar também pelo order_id se charge_id não funcionou
                current_app.logger.warning(f"⚠️ Pagamento não encontrado para charge_id/order_id: {charge_id}. Tentando buscar por order_id...")
                
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
                
                # Se status mudou para processando_envio, sincronizar estoque com Bling
                # REMOVIDO: Criação automática de etiqueta - será criada apenas após aprovação do SEFAZ
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
                    
                    # 2. Criar conta a receber no Bling - REMOVIDO (não essencial para o escopo atual)
                    # A criação de contas a receber será gerenciada diretamente pelo Bling quando necessário
                    
                    # 3. Verificar se precisa emitir NFe
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


def process_order_webhook(webhook_data: dict, event: str, event_id: str, data: dict):
    """
    Processa webhook de pedido do Bling
    
    Args:
        webhook_data: Dados completos do webhook
        event: Tipo do evento (ex: "order.updated")
        event_id: ID do evento
        data: Dados do pedido do webhook
    
    Returns:
        Response Flask
    """
    try:
        # Determinar ação (created, updated, deleted)
        action = event.split('.')[-1] if '.' in event else 'unknown'
        
        current_app.logger.info(f"Processando evento de pedido: {action}")
        current_app.logger.info(f"Dados do pedido: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        # Extrair informações do pedido do webhook
        bling_pedido_id = data.get('id')
        
        if not bling_pedido_id:
            current_app.logger.warning(f"Webhook Bling sem ID do pedido. Event: {event}")
            return jsonify({
                "status": "ok",
                "message": "Webhook sem ID do pedido, ignorado"
            }), 200
        
        # Processar evento de pedido
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Buscar pedido local pelo bling_pedido_id
            cur.execute("""
                SELECT v.id as venda_id, v.status_pedido as status_atual, 
                       v.bling_situacao_id as situacao_atual_id,
                       bp.bling_pedido_id
                FROM vendas v
                JOIN bling_pedidos bp ON v.id = bp.venda_id
                WHERE bp.bling_pedido_id = %s
            """, (bling_pedido_id,))
            
            pedido_local = cur.fetchone()
            
            if not pedido_local:
                current_app.logger.warning(f"Pedido não encontrado no banco local para bling_pedido_id: {bling_pedido_id}")
                return jsonify({
                    "status": "ok",
                    "message": f"Pedido bling_pedido_id {bling_pedido_id} não encontrado localmente"
                }), 200
            
            venda_id = pedido_local['venda_id']
            status_atual = pedido_local['status_atual']
            situacao_atual_id = pedido_local['situacao_atual_id']
            
            # Para eventos deleted, apenas logar
            if action == 'deleted':
                current_app.logger.info(f"Evento de pedido deletado para venda {venda_id} (bling_pedido_id: {bling_pedido_id})")
                return jsonify({
                    "status": "ok",
                    "message": f"Evento deleted recebido para pedido {venda_id}"
                }), 200
            
            # Extrair ID da situação do Bling (pode vir em diferentes formatos)
            situacao_bling_id = None
            situacao_bling_nome = None
            
            # Tentar extrair situação do webhook
            if 'situacao' in data:
                situacao_data = data['situacao']
                if isinstance(situacao_data, dict):
                    situacao_bling_id = situacao_data.get('id')
                    situacao_bling_nome = situacao_data.get('nome')
                elif isinstance(situacao_data, (int, str)):
                    # Se for apenas um ID
                    try:
                        situacao_bling_id = int(situacao_data)
                    except (ValueError, TypeError):
                        pass
            
            # Se não encontrou situação no webhook, buscar do pedido via API
            if not situacao_bling_id:
                try:
                    from ..services.bling_order_service import get_bling_order_by_local_id
                    pedido_bling_full = get_bling_order_by_local_id(venda_id)
                    if pedido_bling_full and 'situacao' in pedido_bling_full:
                        situacao_data = pedido_bling_full['situacao']
                        if isinstance(situacao_data, dict):
                            situacao_bling_id = situacao_data.get('id')
                            situacao_bling_nome = situacao_data.get('nome')
                except Exception as e:
                    current_app.logger.warning(f"Erro ao buscar situação do pedido via API: {e}")
            
            # Se ainda não tem situação, usar situação antiga ou ignorar
            if not situacao_bling_id:
                if situacao_atual_id:
                    current_app.logger.info(
                        f"Nenhuma situação nova no webhook para pedido {venda_id}, "
                        f"mantendo situação atual: {situacao_atual_id}"
                    )
                    return jsonify({
                        "status": "ok",
                        "message": f"Webhook sem situação nova, mantendo situação atual"
                    }), 200
                else:
                    current_app.logger.warning(
                        f"Nenhuma situação encontrada no webhook para pedido {venda_id}"
                    )
                    return jsonify({
                        "status": "ok",
                        "message": "Webhook sem informação de situação"
                    }), 200
            
            # Verificar se a situação mudou
            if situacao_bling_id == situacao_atual_id:
                current_app.logger.info(
                    f"Situação não mudou para pedido {venda_id}: {situacao_bling_id}"
                )
                return jsonify({
                    "status": "ok",
                    "message": "Situação não mudou"
                }), 200
            
            # Buscar nome da situação se não fornecido
            if not situacao_bling_nome:
                current_app.logger.info(f"🔍 [WEBHOOK] Nome da situação não fornecido no webhook, buscando no banco...")
                try:
                    from ..services.bling_situacao_service import get_situacao_mapping
                    situacao_info = get_situacao_mapping(situacao_bling_id)
                    if situacao_info:
                        situacao_bling_nome = situacao_info.get('nome')
                        current_app.logger.info(f"✅ [WEBHOOK] Nome encontrado: '{situacao_bling_nome}'")
                    else:
                        current_app.logger.warning(f"⚠️ [WEBHOOK] Situação ID {situacao_bling_id} não encontrada no banco")
                except Exception as e:
                    current_app.logger.error(f"❌ [WEBHOOK] Erro ao buscar nome da situação: {e}")
            else:
                current_app.logger.info(f"📋 [WEBHOOK] Nome da situação fornecido no webhook: '{situacao_bling_nome}'")
            
            # Atualizar situação e status do pedido usando o serviço de situação
            from ..services.bling_situacao_service import update_pedido_situacao
            
            atualizado = update_pedido_situacao(
                venda_id=venda_id,
                bling_situacao_id=situacao_bling_id,
                bling_situacao_nome=situacao_bling_nome
            )
            
            if atualizado:
                # Buscar novo status para log
                cur.execute("""
                    SELECT status_pedido, bling_situacao_id, bling_situacao_nome
                    FROM vendas
                    WHERE id = %s
                """, (venda_id,))
                
                pedido_atualizado = cur.fetchone()
                novo_status = pedido_atualizado['status_pedido'] if pedido_atualizado else None
                
                current_app.logger.info("=" * 80)
                current_app.logger.info(f"✅ STATUS DO PEDIDO ATUALIZADO VIA WEBHOOK BLING")
                current_app.logger.info(f"   Venda ID: {venda_id}")
                current_app.logger.info(f"   Situação Bling: {situacao_atual_id} → {situacao_bling_id}")
                current_app.logger.info(f"   Nome Situação: {situacao_bling_nome}")
                current_app.logger.info(f"   Status Site: {status_atual} → {novo_status}")
                current_app.logger.info("=" * 80)
                
                # Verificar se mudou para "Em andamento" e emitir NF-e
                situacao_nome_lower = (situacao_bling_nome or '').lower()
                is_em_andamento = 'em andamento' in situacao_nome_lower
                
                # Também verificar pelo ID se conhecido (pode ser mapeado depois)
                # Por enquanto, usar apenas o nome
                if is_em_andamento:
                    current_app.logger.info(f"🚀 Pedido {venda_id} mudou para 'Em andamento'. Emitindo NF-e...")
                    
                    try:
                        from ..services.bling_nfe_service import emit_nfe
                        
                        # Verificar se NF-e já foi emitida
                        cur.execute("""
                            SELECT bling_nfe_id, nfe_status
                            FROM bling_pedidos
                            WHERE venda_id = %s
                        """, (venda_id,))
                        
                        nfe_info = cur.fetchone()
                        
                        if nfe_info and nfe_info.get('bling_nfe_id'):
                            current_app.logger.info(
                                f"ℹ️ NF-e já existe para pedido {venda_id}. "
                                f"ID: {nfe_info.get('bling_nfe_id')}, Status: {nfe_info.get('nfe_status')}"
                            )
                        else:
                            # Emitir NF-e
                            nfe_result = emit_nfe(venda_id)
                            
                            if nfe_result.get('success'):
                                current_app.logger.info(
                                    f"✅ NF-e emitida com sucesso para pedido {venda_id}. "
                                    f"Número: {nfe_result.get('nfe_numero')}, "
                                    f"Chave: {nfe_result.get('nfe_chave_acesso')}"
                                )
                                
                                # Atualizar status do pedido para aguardando aprovação SEFAZ
                                cur.execute("""
                                    UPDATE vendas
                                    SET status_pedido = 'nfe_aguardando_aprovacao',
                                        atualizado_em = NOW()
                                    WHERE id = %s
                                """, (venda_id,))
                                conn.commit()
                                
                                current_app.logger.info(
                                    f"📋 Status do pedido {venda_id} atualizado para 'nfe_aguardando_aprovacao'"
                                )
                            else:
                                current_app.logger.error(
                                    f"❌ Erro ao emitir NF-e para pedido {venda_id}: {nfe_result.get('error')}"
                                )
                                
                                # Atualizar status para erro
                                cur.execute("""
                                    UPDATE vendas
                                    SET status_pedido = 'erro_nfe_timeout',
                                        atualizado_em = NOW()
                                    WHERE id = %s
                                """, (venda_id,))
                                conn.commit()
                                
                    except Exception as e:
                        current_app.logger.error(
                            f"❌ Erro ao processar emissão de NF-e para pedido {venda_id}: {e}",
                            exc_info=True
                        )
            else:
                current_app.logger.warning(f"Falha ao atualizar situação do pedido {venda_id}")
            
            # Atualizar informações da NF-e se houver
            nfe_data = data.get('notaFiscal') or data.get('nota_fiscal')
            if nfe_data:
                nfe_id = nfe_data.get('id')
                nfe_numero = nfe_data.get('numero')
                nfe_chave_acesso = nfe_data.get('chaveAcesso') or nfe_data.get('chave_acesso')
                nfe_situacao = nfe_data.get('situacao', '')
                
                cur.execute("""
                    UPDATE bling_pedidos
                    SET bling_nfe_id = %s,
                        nfe_numero = %s,
                        nfe_chave_acesso = %s,
                        nfe_status = %s,
                        updated_at = NOW()
                    WHERE venda_id = %s
                """, (nfe_id, nfe_numero, nfe_chave_acesso, nfe_situacao, venda_id))
                
                conn.commit()
                
                current_app.logger.info(f"✅ Informações da NF-e atualizadas para pedido {venda_id}")
            
            return jsonify({
                "status": "ok",
                "message": f"Pedido {venda_id} atualizado com sucesso"
            }), 200
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao processar webhook de pedido: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                "status": "ok",
                "message": "Erro ao processar webhook, mas retornando 200 para idempotência"
            }), 200
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro no webhook Bling: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "status": "ok",
            "message": "Erro ao processar webhook"
        }), 200


def process_nfe_webhook(webhook_data: dict, event: str, event_id: str, data: dict):
    """
    Processa webhook de nota fiscal do Bling
    
    Eventos suportados:
    - consumer_invoice.created: NF-e criada
    - consumer_invoice.updated: NF-e atualizada (situação mudou)
    - consumer_invoice.deleted: NF-e deletada
    
    Quando situação = 1 (Autorizada), atualiza pedido e muda para Logística no Bling.
    
    Args:
        webhook_data: Dados completos do webhook
        event: Tipo do evento (ex: "consumer_invoice.updated")
        event_id: ID do evento
        data: Dados da nota fiscal do webhook
    
    Returns:
        Response Flask
    """
    try:
        # Determinar ação (created, updated, deleted)
        action = event.split('.')[-1] if '.' in event else 'unknown'
        
        current_app.logger.info("=" * 80)
        current_app.logger.info(f"📄 WEBHOOK NOTA FISCAL BLING - {action.upper()}")
        current_app.logger.info("=" * 80)
        current_app.logger.info(f"Event: {event}")
        current_app.logger.info(f"Event ID: {event_id}")
        current_app.logger.info(f"Dados: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        # Extrair informações da nota fiscal
        nfe_id = data.get('id')
        nfe_situacao = data.get('situacao')  # 1 = Autorizada, outros valores = outras situações
        nfe_numero = data.get('numero')
        nfe_tipo = data.get('tipo')  # 0 = NF-e (Modelo 55), 1 = NFC-e
        
        if not nfe_id:
            current_app.logger.warning(f"Webhook de nota fiscal sem ID. Event: {event}")
            return jsonify({
                "status": "ok",
                "message": "Webhook sem ID da nota fiscal, ignorado"
            }), 200
        
        # Buscar pedido relacionado à nota fiscal
        from ..services.bling_order_service import get_order_by_nfe_id
        
        pedido_info = get_order_by_nfe_id(nfe_id)
        
        if not pedido_info:
            current_app.logger.warning(
                f"Nota fiscal {nfe_id} não encontrada em nenhum pedido local. "
                f"Pode ser uma nota criada diretamente no Bling."
            )
            return jsonify({
                "status": "ok",
                "message": f"Nota fiscal {nfe_id} não encontrada em pedidos locais"
            }), 200
        
        venda_id = pedido_info['venda_id']
        bling_pedido_id = pedido_info['bling_pedido_id']
        
        current_app.logger.info(f"📋 Nota fiscal {nfe_id} relacionada ao pedido {venda_id} (Bling: {bling_pedido_id})")
        
        # Processar baseado na ação
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            if action == 'updated':
                # Verificar se situação mudou para Autorizada (1)
                if nfe_situacao == 1:
                    current_app.logger.info(
                        f"✅ NF-e {nfe_id} AUTORIZADA pelo SEFAZ para pedido {venda_id}"
                    )
                    
                    # Atualizar informações da NF-e no banco
                    cur.execute("""
                        UPDATE bling_pedidos
                        SET bling_nfe_id = %s,
                            nfe_numero = %s,
                            nfe_status = 'AUTORIZADA',
                            updated_at = NOW()
                        WHERE venda_id = %s
                    """, (nfe_id, nfe_numero, venda_id))
                    
                    # Atualizar status do pedido para nfe_autorizada
                    cur.execute("""
                        UPDATE vendas
                        SET status_pedido = 'nfe_autorizada',
                            atualizado_em = NOW()
                        WHERE id = %s
                    """, (venda_id,))
                    
                    conn.commit()
                    
                    current_app.logger.info(
                        f"✅ Status do pedido {venda_id} atualizado para 'nfe_autorizada'"
                    )
                    
                    # Criar etiqueta de frete após aprovação do SEFAZ
                    # Verificar se já existe etiqueta
                    cur.execute("""
                        SELECT id FROM etiquetas_frete ef
                        INNER JOIN etiquetas_frete_venda_lnk lnk ON ef.id = lnk.etiqueta_frete_id
                        WHERE lnk.venda_id = %s
                        LIMIT 1
                    """, (venda_id,))
                    etiqueta_existente = cur.fetchone()
                    
                    if not etiqueta_existente:
                        # Criar etiqueta automaticamente após aprovação do SEFAZ
                        try:
                            from ..api.labels import create_label_automatically
                            current_app.logger.info(
                                f"📦 Criando etiqueta de frete para venda {venda_id} após aprovação do SEFAZ"
                            )
                            etiqueta_id = create_label_automatically(venda_id)
                            if etiqueta_id:
                                current_app.logger.info(
                                    f"✅ Etiqueta {etiqueta_id} criada automaticamente para venda {venda_id} "
                                    f"após aprovação do SEFAZ"
                                )
                            else:
                                current_app.logger.warning(
                                    f"⚠️ Não foi possível criar etiqueta para venda {venda_id}"
                                )
                        except Exception as etiqueta_error:
                            current_app.logger.error(
                                f"❌ Erro ao criar etiqueta após aprovação SEFAZ para venda {venda_id}: {etiqueta_error}",
                                exc_info=True
                            )
                            # Não falhar o webhook por erro na etiqueta
                    else:
                        current_app.logger.info(
                            f"ℹ️ Etiqueta já existe para venda {venda_id} (ID: {etiqueta_existente[0]})"
                        )
                    
                    # Mudar situação do pedido no Bling para "Logística"
                    from ..services.bling_order_service import update_order_situacao_to_logistica
                    
                    logistica_result = update_order_situacao_to_logistica(venda_id)
                    
                    if logistica_result.get('success'):
                        current_app.logger.info(
                            f"✅ Pedido {venda_id} movido para 'Logística' no Bling. "
                            f"Bling irá automaticamente: decrementar estoque, etc."
                        )
                        
                        # Atualizar status para pronto_envio após mudar para Logística
                        cur.execute("""
                            UPDATE vendas
                            SET status_pedido = 'pronto_envio',
                                atualizado_em = NOW()
                            WHERE id = %s
                        """, (venda_id,))
                        conn.commit()
                        
                        current_app.logger.info(
                            f"✅ Status do pedido {venda_id} atualizado para 'pronto_envio'"
                        )
                    else:
                        current_app.logger.warning(
                            f"⚠️ Não foi possível mover pedido {venda_id} para 'Logística' no Bling: "
                            f"{logistica_result.get('error')}"
                        )
                    
                    return jsonify({
                        "status": "ok",
                        "message": f"NF-e {nfe_id} autorizada e pedido {venda_id} atualizado",
                        "venda_id": venda_id,
                        "nfe_id": nfe_id,
                        "nfe_situacao": nfe_situacao,
                        "logistica_atualizada": logistica_result.get('success', False)
                    }), 200
                else:
                    # Situação mudou mas não é Autorizada
                    current_app.logger.info(
                        f"ℹ️ NF-e {nfe_id} atualizada, mas situação não é Autorizada: {nfe_situacao}"
                    )
                    
                    # Atualizar status da NFC-e mesmo assim
                    situacao_map = {
                        0: 'PENDENTE',
                        1: 'AUTORIZADA',
                        2: 'CANCELADA',
                        3: 'REJEITADA'
                    }
                    nfe_status_str = situacao_map.get(nfe_situacao, f'DESCONHECIDA_{nfe_situacao}')
                    
                    cur.execute("""
                        UPDATE bling_pedidos
                        SET nfe_status = %s,
                            updated_at = NOW()
                        WHERE venda_id = %s
                    """, (nfe_status_str, venda_id))
                    
                    conn.commit()
                    
                    return jsonify({
                        "status": "ok",
                        "message": f"NF-e {nfe_id} atualizada (situação: {nfe_situacao})"
                    }), 200
                    
            elif action == 'created':
                # NF-e criada (ainda não autorizada)
                current_app.logger.info(f"📄 NF-e {nfe_id} criada para pedido {venda_id}")
                
                # Atualizar informações da NF-e no banco
                cur.execute("""
                    UPDATE bling_pedidos
                    SET bling_nfe_id = %s,
                        nfe_numero = %s,
                        nfe_status = 'PENDENTE',
                        updated_at = NOW()
                    WHERE venda_id = %s
                """, (nfe_id, nfe_numero, venda_id))
                
                conn.commit()
                
                return jsonify({
                    "status": "ok",
                    "message": f"NF-e {nfe_id} criada para pedido {venda_id}"
                }), 200
                
            elif action == 'deleted':
                # NF-e deletada
                current_app.logger.info(f"🗑️ NF-e {nfe_id} deletada para pedido {venda_id}")
                
                # Atualizar status da NF-e
                cur.execute("""
                    UPDATE bling_pedidos
                    SET nfe_status = 'CANCELADA',
                        updated_at = NOW()
                    WHERE venda_id = %s
                """, (venda_id,))
                
                conn.commit()
                
                return jsonify({
                    "status": "ok",
                    "message": f"NF-e {nfe_id} deletada para pedido {venda_id}"
                }), 200
            else:
                current_app.logger.warning(f"Ação desconhecida no webhook de NF-e: {action}")
                return jsonify({
                    "status": "ok",
                    "message": f"Ação {action} não processada"
                }), 200
                
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao processar webhook de NF-e: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                "status": "ok",
                "message": "Erro ao processar webhook, mas retornando 200 para idempotência"
            }), 200
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro no webhook de NF-e: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            "status": "ok",
            "message": "Erro ao processar webhook"
        }), 200


@webhook_api_bp.route('/bling', methods=['GET', 'POST'])
def bling_webhook():
    """
    Webhook para receber notificações do Bling sobre eventos de estoque.
    
    GET /api/webhook/bling - Validação de acessibilidade (retorna 200 OK)
    POST /api/webhook/bling - Recebe notificações do Bling
    
    O Bling pode fazer uma requisição GET para validar se a URL está acessível.
    
    Eventos suportados:
    - stock.created: Quando um lançamento de estoque é criado
    - stock.updated: Quando um lançamento de estoque é atualizado
    - stock.deleted: Quando um lançamento de estoque é deletado
    - order.created: Quando um pedido é criado no Bling
    - order.updated: Quando um pedido é atualizado no Bling (incluindo mudanças de status)
    - order.deleted: Quando um pedido é deletado no Bling
    
    A autenticação é feita através do header X-Bling-Signature-256 (HMAC-SHA256).
    """
    # Se for GET, apenas retornar 200 OK para validação
    if request.method == 'GET':
        current_app.logger.info("Webhook Bling - Validação de acessibilidade (GET)")
        return jsonify({
            "status": "ok",
            "message": "Webhook endpoint está acessível"
        }), 200
    
    # Obter o corpo da requisição como bytes para validação HMAC
    request_body = request.get_data()
    signature_header = request.headers.get('X-Bling-Signature-256', '')
    
    # Validar assinatura HMAC
    from ..api.bling import verify_bling_webhook_signature
    
    if not verify_bling_webhook_signature(request_body, signature_header):
        client_ip = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            client_ip = request.headers.get('X-Real-IP')
        
        current_app.logger.error("=" * 80)
        current_app.logger.error("🚨 ACESSO NEGADO AO WEBHOOK BLING - Assinatura inválida")
        current_app.logger.error("=" * 80)
        current_app.logger.error(f"IP de origem: {client_ip}")
        current_app.logger.error(f"Assinatura recebida: {signature_header[:50]}...")
        current_app.logger.error(f"User-Agent: {request.headers.get('User-Agent', 'N/A')}")
        current_app.logger.error("=" * 80)
        
        return jsonify({
            "erro": "Acesso negado",
            "message": "Assinatura inválida"
        }), 403
    
    # Processar webhook
    try:
        # Obter dados JSON do webhook
        webhook_data = request.get_json()
        
        if not webhook_data:
            current_app.logger.warning("Webhook Bling sem dados JSON")
            return jsonify({"erro": "Dados não fornecidos"}), 400
        
        # Log da requisição recebida
        current_app.logger.info("=" * 80)
        current_app.logger.info("🔔 WEBHOOK BLING RECEBIDO (VALIDADO)")
        current_app.logger.info("=" * 80)
        current_app.logger.info(f"Event ID: {webhook_data.get('eventId', 'N/A')}")
        current_app.logger.info(f"Event: {webhook_data.get('event', 'N/A')}")
        current_app.logger.info(f"Date: {webhook_data.get('date', 'N/A')}")
        current_app.logger.info(f"Version: {webhook_data.get('version', 'N/A')}")
        current_app.logger.info(f"Company ID: {webhook_data.get('companyId', 'N/A')}")
        
        # Extrair informações do webhook
        event = webhook_data.get('event', '')
        event_id = webhook_data.get('eventId', '')
        data = webhook_data.get('data', {})
        
        # Verificar tipo de evento
        if event.startswith('stock.'):
            # Processar evento de estoque (já implementado abaixo)
            pass
        elif event.startswith('order.'):
            # Processar evento de pedido
            return process_order_webhook(webhook_data, event, event_id, data)
        elif event.startswith('consumer_invoice.') or event.startswith('nfe.'):
            # Processar evento de nota fiscal
            return process_nfe_webhook(webhook_data, event, event_id, data)
        else:
            current_app.logger.info(f"Evento não reconhecido: {event}. Ignorando...")
            return jsonify({
                "status": "ok",
                "message": f"Evento {event} não reconhecido, ignorado"
            }), 200
        
        # Determinar ação (created, updated, deleted)
        action = event.split('.')[-1] if '.' in event else 'unknown'
        
        current_app.logger.info(f"Processando evento de estoque: {action}")
        
        # Processar evento de estoque
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Extrair informações do produto do webhook
            produto_bling_id = None
            saldo_fisico_total = None
            
            if 'produto' in data and isinstance(data['produto'], dict):
                produto_bling_id = data['produto'].get('id')
            
            # Obter saldo físico total (estoque atual)
            saldo_fisico_total = data.get('saldoFisicoTotal') or data.get('saldo_fisico_total')
            
            if not produto_bling_id:
                current_app.logger.warning(f"Webhook Bling sem produto ID. Event: {event}, Data: {json.dumps(data, indent=2)[:500]}")
                return jsonify({
                    "status": "ok",
                    "message": "Webhook sem produto ID, ignorado"
                }), 200
            
            # Buscar produto local pelo bling_id
            cur.execute("""
                SELECT p.id as produto_id, p.estoque as estoque_atual, bp.bling_id, bp.bling_codigo
                FROM produtos p
                JOIN bling_produtos bp ON p.id = bp.produto_id
                WHERE bp.bling_id = %s
            """, (produto_bling_id,))
            
            produto_local = cur.fetchone()
            
            if not produto_local:
                current_app.logger.warning(f"Produto não encontrado no banco local para bling_id: {produto_bling_id}")
                return jsonify({
                    "status": "ok",
                    "message": f"Produto bling_id {produto_bling_id} não encontrado localmente"
                }), 200
            
            produto_id_local = produto_local['produto_id']
            estoque_anterior = produto_local['estoque_atual']
            
            # Processar baseado na ação
            if action == 'deleted':
                # Para deleted, o webhook pode não ter saldoFisicoTotal
                # Nesse caso, vamos buscar o estoque atual do Bling via API
                # Por enquanto, vamos apenas logar e manter o estoque atual
                current_app.logger.info(f"Evento de estoque deletado para produto {produto_id_local} (bling_id: {produto_bling_id})")
                current_app.logger.info("Para eventos deleted, considere buscar estoque atual via API do Bling se necessário")
                
                # Retornar sucesso mesmo sem atualizar (conforme documentação, deve retornar 2xx)
                return jsonify({
                    "status": "ok",
                    "message": f"Evento deleted recebido para produto {produto_id_local}"
                }), 200
            
            # Para created e updated, atualizar estoque com saldoFisicoTotal
            if saldo_fisico_total is None:
                current_app.logger.warning(f"Webhook Bling sem saldoFisicoTotal. Event: {event}, Produto: {produto_id_local}")
                return jsonify({
                    "status": "ok",
                    "message": "Webhook sem saldoFisicoTotal, ignorado"
                }), 200
            
            # Converter saldo para inteiro
            try:
                estoque_novo = int(float(saldo_fisico_total))
            except (ValueError, TypeError):
                current_app.logger.error(f"Erro ao converter saldoFisicoTotal para inteiro: {saldo_fisico_total}")
                return jsonify({
                    "status": "ok",
                    "message": "Erro ao converter saldoFisicoTotal"
                }), 200
            
            # Atualizar estoque na tabela produtos
            cur.execute("""
                UPDATE produtos
                SET estoque = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (estoque_novo, produto_id_local))
            
            conn.commit()
            
            current_app.logger.info(f"✅ Estoque atualizado para produto {produto_id_local} (bling_id: {produto_bling_id})")
            current_app.logger.info(f"   Estoque anterior: {estoque_anterior}")
            current_app.logger.info(f"   Estoque novo: {estoque_novo}")
            current_app.logger.info(f"   Evento: {event}")
            current_app.logger.info(f"   Event ID: {event_id}")
            
            # Logar sincronização
            try:
                cur.execute("""
                    INSERT INTO bling_sync_logs (entity_type, entity_id, action, status, response_data, created_at)
                    VALUES ('produto', %s, 'sync', 'success', %s, NOW())
                """, (produto_id_local, json.dumps({
                    'event': event,
                    'event_id': event_id,
                    'bling_id': produto_bling_id,
                    'estoque_anterior': estoque_anterior,
                    'estoque_novo': estoque_novo,
                    'action': 'webhook_stock_update'
                })))
                conn.commit()
            except Exception as log_error:
                current_app.logger.warning(f"Erro ao logar sincronização: {log_error}")
                conn.rollback()
            
            return jsonify({
                "status": "ok",
                "message": "Estoque atualizado com sucesso",
                "produto_id": produto_id_local,
                "estoque_anterior": estoque_anterior,
                "estoque_novo": estoque_novo
            }), 200
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao processar webhook Bling: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            # Retornar 200 para não fazer o Bling reenviar (idempotência)
            return jsonify({
                "status": "ok",
                "message": "Erro ao processar, mas webhook aceito"
            }), 200
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro no webhook Bling: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        # Retornar 200 para não fazer o Bling reenviar (idempotência - conforme documentação)
        return jsonify({
            "status": "ok",
            "message": "Erro ao processar webhook"
        }), 200
    """
    Processa webhook de pedido do Bling
    
    Args:
        webhook_data: Dados completos do webhook
        event: Tipo do evento (ex: "order.updated")
        event_id: ID do evento
        data: Dados do pedido do webhook
    
    Returns:
        Response Flask
    """
    try:
        # Determinar ação (created, updated, deleted)
        action = event.split('.')[-1] if '.' in event else 'unknown'
        
        current_app.logger.info(f"Processando evento de pedido: {action}")
        current_app.logger.info(f"Dados do pedido: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
        
        # Extrair informações do pedido do webhook
        bling_pedido_id = data.get('id')
        
        if not bling_pedido_id:
            current_app.logger.warning(f"Webhook Bling sem ID do pedido. Event: {event}")
            return jsonify({
                "status": "ok",
                "message": "Webhook sem ID do pedido, ignorado"
            }), 200
        
        # Processar evento de pedido
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Buscar pedido local pelo bling_pedido_id
            cur.execute("""
                SELECT v.id as venda_id, v.status_pedido as status_atual, bp.bling_pedido_id
                FROM vendas v
                JOIN bling_pedidos bp ON v.id = bp.venda_id
                WHERE bp.bling_pedido_id = %s
            """, (bling_pedido_id,))
            
            pedido_local = cur.fetchone()
            
            if not pedido_local:
                current_app.logger.warning(f"Pedido não encontrado no banco local para bling_pedido_id: {bling_pedido_id}")
                return jsonify({
                    "status": "ok",
                    "message": f"Pedido bling_pedido_id {bling_pedido_id} não encontrado localmente"
                }), 200
            
            venda_id = pedido_local['venda_id']
            status_atual = pedido_local['status_atual']
            
            # Para eventos deleted, apenas logar
            if action == 'deleted':
                current_app.logger.info(f"Evento de pedido deletado para venda {venda_id} (bling_pedido_id: {bling_pedido_id})")
                return jsonify({
                    "status": "ok",
                    "message": f"Evento deleted recebido para pedido {venda_id}"
                }), 200
            
            # Para created e updated, atualizar status se houver mudança
            situacao_bling = data.get('situacao') or data.get('situacao')
            numero = data.get('numero')
            numero_loja = data.get('numeroLoja')
            
            # Mapear situação do Bling para status local
            from ..services.bling_order_service import map_bling_situacao_to_status
            
            status_novo = map_bling_situacao_to_status(situacao_bling) if situacao_bling else status_atual
            
            # Atualizar status se houver mudança
            if status_novo != status_atual:
                cur.execute("""
                    UPDATE vendas
                    SET status_pedido = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (status_novo, venda_id))
                
                # Atualizar informações da NF-e se houver
                nfe_data = data.get('notaFiscal') or data.get('nota_fiscal')
                if nfe_data:
                    nfe_id = nfe_data.get('id')
                    nfe_numero = nfe_data.get('numero')
                    nfe_chave_acesso = nfe_data.get('chaveAcesso') or nfe_data.get('chave_acesso')
                    nfe_situacao = nfe_data.get('situacao', '')
                    
                    cur.execute("""
                        UPDATE bling_pedidos
                        SET bling_nfe_id = %s,
                            nfe_numero = %s,
                            nfe_chave_acesso = %s,
                            nfe_status = %s,
                            updated_at = NOW()
                        WHERE venda_id = %s
                    """, (nfe_id, nfe_numero, nfe_chave_acesso, nfe_situacao, venda_id))
                
                conn.commit()
                
                current_app.logger.info(f"✅ Status atualizado para pedido {venda_id} (bling_pedido_id: {bling_pedido_id})")
                current_app.logger.info(f"   Status anterior: {status_atual}")
                current_app.logger.info(f"   Status novo: {status_novo}")
                current_app.logger.info(f"   Situação Bling: {situacao_bling}")
                current_app.logger.info(f"   Evento: {event}")
                current_app.logger.info(f"   Event ID: {event_id}")
                
                # Logar sincronização
                try:
                    cur.execute("""
                        INSERT INTO bling_sync_logs (entity_type, entity_id, action, status, response_data, created_at)
                        VALUES ('pedido', %s, 'sync', 'success', %s, NOW())
                    """, (venda_id, json.dumps({
                        'event': event,
                        'event_id': event_id,
                        'bling_pedido_id': bling_pedido_id,
                        'status_anterior': status_atual,
                        'status_novo': status_novo,
                        'situacao_bling': situacao_bling,
                        'action': 'webhook_order_update'
                    })))
                    conn.commit()
                except Exception as log_error:
                    current_app.logger.warning(f"Erro ao logar sincronização: {log_error}")
                    conn.rollback()
            else:
                current_app.logger.info(f"Status do pedido {venda_id} não mudou (continua {status_atual})")
            
            return jsonify({
                "status": "ok",
                "message": "Pedido processado com sucesso",
                "venda_id": venda_id,
                "status_atual": status_novo,
                "situacao_bling": situacao_bling
            }), 200
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao processar webhook de pedido Bling: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            # Retornar 200 para não fazer o Bling reenviar (idempotência)
            return jsonify({
                "status": "ok",
                "message": "Erro ao processar, mas webhook aceito"
            }), 200
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro no processamento de webhook de pedido: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        # Retornar 200 para não fazer o Bling reenviar (idempotência)
        return jsonify({
            "status": "ok",
            "message": "Erro ao processar webhook"
        }), 200

