"""
API de Checkout - Processamento de Pedidos

ARQUITETURA DE PAGAMENTO:
========================
O webhook do PagBank é a ÚNICA fonte de verdade do status do pagamento.

REGRAS ARQUITETURAIS (NÃO NEGOCIAR):
- Pagamento só existe depois do webhook
- A resposta do /orders é apenas uma intenção de pagamento
- Webhook é assíncrono, idempotente e confiável
- IDs do PagBank são a chave de reconciliação
- Status inicial SEMPRE é PENDING/AWAITING_PAYMENT
- Backend nunca considera pagamento confirmado fora do webhook
- Frontend nunca valida pagamento, apenas faz polling

FLUXO OBRIGATÓRIO:
1. Checkout cria pedido no banco com status PENDING
2. Backend chama /orders do PagBank
3. Backend salva apenas IDs retornados (order_id, charge_id)
4. Backend NÃO confirma pagamento
5. Backend retorna apenas: public_token, método de pagamento, status inicial (PENDING)
6. Webhook recebe notificação e atualiza status final
"""
from flask import Blueprint, request, jsonify, current_app, session
from ..services import (
    create_order_and_items, create_payment_entry, get_order_status, 
    call_pagbank_api, create_pagbank_payload, get_db, get_cart_owner_info, get_or_create_cart,
    create_order as create_order_record
)
import psycopg2.extras
from ..services.user_service import get_user_by_firebase_uid

checkout_api_bp = Blueprint('checkout_api', __name__, url_prefix='/api/checkout')

