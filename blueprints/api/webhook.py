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
from ..services.order_service import get_order_by_venda_id, update_order_status, delete_order_token, sync_order_status_from_venda
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
                                # Buscar dados completos do pagamento para processar o webhook
                                # Mesmo que a API retorne 404, podemos processar usando o status do banco
                                cur_temp.execute("""
                                    SELECT p.id, p.venda_id, p.status_pagamento, p.pagbank_order_id, p.pagbank_charge_id,
                                           v.codigo_pedido, v.status_pedido
                                    FROM pagamentos p
                                    JOIN vendas v ON p.venda_id = v.id
                                    WHERE p.id = %s
                                """, (payment['id'],))
                                payment_full = cur_temp.fetchone()
                                
                                if payment_full:
                                    # Processar webhook usando dados do banco
                                    # Criar estrutura de dados similar à resposta da API
                                    venda_id = payment_full['venda_id']
                                    current_status = payment_full['status_pagamento']
                                    
                                    # Se o pagamento já está pago e o pedido ainda não foi criado no Bling, criar agora
                                    if current_status in ['PAID', 'AUTHORIZED', 'APPROVED']:
                                        # Verificar se o pedido já existe no Bling
                                        cur_temp.execute("""
                                            SELECT bp.bling_pedido_id
                                            FROM bling_pedidos bp
                                            WHERE bp.venda_id = %s
                                            LIMIT 1
                                        """, (venda_id,))
                                        bling_pedido = cur_temp.fetchone()
                                        
                                        if not bling_pedido:
                                            current_app.logger.info(
                                                f"💰 Pagamento {payment_full['id']} está {current_status} mas pedido ainda não foi criado no Bling. "
                                                f"Criando pedido para venda {venda_id}..."
                                            )
                                            try:
                                                from ..services.bling_order_service import sync_order_to_bling
                                                result = sync_order_to_bling(venda_id)
                                                
                                                if result.get('success'):
                                                    bling_pedido_id = result.get('bling_pedido_id')
                                                    current_app.logger.info(f"✅ Pedido criado no Bling: {bling_pedido_id}")
                                                else:
                                                    current_app.logger.warning(
                                                        f"⚠️ Falha ao criar pedido no Bling: {result.get('error')}"
                                                    )
                                            except Exception as bling_error:
                                                current_app.logger.error(
                                                    f"❌ Erro ao criar pedido no Bling: {bling_error}",
                                                    exc_info=True
                                                )
                                        else:
                                            current_app.logger.info(
                                                f"ℹ️ Pedido já existe no Bling para venda {venda_id} (ID: {bling_pedido['bling_pedido_id']})"
                                            )
                                    
                                    # Aceitar a notificação
                                    return jsonify({
                                        "status": "ok",
                                        "message": "Notificação recebida, pagamento encontrado no banco e processado"
                                    }), 200
                                else:
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
                        bling_pedido_id = result.get('bling_pedido_id')
                        current_app.logger.info(f"✅ Pedido criado no Bling: {bling_pedido_id}")
                        
                        # NOTA: Não emitir NF-e quando pedido está em aberto
                        # A NF-e será emitida apenas quando a nota for aprovada (via webhook NFE)
                        current_app.logger.info(
                            f"ℹ️ Pedido {bling_pedido_id} criado no Bling. "
                            f"NF-e será emitida apenas quando a nota for aprovada."
                        )
                        
                        # REMOVIDO: Lógica de emissão de NF-e no pedido em aberto
                        # A emissão agora acontece apenas quando a nota é aprovada (via webhook NFE)
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
            # IMPORTANTE: Quando o pagamento é confirmado, o pedido vai para "Em aberto" no Bling
            # "Em aberto" (ID 6) mapeia para 'sincronizado_bling' que mostra como 'PAGO'
            # Só quando mudar para "Em andamento" (ID 15) é que vira 'pagamento_aprovado' e mostra como 'APROVADO'
            venda_status_map = {
                'PAID': 'sincronizado_bling',  # Pagamento confirmado → "Em aberto" no Bling → PAGO (não APROVADO)
                'AUTHORIZED': 'sincronizado_bling',  # Pagamento autorizado → "Em aberto" no Bling → PAGO (não APROVADO)
                'APPROVED': 'sincronizado_bling',  # Pagamento aprovado → "Em aberto" no Bling → PAGO (não APROVADO)
                'DECLINED': 'cancelado_pelo_vendedor',
                'CANCELLED': 'cancelado_pelo_vendedor',
                'REFUNDED': 'cancelado_pelo_vendedor',
                'EXPIRED': 'cancelado_pelo_vendedor'
            }
            
            new_venda_status = venda_status_map.get(status.upper())
            if new_venda_status:
                cur.execute("""
                    UPDATE vendas
                    SET status_pedido = %s
                    WHERE id = %s
                """, (new_venda_status, venda_id))
                conn.commit()
                
                # Sincronizar status da tabela orders
                try:
                    sync_order_status_from_venda(venda_id)
                except Exception as sync_error:
                    current_app.logger.warning(f"Erro ao sincronizar status do order: {sync_error}")
                
                # IMPORTANTE: Estoque é gerenciado exclusivamente pelo Bling
                # Quando o pedido for criado no Bling, o Bling abaterá o estoque automaticamente
                # O webhook do Bling (stock.updated) atualizará o estoque do site automaticamente
                if new_venda_status == 'sincronizado_bling':
                    current_app.logger.info(
                        f"ℹ️ Pagamento confirmado. Pedido {venda_id} será criado no Bling em 'Em aberto'. "
                        f"O webhook do Bling atualizará o estoque do site automaticamente."
                    )
                    
                    # NF-e será emitida quando pedido mudar para "Em andamento" no Bling (ID 15)
                    current_app.logger.info(
                        f"ℹ️ NF-e será emitida automaticamente quando pedido {venda_id} "
                        f"mudar para 'Em andamento' no Bling (via webhook do Bling). "
                        f"Até lá, o status permanecerá como 'PAGO' (não 'APROVADO')."
                    )
            
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
            # Verificar se coluna bling_situacao_id existe antes de usar
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'vendas' 
                AND column_name = 'bling_situacao_id'
            """)
            has_bling_situacao_id = cur.fetchone() is not None
            
            if has_bling_situacao_id:
                cur.execute("""
                    SELECT v.id as venda_id, v.status_pedido as status_atual, 
                           v.bling_situacao_id as situacao_atual_id,
                           bp.bling_pedido_id
                    FROM vendas v
                    JOIN bling_pedidos bp ON v.id = bp.venda_id
                    WHERE bp.bling_pedido_id = %s
                """, (bling_pedido_id,))
            else:
                # Se a coluna não existe, buscar apenas status_pedido
                cur.execute("""
                    SELECT v.id as venda_id, v.status_pedido as status_atual, 
                           NULL as situacao_atual_id,
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
            situacao_atual_id = pedido_local.get('situacao_atual_id')  # Pode ser None se coluna não existe
            
            # Para eventos deleted, apenas logar
            if action == 'deleted':
                current_app.logger.info(f"Evento de pedido deletado para venda {venda_id} (bling_pedido_id: {bling_pedido_id})")
                return jsonify({
                    "status": "ok",
                    "message": f"Evento deleted recebido para pedido {venda_id}"
                }), 200
            
            # PROTEÇÃO: Não permitir regressão de "Logística" para "Em andamento"
            # Se o pedido já está em "pronto_envio" (Logística), não deve voltar para "Em andamento"
            if status_atual == 'pronto_envio':
                current_app.logger.info(
                    f"🛡️ PROTEÇÃO: Pedido {venda_id} já está em 'pronto_envio' (Logística). "
                    f"Ignorando atualização de situação via webhook para evitar regressão."
                )
                return jsonify({
                    "status": "ok",
                    "message": f"Pedido {venda_id} já está em Logística, ignorando atualização"
                }), 200
            
            # Extrair ID da situação do Bling (pode vir em diferentes formatos)
            # IMPORTANTE: Extrair antes da proteção para poder verificar se é Logística
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
                # Buscar pedido completo no Bling para obter situação
                try:
                    from ..services.bling_order_service import get_bling_order_by_local_id
                    from ..services.bling_api_service import make_bling_api_request
                    
                    pedido_bling_local = get_bling_order_by_local_id(venda_id)
                    if pedido_bling_local:
                        bling_pedido_id = pedido_bling_local.get('bling_pedido_id')
                        if bling_pedido_id:
                            current_app.logger.info(
                                f"🔍 Situação não encontrada no webhook. Buscando pedido {bling_pedido_id} no Bling..."
                            )
                            response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
                            if response.status_code == 200:
                                pedido_data = response.json().get('data', {})
                                situacao_data = pedido_data.get('situacao', {})
                                if isinstance(situacao_data, dict):
                                    situacao_bling_id = situacao_data.get('id')
                                    situacao_bling_nome = situacao_data.get('nome')
                                    
                                    # Se temos ID mas não nome, buscar nome via API de situações
                                    if situacao_bling_id and not situacao_bling_nome:
                                        try:
                                            from ..services.bling_situacao_service import get_bling_situacao_by_id
                                            situacao_info = get_bling_situacao_by_id(situacao_bling_id)
                                            if situacao_info:
                                                situacao_bling_nome = situacao_info.get('nome')
                                                current_app.logger.info(
                                                    f"✅ Situação encontrada no Bling: ID {situacao_bling_id} - {situacao_bling_nome}"
                                                )
                                            else:
                                                current_app.logger.info(
                                                    f"✅ Situação encontrada no Bling: ID {situacao_bling_id} - (nome não disponível)"
                                                )
                                        except Exception as e:
                                            current_app.logger.warning(f"Erro ao buscar nome da situação {situacao_bling_id}: {e}")
                                            current_app.logger.info(
                                                f"✅ Situação encontrada no Bling: ID {situacao_bling_id}"
                                            )
                                    else:
                                        current_app.logger.info(
                                            f"✅ Situação encontrada no Bling: ID {situacao_bling_id} - {situacao_bling_nome or '(nome não disponível)'}"
                                        )
                except Exception as e:
                    current_app.logger.warning(f"Erro ao buscar situação do pedido via API: {e}")
            
            # Se ainda não tem situação, usar situação antiga ou ignorar
            if not situacao_bling_id:
                if situacao_atual_id is not None:
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
            
            # Buscar nome da situação se não fornecido (ANTES de verificar se mudou)
            if not situacao_bling_nome and situacao_bling_id:
                # Primeiro tentar buscar no banco (mais rápido)
                try:
                    from ..services.bling_situacao_service import get_situacao_mapping
                    situacao_info = get_situacao_mapping(situacao_bling_id)
                    if situacao_info:
                        situacao_bling_nome = situacao_info.get('nome')
                        current_app.logger.info(f"✅ [WEBHOOK] Nome encontrado no banco: '{situacao_bling_nome}'")
                    else:
                        # Se não encontrou no banco, buscar via API do Bling
                        try:
                            from ..services.bling_situacao_service import get_bling_situacao_by_id
                            situacao_info = get_bling_situacao_by_id(situacao_bling_id)
                            if situacao_info:
                                situacao_bling_nome = situacao_info.get('nome')
                                current_app.logger.info(f"✅ [WEBHOOK] Nome encontrado via API: '{situacao_bling_nome}'")
                        except Exception as e:
                            current_app.logger.warning(f"⚠️ [WEBHOOK] Erro ao buscar nome da situação via API: {e}")
                except Exception as e:
                    current_app.logger.warning(f"⚠️ [WEBHOOK] Erro ao buscar nome da situação no banco: {e}")
            
            # Log da situação final
            if situacao_bling_id:
                current_app.logger.info(
                    f"📋 [WEBHOOK] Situação do pedido {venda_id}: ID {situacao_bling_id} - '{situacao_bling_nome or 'sem nome'}'"
                )
            
            # PROTEÇÃO: Se o pedido já está em "nfe_autorizada", permitir apenas mudança para Logística
            if status_atual == 'nfe_autorizada':
                # Se está tentando mudar para Logística (ID 716906), permitir
                if situacao_bling_id == 716906:
                    current_app.logger.info(
                        f"✅ Permitindo mudança para Logística para pedido {venda_id} "
                        f"(status atual: nfe_autorizada)"
                    )
                    # Continuar o fluxo normalmente
                else:
                    current_app.logger.info(
                        f"🛡️ PROTEÇÃO: Pedido {venda_id} já tem NF-e autorizada. "
                        f"Ignorando atualização de situação via webhook para evitar regressão."
                    )
                    return jsonify({
                        "status": "ok",
                        "message": f"Pedido {venda_id} já tem NF-e autorizada, ignorando atualização"
                    }), 200
            
            # PROTEÇÃO ADICIONAL: Verificar se está tentando regredir de "Logística" (ID 716906) para outra situação
            # Se a situação atual é "Logística" e está tentando mudar para outra, bloquear
            if situacao_atual_id is not None and situacao_atual_id == 716906 and situacao_bling_id != 716906:
                current_app.logger.warning(
                    f"🛡️ PROTEÇÃO: Tentativa de regressão detectada para pedido {venda_id}! "
                    f"Situação atual: Logística (ID 716906) → Tentando mudar para: {situacao_bling_id} ({situacao_bling_nome or 'sem nome'})"
                )
                current_app.logger.warning(
                    f"   Status atual: {status_atual}"
                )
                current_app.logger.warning(
                    f"   ⚠️ BLOQUEANDO regressão. Pedido permanecerá em 'Logística'."
                )
                return jsonify({
                    "status": "ok",
                    "message": f"Proteção: bloqueada regressão de Logística para {situacao_bling_id}"
                }), 200
            
            # Verificar se mudou para "Atendido" (comportamento padrão do Bling ao emitir NF-e)
            situacao_nome_lower = (situacao_bling_nome or '').lower() if situacao_bling_nome else ''
            is_atendido = (
                situacao_bling_id == 9 or  # ID conhecido de "Atendido"
                'atendido' in situacao_nome_lower
            )
            
            if is_atendido:
                current_app.logger.info(
                    f"ℹ️ Pedido {venda_id} mudou para 'Atendido' (comportamento padrão do Bling ao emitir NF-e). "
                    f"Será movido para 'Logística' quando NF-e for aprovada pelo SEFAZ."
                )
                # Permitir a mudança - não bloquear (comportamento esperado do Bling)
            
            # IMPORTANTE: Verificar se precisa emitir NF-e quando pedido está em "Em andamento"
            # Isso deve ser verificado tanto quando a situação muda quanto quando não muda
            situacao_nome_lower = (situacao_bling_nome or '').lower() if situacao_bling_nome else ''
            is_em_andamento = (
                'em andamento' in situacao_nome_lower or
                situacao_bling_id == 15  # ID conhecido de "Em andamento"
            )
            
            # Garantir que NÃO está em "Em aberto" (ID 6)
            is_em_aberto = (
                'em aberto' in situacao_nome_lower or
                situacao_bling_id == 6  # ID conhecido de "Em aberto"
            )
            
            current_app.logger.info(
                f"🔍 Verificando emissão de NF-e para pedido {venda_id}: "
                f"situacao_id={situacao_bling_id}, situacao_nome='{situacao_bling_nome}', "
                f"is_em_andamento={is_em_andamento}, is_em_aberto={is_em_aberto}, "
                f"situacao_mudou={situacao_atual_id is None or situacao_bling_id != situacao_atual_id}, "
                f"situacao_atual_id={situacao_atual_id}"
            )
            
            # Função auxiliar para verificar e emitir NF-e
            def verificar_e_emitir_nfe():
                """Verifica se precisa emitir NF-e e emite se necessário"""
                if not is_em_andamento or is_em_aberto:
                    return False
                
                # Verificar se NF-e já foi emitida E está associada ao pedido no Bling
                cur.execute("""
                    SELECT bp.bling_nfe_id, bp.nfe_status, bp.bling_pedido_id
                    FROM bling_pedidos bp
                    WHERE bp.venda_id = %s
                """, (venda_id,))
                
                nfe_info = cur.fetchone()
                pedido_bling_id = nfe_info.get('bling_pedido_id') if nfe_info else None
                nfe_id_local = nfe_info.get('bling_nfe_id') if nfe_info else None
                
                # Verificar se a NF-e está realmente associada ao pedido no Bling
                nfe_associada = False
                if nfe_id_local and pedido_bling_id:
                    try:
                        from ..services.bling_api_service import make_bling_api_request
                        
                        # Buscar pedido no Bling para verificar se tem NF-e associada
                        response_pedido = make_bling_api_request(
                            'GET',
                            f'/pedidos/vendas/{pedido_bling_id}'
                        )
                        
                        if response_pedido.status_code == 200:
                            pedido_data = response_pedido.json().get('data', {})
                            nfe_pedido = pedido_data.get('notaFiscal', {})
                            
                            if nfe_pedido and nfe_pedido.get('id') == nfe_id_local:
                                nfe_associada = True
                                current_app.logger.info(
                                    f"✅ NF-e {nfe_id_local} está associada ao pedido {pedido_bling_id} no Bling"
                                )
                            else:
                                current_app.logger.info(
                                    f"⚠️ NF-e {nfe_id_local} existe no banco local mas NÃO está associada ao pedido {pedido_bling_id} no Bling. "
                                    f"Vamos emitir uma nova NF-e associada ao pedido."
                                )
                    except Exception as e:
                        current_app.logger.warning(
                            f"⚠️ Erro ao verificar associação NF-e/pedido no Bling: {e}. "
                            f"Vamos tentar emitir NF-e novamente."
                        )
                
                # Se não tem NF-e associada, emitir agora
                if not nfe_associada:
                    current_app.logger.info(
                        f"📄 Pedido {venda_id} está em 'Em andamento' e não tem NF-e. "
                        f"Emitindo NF-e agora..."
                    )
                    try:
                        from ..services.bling_nfe_service import emit_nfe
                        nfe_result = emit_nfe(venda_id)
                        
                        if nfe_result.get('success'):
                            current_app.logger.info(
                                f"✅ NF-e emitida com sucesso para pedido {venda_id}: "
                                f"ID={nfe_result.get('nfe_id')}, "
                                f"Status={nfe_result.get('nfe_situacao')}"
                            )
                            return True
                        else:
                            current_app.logger.error(
                                f"❌ Falha ao emitir NF-e para pedido {venda_id}: "
                                f"{nfe_result.get('error')}"
                            )
                            return False
                    except Exception as nfe_error:
                        current_app.logger.error(
                            f"❌ Erro ao emitir NF-e para pedido {venda_id}: {nfe_error}",
                            exc_info=True
                        )
                        return False
                else:
                    current_app.logger.info(
                        f"ℹ️ Pedido {venda_id} está em 'Em andamento' e já tem NF-e associada."
                    )
                    return True
            
            # IMPORTANTE: Se está em "Em andamento", SEMPRE verificar e emitir NF-e
            # Isso deve acontecer ANTES de verificar se a situação mudou
            if is_em_andamento and not is_em_aberto:
                current_app.logger.info(
                    f"🚀 PEDIDO {venda_id} ESTÁ EM 'EM ANDAMENTO' (ID: {situacao_bling_id}) - VERIFICANDO E EMITINDO NF-e AGORA!"
                )
                verificar_e_emitir_nfe()
            
            # Verificar se a situação mudou
            if situacao_atual_id is not None and situacao_bling_id == situacao_atual_id:
                # Se não está em "Em andamento", apenas retornar
                # (A emissão de NF-e já foi verificada acima se estiver em "Em andamento")
                current_app.logger.info(
                    f"ℹ️ Situação não mudou para pedido {venda_id}: {situacao_bling_id} ({situacao_bling_nome or 'sem nome'})"
                )
                return jsonify({
                    "status": "ok",
                    "message": "Situação não mudou"
                }), 200
            
            # Atualizar situação e status do pedido usando o serviço de situação
            from ..services.bling_situacao_service import update_pedido_situacao
            
            atualizado = update_pedido_situacao(
                venda_id=venda_id,
                bling_situacao_id=situacao_bling_id,
                bling_situacao_nome=situacao_bling_nome
            )
            
            if atualizado:
                # Sincronizar status da tabela orders com o novo status da venda
                try:
                    sync_order_status_from_venda(venda_id)
                    current_app.logger.info(f"✅ Status da tabela orders sincronizado para venda {venda_id}")
                except Exception as sync_error:
                    current_app.logger.warning(f"⚠️ Erro ao sincronizar status do order: {sync_error}")
                
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
                current_app.logger.info(f"   Situação Bling: {situacao_atual_id or '(desconhecida)'} → {situacao_bling_id}")
                current_app.logger.info(f"   Nome Situação: {situacao_bling_nome}")
                current_app.logger.info(f"   Status Site: {status_atual} → {novo_status}")
                current_app.logger.info("=" * 80)
                
                # Verificar se mudou para "Logística" e decrementar estoque
                situacao_nome_lower = (situacao_bling_nome or '').lower() if situacao_bling_nome else ''
                is_logistica = (
                    'logística' in situacao_nome_lower or 
                    'logistica' in situacao_nome_lower or
                    novo_status == 'pronto_envio'
                )
                
                if is_logistica:
                    current_app.logger.info(
                        f"🚚 Pedido {venda_id} mudou para 'Logística' (ID: {situacao_bling_id}). "
                        f"Decrementando estoque local..."
                    )
                    # Decrementar estoque quando pedido for para Logística
                    try:
                        cur.execute("""
                            SELECT produto_id, quantidade
                            FROM itens_venda
                            WHERE venda_id = %s
                        """, (venda_id,))
                        
                        itens = cur.fetchall()
                        estoque_decrementado = False
                        
                        for item in itens:
                            produto_id = item[0]
                            quantidade = item[1]
                            
                            cur.execute("""
                                UPDATE produtos 
                                SET estoque = estoque - %s,
                                    updated_at = NOW()
                                WHERE id = %s AND estoque >= %s
                            """, (quantidade, produto_id, quantidade))
                            
                            if cur.rowcount > 0:
                                estoque_decrementado = True
                                current_app.logger.info(
                                    f"✅ Estoque decrementado para produto {produto_id}: -{quantidade} unidades"
                                )
                            else:
                                current_app.logger.warning(
                                    f"⚠️ Não foi possível decrementar estoque para produto {produto_id} "
                                    f"(estoque insuficiente ou produto não encontrado)"
                                )
                        
                        if estoque_decrementado:
                            conn.commit()
                            current_app.logger.info(
                                f"✅ Estoque local decrementado para pedido {venda_id} quando mudou para 'Logística'"
                            )
                        else:
                            conn.rollback()
                            current_app.logger.warning(
                                f"⚠️ Nenhum estoque foi decrementado para pedido {venda_id}"
                            )
                    except Exception as estoque_error:
                        conn.rollback()
                        current_app.logger.error(
                            f"❌ Erro ao decrementar estoque para pedido {venda_id}: {estoque_error}",
                            exc_info=True
                        )
                        # Não falhar a atualização de situação por erro no estoque
                
                # Se mudou para "Em andamento", verificar se precisa emitir NF-e
                if is_em_andamento and not is_em_aberto:
                    current_app.logger.info(
                        f"📄 Pedido {venda_id} mudou para 'Em andamento' (ID: {situacao_bling_id}). "
                        f"Emitindo NF-e agora..."
                    )
                    resultado_nfe = verificar_e_emitir_nfe()
                    if resultado_nfe:
                        current_app.logger.info(f"✅ NF-e processada com sucesso para pedido {venda_id}")
                    else:
                        current_app.logger.warning(f"⚠️ NF-e não foi emitida para pedido {venda_id} (já existe ou erro)")
                else:
                    current_app.logger.info(
                        f"ℹ️ Pedido {venda_id} não está em 'Em andamento' ou está em 'Em aberto'. "
                        f"is_em_andamento={is_em_andamento}, is_em_aberto={is_em_aberto}"
                    )
                
                # Se mudou para "Pronto para entrega" (ID 718557), atualizar transportadora
                is_pronto_entrega = (
                    situacao_bling_id == 718557 or
                    'pronto para entrega' in situacao_nome_lower
                )
                
                if is_pronto_entrega:
                    current_app.logger.info(
                        f"🚚 Pedido {venda_id} mudou para 'Pronto para entrega' (ID: {situacao_bling_id}). "
                        f"Atualizando transportadora..."
                    )
                    
                    try:
                        # Buscar dados da transportadora do pedido no Bling
                        from ..services.bling_order_service import get_bling_order_by_local_id
                        from ..services.bling_api_service import make_bling_api_request
                        
                        bling_order = get_bling_order_by_local_id(venda_id)
                        if bling_order:
                            bling_pedido_id = bling_order.get('bling_pedido_id')
                            if bling_pedido_id:
                                # Buscar pedido completo no Bling para obter dados da transportadora
                                response_pedido = make_bling_api_request(
                                    'GET',
                                    f'/pedidos/vendas/{bling_pedido_id}'
                                )
                                
                                if response_pedido.status_code == 200:
                                    pedido_data = response_pedido.json().get('data', {})
                                    
                                    # Extrair dados da transportadora do pedido Bling
                                    transportadora_data = pedido_data.get('transportadora', {})
                                    if transportadora_data:
                                        transportadora_nome = transportadora_data.get('nome')
                                        transportadora_cnpj = transportadora_data.get('cnpj')
                                        
                                        if transportadora_nome:
                                            # Atualizar transportadora no banco local
                                            cur.execute("""
                                                UPDATE vendas
                                                SET transportadora_nome = %s,
                                                    transportadora_cnpj = %s,
                                                    updated_at = NOW()
                                                WHERE id = %s
                                            """, (transportadora_nome, transportadora_cnpj, venda_id))
                                            
                                            conn.commit()
                                            
                                            current_app.logger.info(
                                                f"✅ Transportadora atualizada para pedido {venda_id}: "
                                                f"{transportadora_nome} (CNPJ: {transportadora_cnpj or 'N/A'})"
                                            )
                                        else:
                                            current_app.logger.warning(
                                                f"⚠️ Pedido {venda_id} em 'Pronto para entrega' mas sem nome de transportadora no Bling"
                                            )
                                    else:
                                        current_app.logger.warning(
                                            f"⚠️ Pedido {venda_id} em 'Pronto para entrega' mas sem dados de transportadora no Bling"
                                        )
                                else:
                                    current_app.logger.warning(
                                        f"⚠️ Erro ao buscar pedido {bling_pedido_id} no Bling para atualizar transportadora: "
                                        f"HTTP {response_pedido.status_code}"
                                    )
                            else:
                                current_app.logger.warning(
                                    f"⚠️ Pedido {venda_id} não tem bling_pedido_id para buscar transportadora"
                                )
                        else:
                            current_app.logger.warning(
                                f"⚠️ Pedido {venda_id} não encontrado na tabela bling_pedidos"
                            )
                    except Exception as transportadora_error:
                        conn.rollback()
                        current_app.logger.error(
                            f"❌ Erro ao atualizar transportadora para pedido {venda_id}: {transportadora_error}",
                            exc_info=True
                        )
                        # Não falhar a atualização de situação por erro na transportadora
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
        # O Bling pode enviar os dados diretamente ou dentro de um objeto 'invoice'
        nfe_data = data.get('invoice') or data  # Tentar 'invoice' primeiro, depois dados diretos
        
        nfe_id = nfe_data.get('id') or data.get('id')
        nfe_situacao = nfe_data.get('situacao') or data.get('situacao')  # 1 = Autorizada, outros valores = outras situações
        nfe_numero = nfe_data.get('numero') or data.get('numero')
        nfe_tipo = nfe_data.get('tipo') or data.get('tipo')  # 0 = NF-e (Modelo 55), 1 = NFC-e
        
        current_app.logger.info(
            f"📋 Dados extraídos da NF-e: ID={nfe_id}, Situação={nfe_situacao}, "
            f"Número={nfe_numero}, Tipo={nfe_tipo}"
        )
        
        if not nfe_id:
            current_app.logger.warning(
                f"Webhook de nota fiscal sem ID. Event: {event}, "
                f"Dados recebidos: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}"
            )
            return jsonify({
                "status": "ok",
                "message": "Webhook sem ID da nota fiscal, ignorado"
            }), 200
        
        # Buscar pedido relacionado à nota fiscal
        from ..services.bling_order_service import get_order_by_nfe_id
        
        pedido_info = get_order_by_nfe_id(nfe_id)
        
        # Se não encontrou pelo ID, tentar buscar pelo número da NF-e (normalizado)
        if not pedido_info and nfe_numero:
            current_app.logger.info(
                f"⚠️ NF-e não encontrada pelo ID {nfe_id}. Tentando buscar pelo número {nfe_numero}..."
            )
            conn_temp = get_db()
            cur_temp = conn_temp.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                # Normalizar número da NF-e (remover zeros à esquerda e converter para string)
                nfe_numero_normalizado = str(int(nfe_numero)) if nfe_numero else None
                nfe_numero_com_zeros = str(nfe_numero).zfill(9)  # Formato com zeros: 000000004
                
                # Tentar buscar com número normalizado e com zeros
                # O número pode estar salvo como string ou inteiro
                cur_temp.execute("""
                    SELECT venda_id, bling_pedido_id
                    FROM bling_pedidos
                    WHERE (nfe_numero::text = %s 
                       OR nfe_numero::text = %s
                       OR nfe_numero::text = %s
                       OR nfe_numero::text = %s
                       OR LPAD(nfe_numero::text, 9, '0') = %s)
                    LIMIT 1
                """, (
                    nfe_numero_normalizado, 
                    nfe_numero_com_zeros, 
                    nfe_numero, 
                    str(nfe_numero),
                    nfe_numero_com_zeros
                ))
                pedido_temp = cur_temp.fetchone()
                if pedido_temp:
                    pedido_info = {
                        'venda_id': pedido_temp['venda_id'],
                        'bling_pedido_id': pedido_temp['bling_pedido_id']
                    }
                    current_app.logger.info(
                        f"✅ Pedido encontrado pelo número da NF-e: {pedido_info['venda_id']}"
                    )
            except Exception as e:
                current_app.logger.error(f"Erro ao buscar pedido pelo número da NF-e: {e}")
            finally:
                cur_temp.close()
        
        # Se ainda não encontrou, tentar buscar pelo contato do pedido (se disponível)
        if not pedido_info:
            contato_id = data.get('contato', {}).get('id') if isinstance(data.get('contato'), dict) else None
            if contato_id:
                current_app.logger.info(
                    f"⚠️ Tentando buscar pedido pelo contato {contato_id} da NF-e..."
                )
                conn_temp = get_db()
                cur_temp = conn_temp.cursor(cursor_factory=psycopg2.extras.DictCursor)
                try:
                    # Buscar pedido pelo contato do Bling (cliente)
                    # Buscar pedido Bling mais recente do contato e depois encontrar pedido local
                    from ..services.bling_api_service import make_bling_api_request
                    try:
                        # Buscar pedidos do contato no Bling
                        response = make_bling_api_request(
                            'GET',
                            '/pedidos/vendas',
                            params={
                                'contato': contato_id,
                                'limite': 10
                            }
                        )
                        if response.status_code == 200:
                            pedidos_data = response.json().get('data', [])
                            # Procurar pedido mais recente que ainda não tem NF-e ou tem esta NF-e
                            for pedido_bling in pedidos_data:
                                pedido_bling_id = pedido_bling.get('id')
                                nfe_pedido = pedido_bling.get('notaFiscal', {})
                                nfe_pedido_id = nfe_pedido.get('id') if isinstance(nfe_pedido, dict) else None
                                
                                # Se este pedido tem esta NF-e ou não tem NF-e ainda
                                if nfe_pedido_id == nfe_id or nfe_pedido_id is None:
                                    # Buscar pedido local pelo bling_pedido_id
                                    cur_temp.execute("""
                                        SELECT venda_id, bling_pedido_id
                                        FROM bling_pedidos
                                        WHERE bling_pedido_id = %s
                                        LIMIT 1
                                    """, (pedido_bling_id,))
                                    pedido_local = cur_temp.fetchone()
                                    if pedido_local:
                                        pedido_info = {
                                            'venda_id': pedido_local['venda_id'],
                                            'bling_pedido_id': pedido_local['bling_pedido_id']
                                        }
                                        current_app.logger.info(
                                            f"✅ Pedido encontrado pelo contato via API Bling: {pedido_info['venda_id']}"
                                        )
                                        break
                    except Exception as api_error:
                        current_app.logger.warning(f"Erro ao buscar pedido via API Bling: {api_error}")
                    
                    # Se não encontrou via API, tentar buscar pedido local mais recente sem NF-e
                    if not pedido_info:
                        cur_temp.execute("""
                            SELECT v.id as venda_id, bp.bling_pedido_id
                            FROM vendas v
                            JOIN bling_pedidos bp ON v.id = bp.venda_id
                            WHERE bp.bling_nfe_id IS NULL
                            ORDER BY v.id DESC
                            LIMIT 5
                        """)
                        pedidos_sem_nfe = cur_temp.fetchall()
                        # Tentar encontrar pedido do mesmo contato verificando via API
                        for pedido_candidate in pedidos_sem_nfe:
                            try:
                                pedido_bling_id_candidate = pedido_candidate['bling_pedido_id']
                                response = make_bling_api_request(
                                    'GET',
                                    f'/pedidos/vendas/{pedido_bling_id_candidate}'
                                )
                                if response.status_code == 200:
                                    pedido_data = response.json().get('data', {})
                                    contato_pedido = pedido_data.get('contato', {})
                                    contato_pedido_id = contato_pedido.get('id') if isinstance(contato_pedido, dict) else None
                                    if contato_pedido_id == contato_id:
                                        pedido_info = {
                                            'venda_id': pedido_candidate['venda_id'],
                                            'bling_pedido_id': pedido_bling_id_candidate
                                        }
                                        current_app.logger.info(
                                            f"✅ Pedido encontrado pelo contato (verificação via API): {pedido_info['venda_id']}"
                                        )
                                        break
                            except:
                                continue
                    pedido_temp = cur_temp.fetchone()
                    if pedido_temp:
                        pedido_info = {
                            'venda_id': pedido_temp['venda_id'],
                            'bling_pedido_id': pedido_temp['bling_pedido_id']
                        }
                        current_app.logger.info(
                            f"✅ Pedido encontrado pelo contato: {pedido_info['venda_id']}"
                        )
                except Exception as e:
                    current_app.logger.error(f"Erro ao buscar pedido pelo contato: {e}")
                finally:
                    cur_temp.close()
        
        if not pedido_info:
            # Tentar buscar pelo pedido Bling diretamente usando o contato
            # Se a NF-e foi criada mas não foi salva no banco ainda, podemos tentar encontrar o pedido
            contato_id = data.get('contato', {}).get('id') if isinstance(data.get('contato'), dict) else None
            if contato_id:
                current_app.logger.info(
                    f"⚠️ Tentando buscar pedido mais recente do contato {contato_id} para vincular NF-e..."
                )
                conn_temp = get_db()
                cur_temp = conn_temp.cursor(cursor_factory=psycopg2.extras.DictCursor)
                try:
                    # Buscar pedido mais recente do cliente que ainda não tem NF-e
                    # Usar API do Bling para buscar pedidos do contato
                    from ..services.bling_api_service import make_bling_api_request
                    try:
                        response = make_bling_api_request(
                            'GET',
                            '/pedidos/vendas',
                            params={
                                'contato': contato_id,
                                'limite': 10
                            }
                        )
                        if response.status_code == 200:
                            pedidos_data = response.json().get('data', [])
                            for pedido_bling in pedidos_data:
                                pedido_bling_id = pedido_bling.get('id')
                                nfe_pedido = pedido_bling.get('notaFiscal', {})
                                # Se pedido não tem NF-e ainda
                                if not nfe_pedido or not nfe_pedido.get('id'):
                                    # Buscar pedido local
                                    cur_temp.execute("""
                                        SELECT venda_id, bling_pedido_id
                                        FROM bling_pedidos
                                        WHERE bling_pedido_id = %s
                                        LIMIT 1
                                    """, (pedido_bling_id,))
                                    pedido_local = cur_temp.fetchone()
                                    if pedido_local:
                                        pedido_info = {
                                            'venda_id': pedido_local['venda_id'],
                                            'bling_pedido_id': pedido_local['bling_pedido_id']
                                        }
                                        break
                    except Exception as api_error:
                        current_app.logger.warning(f"Erro ao buscar pedido via API Bling: {api_error}")
                    pedido_temp = cur_temp.fetchone()
                    if pedido_temp:
                        pedido_info = {
                            'venda_id': pedido_temp['venda_id'],
                            'bling_pedido_id': pedido_temp['bling_pedido_id']
                        }
                        current_app.logger.info(
                            f"✅ Pedido encontrado pelo contato (sem NF-e ainda): {pedido_info['venda_id']}. "
                            f"Vinculando NF-e {nfe_id} a este pedido."
                        )
                        # Salvar a NF-e neste pedido
                        cur_temp.execute("""
                            UPDATE bling_pedidos
                            SET bling_nfe_id = %s,
                                nfe_numero = %s,
                                nfe_status = %s,
                                updated_at = NOW()
                            WHERE venda_id = %s
                        """, (nfe_id, nfe_numero, f'SITUACAO_{nfe_situacao}', pedido_info['venda_id']))
                        conn_temp.commit()
                except Exception as e:
                    current_app.logger.error(f"Erro ao buscar/vincular pedido pelo contato: {e}")
                    conn_temp.rollback()
                finally:
                    cur_temp.close()
        
        if not pedido_info:
            current_app.logger.warning(
                f"Nota fiscal {nfe_id} (número: {nfe_numero}) não encontrada em nenhum pedido local. "
                f"Pode ser uma nota criada diretamente no Bling ou ainda não sincronizada."
            )
            # Não retornar erro, apenas logar - pode ser uma NF-e criada diretamente no Bling
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
                # Buscar situação real da NF-e no Bling para confirmar
                # O Bling pode usar códigos diferentes ou o webhook pode estar desatualizado
                situacao_real = None
                nfe_data_real = {}
                nfe_chave_acesso_real = None
                try:
                    from ..services.bling_api_service import make_bling_api_request
                    nfe_response = make_bling_api_request('GET', f'/nfe/{nfe_id}')
                    if nfe_response.status_code == 200:
                        nfe_data_real = nfe_response.json().get('data', {})
                        situacao_real = nfe_data_real.get('situacao')
                        nfe_chave_acesso_real = nfe_data_real.get('chaveAcesso') or nfe_data_real.get('chave_acesso')
                        current_app.logger.info(
                            f"📋 Situação real da NF-e {nfe_id} no Bling: {situacao_real} "
                            f"(webhook informou: {nfe_situacao}), "
                            f"Chave de acesso: {'Sim' if nfe_chave_acesso_real else 'Não'}"
                        )
                except Exception as busca_error:
                    current_app.logger.warning(f"Erro ao buscar situação real da NF-e: {busca_error}")
                
                # Usar situação real se disponível, senão usar do webhook
                situacao_final = situacao_real if situacao_real is not None else nfe_situacao
                
                # Mapear situações do Bling conforme documentação oficial:
                # 1 = Pendente, 2 = Cancelada, 3 = Aguardando recibo
                # 4 = Rejeitada, 5 = Autorizada, 6 = Emitida DANFE
                # 7 = Registrada, 8 = Aguardando protocolo, 9 = Denegada
                # 10 = Consulta situação, 11 = Bloqueada
                situacao_map = {
                    1: 'PENDENTE',
                    2: 'CANCELADA',
                    3: 'AGUARDANDO_RECIBO',
                    4: 'REJEITADA',
                    5: 'AUTORIZADA',  # Situação 5 = AUTORIZADA
                    6: 'EMITIDA_DANFE',  # Situação 6 = Emitida DANFE
                    7: 'REGISTRADA',
                    8: 'AGUARDANDO_PROTOCOLO',
                    9: 'DENEGADA',
                    10: 'CONSULTA_SITUACAO',
                    11: 'BLOQUEADA'
                }
                nfe_status_str = situacao_map.get(situacao_final, f'DESCONHECIDA_{situacao_final}')
                
                current_app.logger.info(
                    f"📋 Situação da NF-e {nfe_id}: {situacao_final} ({nfe_status_str}) "
                    f"(webhook: {nfe_situacao}, real: {situacao_real})"
                )
                
                # Verificar se situação mudou para Autorizada
                # Situação 1 = PENDENTE (estado inicial, ainda não processada)
                # Situação 5 = AUTORIZADA (nota autorizada pelo SEFAZ)
                # Situação 6 = EMITIDA_DANFE (DANFE foi emitido)
                # Situação 7 = REGISTRADA (nota registrada)
                # Se a NF-e tem chave de acesso, provavelmente está autorizada mesmo com situação diferente
                nfe_chave_acesso = (
                    nfe_data.get('chaveAcesso') or 
                    nfe_data.get('chave_acesso') or 
                    data.get('chaveAcesso') or 
                    data.get('chave_acesso') or
                    nfe_chave_acesso_real
                )
                
                # Considerar autorizada se:
                # 1. Situação é 5 (AUTORIZADA) - nota autorizada pelo SEFAZ
                # 2. Situação é 6 (EMITIDA_DANFE) - DANFE foi emitido (nota autorizada)
                # 3. Situação é 7 (REGISTRADA) - nota registrada (autorizada)
                # 4. Tem chave de acesso válida (44 dígitos) - independente da situação
                is_autorizada = (
                    situacao_final == 5 or  # Situação 5 = AUTORIZADA
                    situacao_final == 6 or  # Situação 6 = EMITIDA_DANFE (nota autorizada)
                    situacao_final == 7 or  # Situação 7 = REGISTRADA (nota autorizada)
                    (nfe_chave_acesso and len(str(nfe_chave_acesso).strip()) == 44)  # Chave de acesso válida (44 dígitos)
                )
                
                if nfe_chave_acesso:
                    current_app.logger.info(
                        f"🔑 NF-e {nfe_id} possui chave de acesso: {str(nfe_chave_acesso)[:20]}... "
                        f"(situação: {situacao_final}, tamanho: {len(str(nfe_chave_acesso).strip())})"
                    )
                else:
                    current_app.logger.info(
                        f"⚠️ NF-e {nfe_id} não possui chave de acesso (situação: {situacao_final})"
                    )
                
                # Log detalhado da verificação
                current_app.logger.info(
                    f"🔍 Verificando autorização da NF-e {nfe_id} para pedido {venda_id}:"
                )
                current_app.logger.info(
                    f"   - Situação final: {situacao_final} ({nfe_status_str})"
                )
                current_app.logger.info(
                    f"   - Tem chave de acesso: {'Sim' if nfe_chave_acesso else 'Não'}"
                )
                if nfe_chave_acesso:
                    current_app.logger.info(
                        f"   - Tamanho da chave: {len(str(nfe_chave_acesso).strip())} dígitos"
                    )
                current_app.logger.info(
                    f"   - Situação 5 (AUTORIZADA): {'Sim' if situacao_final == 5 else 'Não'}"
                )
                current_app.logger.info(
                    f"   - Situação 6 (EMITIDA_DANFE): {'Sim' if situacao_final == 6 else 'Não'}"
                )
                current_app.logger.info(
                    f"   - Situação 7 (REGISTRADA): {'Sim' if situacao_final == 7 else 'Não'}"
                )
                current_app.logger.info(
                    f"   - Chave válida (44 dígitos): {'Sim' if (nfe_chave_acesso and len(str(nfe_chave_acesso).strip()) == 44) else 'Não'}"
                )
                current_app.logger.info(
                    f"   - RESULTADO: {'✅ AUTORIZADA' if is_autorizada else '❌ NÃO AUTORIZADA'}"
                )
                
                if is_autorizada:
                    current_app.logger.info(
                        f"✅ NF-e {nfe_id} AUTORIZADA pelo SEFAZ para pedido {venda_id} "
                        f"(situação: {situacao_final} - {nfe_status_str})"
                    )
                    
                    # Verificar situação atual do pedido no Bling antes de mover para Logística
                    # O Bling move automaticamente para "Atendido" quando emite a NF-e
                    # Precisamos mover de "Atendido" para "Logística" quando a NF-e for aprovada
                    from ..services.bling_order_service import get_bling_order_by_local_id
                    from ..services.bling_api_service import make_bling_api_request
                    
                    bling_order = get_bling_order_by_local_id(venda_id)
                    situacao_atual_id = None
                    
                    if bling_order:
                        bling_pedido_id = bling_order['bling_pedido_id']
                        
                        try:
                            # Buscar situação atual do pedido no Bling
                            response_pedido = make_bling_api_request(
                                'GET',
                                f'/pedidos/vendas/{bling_pedido_id}'
                            )
                            
                            if response_pedido.status_code == 200:
                                pedido_data = response_pedido.json().get('data', {})
                                situacao_atual = pedido_data.get('situacao', {})
                                
                                if isinstance(situacao_atual, dict):
                                    situacao_atual_id = situacao_atual.get('id')
                                    situacao_atual_nome = situacao_atual.get('nome', '')
                                elif isinstance(situacao_atual, (int, str)):
                                    situacao_atual_id = int(situacao_atual)
                                    situacao_atual_nome = ''
                                
                                current_app.logger.info(
                                    f"📋 Situação atual do pedido {venda_id} no Bling: "
                                    f"ID {situacao_atual_id} ({situacao_atual_nome or 'sem nome'})"
                                )
                                
                                # Se está em "Atendido" (ID 9), mover para "Logística"
                                if situacao_atual_id == 9:
                                    current_app.logger.info(
                                        f"🔄 Pedido {venda_id} está em 'Atendido' (comportamento padrão do Bling). "
                                        f"Movendo para 'Logística' após aprovação da NF-e pelo SEFAZ..."
                                    )
                                else:
                                    current_app.logger.info(
                                        f"ℹ️ Pedido {venda_id} está em situação {situacao_atual_id} "
                                        f"({situacao_atual_nome or 'sem nome'}). "
                                        f"Movendo para 'Logística' mesmo assim..."
                                    )
                        except Exception as e:
                            current_app.logger.warning(
                                f"⚠️ Erro ao verificar situação atual do pedido: {e}. "
                                f"Continuando com movimento para Logística..."
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
                        SET status_pedido = 'nfe_autorizada'
                        WHERE id = %s
                    """, (venda_id,))
                    
                    conn.commit()
                    
                    # Sincronizar status da tabela orders
                    try:
                        sync_order_status_from_venda(venda_id)
                    except Exception as sync_error:
                        current_app.logger.warning(f"Erro ao sincronizar status do order: {sync_error}")
                    
                    current_app.logger.info(
                        f"✅ Status do pedido {venda_id} atualizado para 'nfe_autorizada'"
                    )
                    
                    # Bling criará remessa automaticamente quando pedido for movido para Logística
                    current_app.logger.info(
                        f"ℹ️ Bling criará remessa automaticamente quando pedido {venda_id} for movido para Logística"
                    )
                    
                    # Mudar situação do pedido no Bling para "Logística"
                    current_app.logger.info(
                        f"🚚 Iniciando processo para mover pedido {venda_id} para 'Logística' no Bling..."
                    )
                    from ..services.bling_order_service import update_order_situacao_to_logistica
                    
                    logistica_result = update_order_situacao_to_logistica(venda_id)
                    
                    current_app.logger.info(
                        f"📋 Resultado de update_order_situacao_to_logistica para venda {venda_id}: "
                        f"{json.dumps(logistica_result, indent=2, ensure_ascii=False)}"
                    )
                    
                    if logistica_result.get('success'):
                        current_app.logger.info(
                            f"✅ Pedido {venda_id} movido para 'Logística' no Bling. "
                            f"Bling irá automaticamente: decrementar estoque, etc."
                        )
                        
                        # Atualizar status para pronto_envio após mudar para Logística
                        cur.execute("""
                            UPDATE vendas
                            SET status_pedido = 'pronto_envio'
                            WHERE id = %s
                        """, (venda_id,))
                        conn.commit()
                        
                        # Sincronizar status da tabela orders
                        try:
                            sync_order_status_from_venda(venda_id)
                        except Exception as sync_error:
                            current_app.logger.warning(f"Erro ao sincronizar status do order: {sync_error}")
                        
                        current_app.logger.info(
                            f"✅ Status do pedido {venda_id} atualizado para 'pronto_envio'"
                        )
                    else:
                        error_msg = logistica_result.get('error', 'Erro desconhecido')
                        current_app.logger.error(
                            f"❌ FALHA ao mover pedido {venda_id} para 'Logística' no Bling: {error_msg}"
                        )
                        current_app.logger.error(
                            f"📋 Detalhes completos do erro: {json.dumps(logistica_result, indent=2, ensure_ascii=False)}"
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
                    # Mapear situações conforme documentação oficial do Bling
                    situacao_map = {
                        1: 'PENDENTE',
                        2: 'CANCELADA',
                        3: 'AGUARDANDO_RECIBO',
                        4: 'REJEITADA',
                        5: 'AUTORIZADA',
                        6: 'EMITIDA_DANFE',
                        7: 'REGISTRADA',
                        8: 'AGUARDANDO_PROTOCOLO',
                        9: 'DENEGADA',
                        10: 'CONSULTA_SITUACAO',
                        11: 'BLOQUEADA'
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
        elif (event.startswith('consumer_invoice.') or 
              event.startswith('invoice.') or 
              event.startswith('nfe.')):
            # Processar evento de nota fiscal
            # Bling pode enviar: consumer_invoice.updated, invoice.updated, nfe.updated
            return process_nfe_webhook(webhook_data, event, event_id, data)
        elif event.startswith('product.'):
            # Processar evento de produto (estoque, atualização, etc.)
            # Eventos: product.created, product.updated, product.deleted
            # Por enquanto, apenas logar - estoque é sincronizado via webhook stock.*
            current_app.logger.info(f"📦 Evento de produto recebido: {event}")
            return jsonify({
                "status": "ok",
                "message": f"Evento de produto {event} recebido (processamento de estoque via stock.*)"
            }), 200
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
                    updated_at = NOW()
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
                    SET status_pedido = %s
                    WHERE id = %s
                """, (status_novo, venda_id))
                conn.commit()
                
                # Sincronizar status da tabela orders
                try:
                    sync_order_status_from_venda(venda_id)
                except Exception as sync_error:
                    current_app.logger.warning(f"Erro ao sincronizar status do order: {sync_error}")
                
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