@checkout_api_bp.route('/process', methods=['POST'])
def process_checkout():
    """
    Processa o checkout completo: valida carrinho, cria pedido e processa pagamento
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Dados da requisição ausentes"}), 400

        # 1. Validar dados de entrada
        if 'shipping_info' not in data:
            return jsonify({"erro": "Campo obrigatório ausente: shipping_info"}), 400
        
        if 'payment_details' not in data:
            return jsonify({"erro": "Campo obrigatório ausente: payment_details"}), 400

        shipping_info = data.get('shipping_info')
        payment_details = data.get('payment_details')
        fiscal_data = data.get('fiscal_data')
        
        # Extrair método de pagamento dos payment_details se não estiver no root
        payment_method = data.get('payment_method') or payment_details.get('payment_method_type', '').upper()
        if not payment_method:
            return jsonify({"erro": "Método de pagamento não especificado"}), 400
        
        # Extrair opção de frete dos dados de envio ou usar padrão
        shipping_option = data.get('shipping_option', {})
        if not shipping_option and shipping_info:
            # Tentar construir shipping_option a partir de shipping_info
            shipping_option = {
                'name': shipping_info.get('shipping_name', 'Frete Padrão'),
                'price': data.get('freight_value', 0),
                'deadline': shipping_info.get('shipping_deadline', '10-15 dias úteis')
            }
        
        # 2. Obter dados do usuário
        user_id = None
        user_data = None
        uid = session.get('uid')
        if uid:
            user_data = get_user_by_firebase_uid(uid)
            if user_data:
                user_id = user_data['id']

        # 3. Obter itens do carrinho
        error_response, cart_user_id, session_id = get_cart_owner_info()
        if error_response:
            return error_response

        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Obter carrinho
            cart_id = get_or_create_cart(user_id=cart_user_id, session_id=session_id)
            if not cart_id:
                return jsonify({"erro": "Não foi possível identificar o carrinho"}), 500

            # Buscar itens do carrinho com informações completas
            cur.execute("""
                SELECT 
                    ci.id AS cart_item_id,
                    ci.quantidade,
                    ci.preco_unitario_no_momento,
                    p.id AS produto_id,
                    p.codigo_sku,
                    np.nome AS nome_produto,
                    np.descricao AS descricao_produto,
                    e.nome AS estampa_nome,
                    t.nome AS tamanho_nome,
                    c.nome AS categoria_nome
                FROM carrinho_itens ci
                JOIN produtos p ON ci.produto_id = p.id
                JOIN nome_produto np ON p.nome_produto_id = np.id
                JOIN estampa e ON p.estampa_id = e.id
                JOIN tamanho t ON p.tamanho_id = t.id
                JOIN categorias c ON np.categoria_id = c.id
                WHERE ci.carrinho_id = %s
                ORDER BY ci.id ASC
            """, (cart_id,))
            
            cart_items_db = cur.fetchall()
            
            if not cart_items_db:
                return jsonify({"erro": "Carrinho vazio"}), 400

            # Preparar itens para o pedido
            cart_items = []
            total_value = 0.0
            
            for item in cart_items_db:
                subtotal = item[1] * float(item[2])  # quantidade * preco_unitario
                total_value += subtotal
                
                cart_items.append({
                    'produto_id': item[3],
                    'quantidade': item[1],
                    'preco_unitario': float(item[2]),
                    'subtotal': subtotal,
                    'nome_produto_snapshot': item[5],
                    'sku_produto_snapshot': item[4],
                    'detalhes_produto_snapshot': {
                        'descricao': item[6],
                        'estampa': item[7],
                        'tamanho': item[8],
                        'categoria': item[9]
                    }
                })

            # 4. Processar cupom se fornecido
            cupom_id = None
            discount_value = float(data.get('discount_value', 0))
            
            # Se houver desconto, buscar o cupom_id do código do cupom
            if discount_value > 0 and data.get('cupom_codigo'):
                cupom_codigo = data.get('cupom_codigo').strip().upper()
                cur.execute("SELECT id FROM cupom WHERE codigo = %s AND ativo = TRUE", (cupom_codigo,))
                cupom_result = cur.fetchone()
                if cupom_result:
                    cupom_id = cupom_result[0]
            
            # Calcular valores finais
            freight_value = float(shipping_option.get('price', data.get('freight_value', 0)))
            final_total = total_value + freight_value - discount_value
            
            # Validação básica
            if final_total <= 0:
                return jsonify({"erro": "Valor total do pedido deve ser maior que zero"}), 400
            
            # Validar valor mínimo para boleto (R$ 0,20)
            if payment_method == 'BOLETO' and final_total < 0.20:
                return jsonify({"erro": "O valor mínimo para pagamento via boleto é R$ 0,20"}), 400
            
            if not shipping_info.get('nome_recebedor'):
                return jsonify({"erro": "Nome do recebedor é obrigatório"}), 400
            
            if not shipping_info.get('cep'):
                return jsonify({"erro": "CEP é obrigatório"}), 400

            # 5. Obter IP e User-Agent
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
            user_agent = request.headers.get('User-Agent', '')

            # 6. Criar pedido no banco
            venda_id, codigo_pedido = create_order_and_items(
                user_id=user_id,
                cart_items=cart_items,
                shipping_info=shipping_info,
                total_value=final_total,
                freight_value=freight_value,
                discount_value=discount_value,
                client_ip=client_ip,
                user_agent=user_agent,
                fiscal_data=fiscal_data,
                cupom_id=cupom_id,
                shipping_option=shipping_option
            )

            # 7. Preparar dados do cliente
            customer_data = {
                'name': payment_details.get('customer_name', '') or shipping_info.get('nome_recebedor', ''),
                'email': payment_details.get('customer_email', '') or shipping_info.get('email', ''),
                'tax_id': payment_details.get('customer_cpf_cnpj', '') or payment_details.get('customer_tax_id', ''),
                'phone_area': payment_details.get('phone_area', '') or payment_details.get('customer_phone_area', '11'),
                'phone_number': payment_details.get('phone_number', '') or payment_details.get('customer_phone_number', '999999999')
            }
            
            # Validações de dados do cliente
            if not customer_data['name']:
                return jsonify({"erro": "Nome do cliente é obrigatório"}), 400
            
            if not customer_data['email'] or '@' not in customer_data['email']:
                return jsonify({"erro": "Email válido do cliente é obrigatório"}), 400
            
            # Limpar CPF/CNPJ (remover pontos, traços, barras)
            customer_data['tax_id'] = customer_data['tax_id'].replace('.', '').replace('-', '').replace('/', '')
            
            if not customer_data['tax_id'] or len(customer_data['tax_id']) < 11:
                return jsonify({"erro": "CPF/CNPJ do cliente é obrigatório e deve ter pelo menos 11 dígitos"}), 400

            # 8. Preparar dados do pagamento
            payment_data = {
                'payment_method': payment_method,
                'total_value': final_total,
                'freight_value': freight_value,
                'discount_value': discount_value
            }
            
            # Adicionar dados específicos do cartão se necessário
            if payment_method == 'CREDIT_CARD':
                # SEGURANÇA: O checkout principal NUNCA recebe dados completos do cartão diretamente.
                # Os dados são validados no endpoint isolado /api/pagbank/validate-card
                # e recuperados aqui apenas para envio ao PagBank (não são armazenados)
                
                # Validar que temos o card_id (obrigatório)
                card_id = payment_details.get('card_id', '')
                if not card_id:
                    conn.rollback()
                    return jsonify({
                        "erro": "Dados do cartão não validados. Por favor, tente novamente."
                    }), 400
                
                # Recuperar dados do cartão do cache temporário (uso único, será removido após)
                # Importação lazy para evitar importação circular
                try:
                    from ..api.pagbank import get_card_data_by_id
                    card_data = get_card_data_by_id(card_id)
                except ImportError:
                    # Fallback: tentar importar diretamente
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from blueprints.api.pagbank import get_card_data_by_id
                    card_data = get_card_data_by_id(card_id)
                if not card_data:
                    conn.rollback()
                    return jsonify({
                        "erro": "Dados do cartão expirados ou inválidos. Por favor, tente novamente."
                    }), 400
                
                # Usar CPF/CNPJ do portador do cartão, ou do cliente como fallback
                card_holder_cpf_cnpj = (
                    card_data.get('card_holder_cpf_cnpj', '') or 
                    payment_details.get('customer_cpf_cnpj', '') or
                    customer_data.get('tax_id', '')
                )
                
                # Limpar CPF/CNPJ do portador do cartão
                card_holder_cpf_cnpj_clean = str(card_holder_cpf_cnpj).replace('.', '').replace('-', '').replace('/', '').strip()
                
                # Preparar dados para envio ao PagBank (dados serão usados apenas uma vez e descartados)
                payment_data.update({
                    'card_number': card_data.get('card_number', ''),
                    'card_exp_month': card_data.get('card_exp_month', ''),
                    'card_exp_year': card_data.get('card_exp_year', ''),
                    'card_cvv': card_data.get('card_cvv', ''),
                    'card_holder_name': card_data.get('card_holder_name', '') or customer_data.get('name', ''),
                    'card_holder_cpf_cnpj': card_holder_cpf_cnpj_clean,
                    'installments': payment_details.get('installments', 1)
                })
                
                # Limpar dados do cartão da memória (já foram recuperados)
                # Os dados serão enviados ao PagBank e depois descartados

            # 9. Criar payload para PagBank
            pagbank_payload = create_pagbank_payload(
                cart_items=cart_items,
                shipping_info=shipping_info,
                payment_data=payment_data,
                customer_data=customer_data
            )

            # 10. Chamar API do PagBank
            api_token = current_app.config.get('PAGBANK_API_TOKEN')
            
            # Validar token antes de chamar a API
            if not api_token or api_token.strip() == '':
                current_app.logger.error("[PagBank] Token de API não configurado")
                conn.rollback()
                return jsonify({
                    "erro": "Configuração de pagamento inválida. Entre em contato com o suporte.",
                    "detalhes": "Token de API do PagBank não configurado"
                }), 500
            
            # Usar a URL do ambiente correto (sandbox ou production)
            pagbank_env = current_app.config.get('PAGBANK_ENVIRONMENT', 'sandbox')
            if pagbank_env == 'production':
                api_url = current_app.config.get('PAGBANK_PRODUCTION_API_URL')
            else:
                api_url = current_app.config.get('PAGBANK_SANDBOX_API_URL')
            
            # Validar URL da API
            if not api_url or api_url.strip() == '':
                current_app.logger.error("[PagBank] URL da API não configurada")
                conn.rollback()
                return jsonify({
                    "erro": "Configuração de pagamento inválida. Entre em contato com o suporte.",
                    "detalhes": "URL da API do PagBank não configurada"
                }), 500
            
            # Chamar API do PagBank - confiar apenas na resposta real
            try:
                current_app.logger.info(f"[PagBank] Chamando API: {api_url} (ambiente: {pagbank_env})")
                pagbank_response = call_pagbank_api(api_url, api_token, pagbank_payload)
                
                # Validar resposta do PagBank
                if not pagbank_response:
                    raise Exception("Resposta vazia do PagBank")
                
                # Verificar se a resposta contém charges ou qr_codes (para PIX)
                charges = pagbank_response.get('charges', [])
                qr_codes = pagbank_response.get('qr_codes', [])
                
                if not charges and not qr_codes:
                    raise Exception("Resposta do PagBank não contém informações de cobrança (charges) nem QR codes (qr_codes)")
                
                if qr_codes:
                    current_app.logger.info(f"[PagBank] Resposta recebida com sucesso. QR Codes PIX: {len(qr_codes)}")
                else:
                    current_app.logger.info(f"[PagBank] Resposta recebida com sucesso. Charges: {len(charges)}")
                
            except Exception as api_error:
                current_app.logger.error(f"[PagBank] Erro ao chamar API: {api_error}")
                import traceback
                current_app.logger.error(f"[PagBank] Traceback: {traceback.format_exc()}")
                
                # Rollback da transação do pedido
                conn.rollback()
                
                # Determinar mensagem de erro apropriada
                error_message = "Erro ao processar pagamento"
                error_details = str(api_error)
                
                # Mensagens específicas para diferentes tipos de erro
                if "Timeout" in str(api_error) or "timeout" in str(api_error).lower():
                    error_message = "Tempo de resposta do gateway de pagamento excedido. Tente novamente."
                    error_details = "O servidor de pagamento demorou muito para responder."
                elif "Connection" in str(api_error) or "conexão" in str(api_error).lower():
                    error_message = "Erro de conexão com o gateway de pagamento. Verifique sua conexão e tente novamente."
                    error_details = "Não foi possível conectar ao servidor de pagamento."
                elif "401" in str(api_error) or "Unauthorized" in str(api_error):
                    error_message = "Erro de autenticação no gateway de pagamento. Entre em contato com o suporte."
                    error_details = "Credenciais de pagamento inválidas."
                elif "400" in str(api_error) or "Bad Request" in str(api_error):
                    error_message = "Dados de pagamento inválidos. Verifique as informações e tente novamente."
                    error_details = "A requisição foi rejeitada pelo gateway de pagamento."
                elif "500" in str(api_error) or "Internal Server Error" in str(api_error):
                    error_message = "Erro interno no gateway de pagamento. Tente novamente em alguns instantes."
                    error_details = "O servidor de pagamento está temporariamente indisponível."
                
                # Retornar erro detalhado
                return jsonify({
                    "erro": error_message,
                    "detalhes": error_details if current_app.config.get('DEBUG', False) else None
                }), 500

            # 11. Salvar resposta do pagamento
            # IMPORTANTE: O status do pagamento NÃO é confirmado aqui.
            # Apenas salvamos os IDs do PagBank (order_id, charge_id) para reconciliação.
            # O webhook do PagBank é a ÚNICA fonte de verdade do status do pagamento.
            payment_id = create_payment_entry(venda_id, payment_data, pagbank_response)

            # 11.5. Criar registro na tabela orders com token público
            # REGRA ARQUITETURAL: Status inicial SEMPRE é PENDENTE.
            # A resposta do /orders é apenas uma intenção de pagamento, não confirmação.
            # Toda mudança de estado vem exclusivamente do webhook.
            initial_status = 'PENDENTE'
            
            order_record = create_order_record(venda_id, final_total, initial_status)
            public_token = order_record['public_token']

            # 12. Limpar carrinho após sucesso
            cur.execute("DELETE FROM carrinho_itens WHERE carrinho_id = %s", (cart_id,))
            conn.commit()

            # 13. Enviar email de confirmação de pedido (TEMPORARIAMENTE DESABILITADO)
            # TODO: Reativar quando SMTP estiver configurado
            # try:
            #     from ..services.email_service import send_order_confirmation_email
            #     
            #     # Preparar itens do pedido para o email
            #     order_items = []
            #     for item in cart_items:
            #         order_items.append({
            #             'nome': item.get('nome', 'Produto'),
            #             'quantidade': item.get('quantidade', 1),
            #             'preco': float(item.get('preco', 0))
            #         })
            #     
            #     # Obter nome do cliente
            #     customer_name = customer_data.get('name', shipping_info.get('nome_recebedor', 'Cliente'))
            #     customer_email = customer_data.get('email', shipping_info.get('email'))
            #     
            #     if customer_email:
            #         send_order_confirmation_email(
            #             user_email=customer_email,
            #             user_name=customer_name,
            #             order_number=codigo_pedido,
            #             order_total=final_total,
            #             order_items=order_items
            #         )
            # except Exception as email_error:
            #     current_app.logger.warning(f"Erro ao enviar email de confirmação de pedido: {email_error}")
            #     # Não falhar o checkout se o email falhar

            # 14. Preparar resposta
            response_data = {
                "success": True,
                "codigo_pedido": codigo_pedido,
                "venda_id": venda_id,
                "payment_id": payment_id,
                "public_token": public_token,  # Token público para acessar o pedido
                "total_value": final_total,
                "freight_value": freight_value,
                "discount_value": discount_value
            }

            # Adicionar dados específicos do pagamento da resposta do PagBank
            charges = pagbank_response.get('charges', [])
            qr_codes = pagbank_response.get('qr_codes', [])
            
            # Processar resposta baseado no tipo de pagamento
            if qr_codes and len(qr_codes) > 0:
                # PIX: os dados vêm em qr_codes no nível raiz
                qr_code = qr_codes[0]
                links = qr_code.get('links', [])
                
                if links:
                    # Buscar link do QR code PNG
                    qr_code_link = None
                    for link in links:
                        if link.get('rel') == 'QRCODE.PNG':
                            qr_code_link = link.get('href', '')
                            break
                        elif link.get('rel') == 'QRCODE.BASE64' and not qr_code_link:
                            qr_code_link = link.get('href', '')
                    
                    # Se não encontrou link específico, usar o primeiro
                    if not qr_code_link and links:
                        qr_code_link = links[0].get('href', '')
                    
                    response_data.update({
                        'payment_method_type': 'pix',
                        'pix_qr_code_link': qr_code_link,
                        'pix_qr_code_text': qr_code.get('text', ''),
                        'pix_qr_code': qr_code.get('text', '')  # Backup
                    })
                else:
                    # Tentar estrutura alternativa
                    response_data.update({
                        'payment_method_type': 'pix',
                        'pix_qr_code_link': qr_code.get('href', ''),
                        'pix_qr_code_text': qr_code.get('text', ''),
                        'pix_qr_code': qr_code.get('text', '')
                    })
                    
            elif charges and len(charges) > 0:
                # CREDIT_CARD ou BOLETO: os dados vêm em charges
                charge = charges[0]
                payment_method_type = charge.get('payment_method', {}).get('type', '').upper()
                
                if payment_method_type == 'PIX':
                    # PIX dentro de charges (estrutura alternativa - não esperada, mas tratamos)
                    pix_data = charge.get('payment_method', {}).get('pix', {})
                    qr_codes_in_charge = pix_data.get('qr_codes', [])
                    if not qr_codes_in_charge:
                        qr_codes_in_charge = pix_data.get('qr_code', [])
                    
                    if qr_codes_in_charge and len(qr_codes_in_charge) > 0:
                        qr_code = qr_codes_in_charge[0]
                        links = qr_code.get('links', [])
                        if links:
                            response_data.update({
                                'payment_method_type': 'pix',
                                'pix_qr_code_link': links[0].get('href', ''),
                                'pix_qr_code_text': qr_code.get('text', ''),
                                'pix_qr_code': qr_code.get('text', '')  # Backup
                            })
                        else:
                            response_data.update({
                                'payment_method_type': 'pix',
                                'pix_qr_code_link': qr_code.get('href', ''),
                                'pix_qr_code_text': qr_code.get('text', '')
                            })
                    else:
                        current_app.logger.error(f"[PagBank] Estrutura de resposta PIX inválida: {pix_data}")
                        conn.rollback()
                        return jsonify({
                            "erro": "Resposta inválida do gateway de pagamento. Tente novamente.",
                            "detalhes": "A resposta do PagBank não contém QR Code PIX válido"
                        }), 500
                
                elif payment_method_type == 'BOLETO':
                    boleto_data = charge.get('payment_method', {}).get('boleto', {})
                    
                    # Os links do boleto vêm em charges.links, não em boleto.links
                    charge_links = charge.get('links', [])
                    
                    # Tentar também em boleto_data.links como fallback
                    boleto_links = boleto_data.get('links', [])
                    
                    # Usar links do charge primeiro, depois do boleto
                    all_links = charge_links if charge_links else boleto_links
                    
                    # Buscar código de barras (pode ser barcode ou formatted_barcode)
                    barcode = None
                    formatted_barcode = None
                    
                    if isinstance(boleto_data.get('barcode'), dict):
                        barcode = boleto_data.get('barcode', {}).get('content', '')
                    elif boleto_data.get('barcode'):
                        barcode = boleto_data.get('barcode', '')
                    
                    if boleto_data.get('formatted_barcode'):
                        formatted_barcode = boleto_data.get('formatted_barcode', '')
                    
                    # Usar formatted_barcode se disponível, senão usar barcode
                    barcode_to_use = formatted_barcode if formatted_barcode else barcode
                    
                    response_data.update({
                        'payment_method_type': 'boleto',
                        'boleto_link': all_links[0].get('href', '') if all_links else '',
                        'boleto_barcode': barcode_to_use or '',
                        'boleto_formatted_barcode': formatted_barcode or '',
                        'boleto_expires_at': boleto_data.get('due_date', '')
                    })
                    
                elif payment_method_type == 'CREDIT_CARD':
                    # IMPORTANTE: Não consideramos o status da resposta como confirmação.
                    # O status retornado aqui é apenas informativo.
                    # O webhook do PagBank é a única fonte de verdade.
                    status = charge.get('status', '').lower()
                    response_data.update({
                        'payment_method_type': 'credit_card',
                        'installments': charge.get('installments', 1)
                        # Não incluímos status ou payment_approved - webhook é a fonte de verdade
                    })

            current_app.logger.info(f"Checkout processado com sucesso: {codigo_pedido}")
            
            # Log detalhado da resposta
            current_app.logger.info(f"Response data: {response_data}")
            
            return jsonify(response_data), 200

        except Exception as e:
            import traceback
            conn.rollback()
            error_trace = traceback.format_exc()
            current_app.logger.error(f"Erro no processamento do checkout: {e}")
            current_app.logger.error(f"Traceback: {error_trace}")
            
            # Retornar erro detalhado em desenvolvimento
            error_message = str(e)
            if current_app.config.get('DEBUG', False):
                return jsonify({
                    "erro": "Erro interno ao processar checkout",
                    "detalhes": error_message,
                    "traceback": error_trace
                }), 500
            else:
                return jsonify({"erro": "Erro interno ao processar checkout", "detalhes": error_message}), 500
        finally:
            if cur:
                cur.close()

    except Exception as e:
        current_app.logger.error(f"Erro na API de checkout: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@checkout_api_bp.route('/status/<string:codigo_pedido>', methods=['GET'])
def get_order_full_status(codigo_pedido):
    """
    Retorna o status completo de um pedido
    """
    try:
        order_status = get_order_status(codigo_pedido=codigo_pedido)
        
        if not order_status:
            return jsonify({"erro": "Pedido não encontrado"}), 404
            
        return jsonify({
            "success": True,
            "order": order_status
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar status do pedido {codigo_pedido}: {e}")
        return jsonify({"erro": "Erro interno ao buscar status do pedido"}), 500

@checkout_api_bp.route('/cart-details', methods=['GET'])
def get_cart_details():
    """
    Retorna detalhes do carrinho para o checkout
    """
    try:
        error_response, user_id, session_id = get_cart_owner_info()
        if error_response:
            return error_response

        conn = get_db()
        cur = conn.cursor()
        
        try:
            cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
            if not cart_id:
                return jsonify({"erro": "Não foi possível identificar o carrinho"}), 500

            # Buscar itens do carrinho
            cur.execute("""
                SELECT 
                    ci.quantidade,
                    ci.preco_unitario_no_momento,
                    p.id AS produto_id,
                    p.codigo_sku,
                    np.nome AS nome_produto,
                    e.nome AS estampa_nome,
                    t.nome AS tamanho_nome,
                    (SELECT ip.url FROM imagens_produto ip WHERE ip.produto_id = p.id ORDER BY ip.ordem ASC LIMIT 1) AS image_url
                FROM carrinho_itens ci
                JOIN produtos p ON ci.produto_id = p.id
                JOIN nome_produto np ON p.nome_produto_id = np.id
                JOIN estampa e ON p.estampa_id = e.id
                JOIN tamanho t ON p.tamanho_id = t.id
                WHERE ci.carrinho_id = %s
                ORDER BY ci.id ASC
            """, (cart_id,))
            
            cart_items_db = cur.fetchall()
            
            # Calcular totais
            items = []
            total_value = 0.0
            
            for item in cart_items_db:
                item_total = item[0] * float(item[1])  # quantidade * preco_unitario
                total_value += item_total
                
                items.append({
                    'produto_id': item[2],
                    'sku': item[3],
                    'nome_produto': item[4],
                    'estampa': item[5],
                    'tamanho': item[6],
                    'quantidade': item[0],
                    'preco_unitario': float(item[1]),
                    'subtotal': item_total,
                    'image_url': item[7] if item[7] else '/static/img/placeholder.jpg'
                })

            # Obter dados do cliente se logado
            customer_data = {}
            uid = session.get('uid')
            if uid:
                user_data = get_user_by_firebase_uid(uid)
                if user_data:
                    customer_data = {
                        'name': user_data.get('nome', ''),
                        'email': user_data.get('email', ''),
                        'tax_id': user_data.get('cpf', ''),
                        'phone': user_data.get('telefone', '')
                    }

            return jsonify({
                "success": True,
                "items": items,
                "totals": {
                    "subtotal": total_value,
                    "freight": 0.0,  # Será calculado no frontend
                    "discount": 0.0,
                    "total": total_value
                },
                "customer": customer_data
            }), 200

        except Exception as e:
            current_app.logger.error(f"Erro ao buscar detalhes do carrinho: {e}")
            return jsonify({"erro": "Erro interno ao buscar carrinho"}), 500
        finally:
            if cur:
                cur.close()

    except Exception as e:
        current_app.logger.error(f"Erro na API de detalhes do carrinho: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500