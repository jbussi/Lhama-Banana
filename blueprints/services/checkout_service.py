import requests
import json
from flask import g, current_app
import datetime
import os
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple

# --- Funções de interação com o banco de dados ---
def create_order_and_items(user_id: Optional[int], cart_items: List[Dict], shipping_info: Dict, 
                          total_value: float, freight_value: float, discount_value: float, 
                          client_ip: str, user_agent: str) -> Tuple[int, str]:
    """
    Cria um pedido e seus itens no banco de dados
    
    Args:
        user_id: ID do usuário (None se não logado)
        cart_items: Lista de itens do carrinho
        shipping_info: Informações de entrega
        total_value: Valor total do pedido
        freight_value: Valor do frete
        discount_value: Valor do desconto
        client_ip: IP do cliente
        user_agent: User agent do navegador
        
    Returns:
        Tuple com (venda_id, codigo_pedido)
    """
    conn = g.db
    cur = conn.cursor()
    
    try:
        # 1. Gerar um código de pedido único
        codigo_pedido = f"LB-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex().upper()}"

        # 2. Inserir na tabela 'vendas'
        # Verificar se há endereco_id no shipping_info (quando usuário usa endereço salvo)
        endereco_id = shipping_info.get('endereco_id')
        
        cur.execute("""
            INSERT INTO vendas (
                codigo_pedido, usuario_id, valor_total, valor_frete, valor_desconto,
                endereco_entrega_id, nome_recebedor, rua_entrega, numero_entrega, complemento_entrega, 
                bairro_entrega, cidade_entrega, estado_entrega, cep_entrega, telefone_entrega, email_entrega,
                status_pedido, cliente_ip, user_agent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            codigo_pedido, user_id, total_value, freight_value, discount_value,
            endereco_id,  # Vincular endereço salvo se fornecido
            shipping_info.get('nome_recebedor'), shipping_info.get('rua'), shipping_info.get('numero'),
            shipping_info.get('complemento'), shipping_info.get('bairro'),
            shipping_info.get('cidade'), shipping_info.get('estado'), shipping_info.get('cep'),
            shipping_info.get('telefone'), shipping_info.get('email'),
            'pendente_pagamento', # Status inicial
            client_ip, user_agent
        ))
        venda_id = cur.fetchone()[0]

        # 3. Inserir na tabela 'itens_venda' e decrementar estoque
        for item in cart_items:
            # Verificar estoque disponível
            cur.execute("""
                SELECT estoque FROM produtos WHERE id = %s
            """, (item['produto_id'],))
            
            estoque_atual = cur.fetchone()
            if not estoque_atual or estoque_atual[0] < item['quantidade']:
                raise Exception(f"Estoque insuficiente para o produto {item.get('nome_produto_snapshot', 'N/A')}")
            
            # Inserir item da venda
            cur.execute("""
                INSERT INTO itens_venda (
                    venda_id, produto_id, quantidade, preco_unitario, subtotal,
                    nome_produto_snapshot, sku_produto_snapshot, detalhes_produto_snapshot
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                venda_id, item['produto_id'], item['quantidade'], item['preco_unitario'], item['subtotal'],
                item['nome_produto_snapshot'], item['sku_produto_snapshot'], 
                json.dumps(item.get('detalhes_produto_snapshot', {}))
            ))
            
            # Decrementar estoque
            cur.execute("""
                UPDATE produtos 
                SET estoque = estoque - %s 
                WHERE id = %s
            """, (item['quantidade'], item['produto_id']))

        conn.commit()
        current_app.logger.info(f"Pedido {codigo_pedido} criado com sucesso. Venda ID: {venda_id}")
        return venda_id, codigo_pedido
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar pedido: {e}")
        raise e
    finally:
        cur.close()

def create_payment_entry(venda_id: int, payment_data: Dict, pagseguro_response: Dict) -> int:
    """
    Cria entrada de pagamento no banco de dados
    
    Args:
        venda_id: ID da venda
        payment_data: Dados do pagamento enviados
        pagseguro_response: Resposta da API do PagSeguro
        
    Returns:
        ID da entrada de pagamento criada
    """
    conn = g.db
    cur = conn.cursor()
    
    try:
        # Parse da resposta do PagBank
        transaction_id = pagseguro_response.get('id')
        charges = pagseguro_response.get('charges', [])
        
        if not charges:
            raise Exception("Resposta do PagBank não contém informações de cobrança")
            
        charge = charges[0]  # Primeira cobrança
        payment_method = charge.get('payment_method', {})
        
        payment_type = payment_method.get('type', 'UNKNOWN')
        status = charge.get('status', 'UNKNOWN')
        amount = charge.get('amount', {})
        value = amount.get('value', 0) / 100  # PagSeguro retorna em centavos
        
        # Informações específicas por tipo de pagamento
        qrcode_link = None
        qrcode_image = None
        boleto_link = None
        barcode_data = None
        card_brand = None
        installments = 1
        
        if payment_type == 'PIX':
            pix_data = payment_method.get('pix', {})
            # Tentar diferentes estruturas de resposta do PagBank
            qr_codes = pix_data.get('qr_codes', [])
            if not qr_codes:
                qr_codes = pix_data.get('qr_code', [])
            
            if qr_codes and len(qr_codes) > 0:
                qr_code = qr_codes[0]
                links = qr_code.get('links', [])
                qrcode_link = links[0].get('href') if links else qr_code.get('href', '')
                qrcode_image = links[0].get('href') if links else qr_code.get('href', '')
                # O código PIX text será extraído do JSON quando necessário
            else:
                qrcode_link = pix_data.get('link', '')
                qrcode_image = pix_data.get('link', '')
            
        elif payment_type == 'BOLETO':
            boleto_data = payment_method.get('boleto', {})
            boleto_link = boleto_data.get('links', [{}])[0].get('href')
            barcode_data = boleto_data.get('barcode', {}).get('content')
            
        elif payment_type == 'CREDIT_CARD':
            card_data = payment_method.get('card', {})
            card_brand = card_data.get('brand', '')
            installments = charge.get('installments', 1)

        cur.execute("""
            INSERT INTO pagamentos (
                venda_id, pagbank_transaction_id, forma_pagamento_tipo,
                bandeira_cartao, parcelas, valor_pago, status_pagamento,
                pagbank_qrcode_link, pagbank_qrcode_image, pagbank_boleto_link, 
                pagbank_barcode_data, json_resposta_api
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            venda_id, transaction_id, payment_type,
            card_brand, installments, value, status,
            qrcode_link, qrcode_image, boleto_link,
            barcode_data, json.dumps(pagseguro_response)
        ))
        
        payment_id = cur.fetchone()[0]
        conn.commit()
        
        current_app.logger.info(f"Pagamento {payment_id} criado para venda {venda_id}")
        return payment_id
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar entrada de pagamento: {e}")
        raise e
    finally:
        cur.close()

def get_order_status(venda_id=None, codigo_pedido=None):
    conn = g.db
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # Para retornar dicionários
    try:
        query = """
            SELECT
                v.id as venda_id, v.codigo_pedido, v.valor_total, v.status_pedido,
                p.status_pagamento, p.forma_pagamento_tipo, p.pagbank_qrcode_link, p.pagbank_barcode_data
            FROM vendas v
            LEFT JOIN pagamentos p ON v.id = p.venda_id
            WHERE 1=1
        """
        params = []
        if venda_id:
            query += " AND v.id = %s"
            params.append(venda_id)
        if codigo_pedido:
            query += " AND v.codigo_pedido = %s"
            params.append(codigo_pedido)
        
        cur.execute(query, params)
        result = cur.fetchone() # Ou fetchall() se puder ter múltiplas tentativas de pagamento por venda
        return dict(result) if result else None
    except Exception as e:
        raise e
    finally:
        cur.close()

# --- Funções de interação com o PagBank API ---
def call_pagbank_api(endpoint_url: str, api_token: str, payload: Dict) -> Dict:
    """
    Chama a API do PagBank para processar pagamentos
    
    Args:
        endpoint_url: URL do endpoint da API
        api_token: Token de autenticação
        payload: Dados do pagamento
        
    Returns:
        Resposta da API do PagBank
    """
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        current_app.logger.info(f"Enviando requisição para PagBank: {endpoint_url}")
        current_app.logger.info(f"Payload PagBank:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            endpoint_url, 
            headers=headers, 
            json=payload,  # Usar json= ao invés de data=json.dumps()
            timeout=30
        )
        
        current_app.logger.info(f"Resposta PagBank - Status: {response.status_code}")
        
        # PagBank retorna 200 ou 201 para sucesso
        if response.status_code in [200, 201]:
            try:
                response_data = response.json()
                
                # Validar estrutura básica da resposta
                if not isinstance(response_data, dict):
                    raise Exception("Resposta do PagBank não é um objeto JSON válido")
                
                # Validar que a resposta contém charges
                charges = response_data.get('charges', [])
                if not charges or len(charges) == 0:
                    raise Exception("Resposta do PagBank não contém informações de cobrança")
                
                current_app.logger.info(f"Resposta PagBank válida: {len(charges)} charge(s)")
                return response_data
                
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Erro ao decodificar JSON da resposta PagBank: {e}")
                current_app.logger.error(f"Resposta recebida: {response.text[:500]}")
                raise Exception(f"Resposta inválida do PagBank: não é um JSON válido")
        else:
            # Tratar diferentes códigos de erro HTTP
            error_data = {}
            error_message = f"Erro na API do PagBank (HTTP {response.status_code})"
            
            try:
                error_data = response.json()
                
                # Extrair mensagem de erro específica se disponível
                if 'error' in error_data:
                    error_message = f"Erro do PagBank: {error_data.get('error', {}).get('message', error_message)}"
                elif 'message' in error_data:
                    error_message = f"Erro do PagBank: {error_data.get('message')}"
                elif 'errors' in error_data and isinstance(error_data['errors'], list) and len(error_data['errors']) > 0:
                    error_message = f"Erro do PagBank: {error_data['errors'][0].get('message', error_message)}"
                    
            except json.JSONDecodeError:
                # Se não conseguir parsear JSON, usar o texto da resposta
                error_text = response.text[:500]
                error_data = {'error': error_text, 'status_code': response.status_code}
                
                # Mensagens específicas por código de status
                if response.status_code == 400:
                    error_message = "Dados de pagamento inválidos. Verifique as informações e tente novamente."
                elif response.status_code == 401:
                    error_message = "Erro de autenticação no gateway de pagamento. Entre em contato com o suporte."
                elif response.status_code == 403:
                    error_message = "Acesso negado ao gateway de pagamento. Entre em contato com o suporte."
                elif response.status_code == 404:
                    error_message = "Endpoint do gateway de pagamento não encontrado. Entre em contato com o suporte."
                elif response.status_code >= 500:
                    error_message = "Erro interno no gateway de pagamento. Tente novamente em alguns instantes."
                else:
                    error_message = f"Erro ao processar pagamento (código {response.status_code})"
            
            current_app.logger.error(f"Erro PagBank: {response.status_code} - {error_data}")
            raise Exception(f"{error_message} (HTTP {response.status_code})")
            
    except requests.exceptions.Timeout:
        current_app.logger.error("Timeout na comunicação com PagBank (30s)")
        raise Exception("Tempo de resposta do gateway de pagamento excedido. Tente novamente.")
    except requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"Erro de conexão com PagBank: {e}")
        raise Exception("Erro de conexão com o gateway de pagamento. Verifique sua conexão e tente novamente.")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro na requisição ao PagBank: {e}")
        raise Exception(f"Erro ao comunicar com o gateway de pagamento: {str(e)}")
    except Exception as e:
        # Re-lançar exceções que já foram tratadas
        if "Erro" in str(e) or "Erro do PagBank" in str(e) or "Resposta" in str(e):
            raise
        # Tratar outras exceções inesperadas
        current_app.logger.error(f"Erro inesperado ao chamar PagBank: {e}")
        raise Exception(f"Erro inesperado ao processar pagamento: {str(e)}")

def create_pagbank_payload(cart_items: List[Dict], shipping_info: Dict, 
                           payment_data: Dict, customer_data: Dict) -> Dict:
    """
    Cria o payload para a API do PagBank
    
    Args:
        cart_items: Itens do carrinho
        shipping_info: Informações de entrega
        payment_data: Dados do pagamento
        customer_data: Dados do cliente
        
    Returns:
        Payload formatado para PagBank
    """
    try:
        # Preparar itens
        items = []
        for item in cart_items:
            items.append({
                "reference_id": str(item['produto_id']),
                "name": item['nome_produto_snapshot'],
                "quantity": item['quantidade'],
                "unit_amount": int(item['preco_unitario'] * 100)  # Em centavos
            })
        
        # Preparar endereço de entrega
        shipping_address = {
            "street": shipping_info.get('rua', ''),
            "number": shipping_info.get('numero', ''),
            "complement": shipping_info.get('complemento', ''),
            "locality": shipping_info.get('bairro', ''),
            "city": shipping_info.get('cidade', ''),
            "region_code": shipping_info.get('estado', ''),
            "country": "BRA",
            "postal_code": shipping_info.get('cep', '').replace('-', '')
        }
        
        # Preparar dados do cliente
        customer = {
            "name": customer_data.get('name', ''),
            "email": customer_data.get('email', ''),
            "tax_id": customer_data.get('tax_id', '').replace('.', '').replace('-', '').replace('/', ''),
            "phones": [{
                "country": "55",
                "area": customer_data.get('phone_area', ''),
                "number": customer_data.get('phone_number', ''),
                "type": "MOBILE"
            }]
        }
        
        # Preparar cobrança
        charge = {
            "reference_id": f"order-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": f"Pedido LhamaBanana - {len(cart_items)} item(s)",
            "amount": {
                "value": int(payment_data.get('total_value', 0) * 100),  # Em centavos
                "currency": "BRL"
            },
            "payment_method": {
                "type": payment_data.get('payment_method', 'CREDIT_CARD').upper()
            }
        }
        
        # Adicionar dados específicos do método de pagamento
        payment_method_type = payment_data.get('payment_method', 'CREDIT_CARD').upper()
        
        if payment_method_type == 'CREDIT_CARD':
            # Converter exp_year para 4 dígitos se necessário
            exp_year_str = str(payment_data.get('card_exp_year', ''))
            if len(exp_year_str) == 2:
                # Se for 2 dígitos, assumir 20XX
                current_year_prefix = str(datetime.datetime.now().year)[:2]
                exp_year_int = int(current_year_prefix + exp_year_str)
            elif len(exp_year_str) == 4:
                exp_year_int = int(exp_year_str)
            else:
                exp_year_int = int(exp_year_str) if exp_year_str.isdigit() else datetime.datetime.now().year
            
            # Converter exp_month para inteiro
            exp_month_str = str(payment_data.get('card_exp_month', '')).strip()
            exp_month_int = int(exp_month_str) if exp_month_str.isdigit() else 12
            
            # Limpar e validar tax_id do portador do cartão
            card_holder_tax_id = str(payment_data.get('card_holder_cpf_cnpj', '')).replace('.', '').replace('-', '').replace('/', '').strip()
            # Se não tiver tax_id, usar o do cliente como fallback
            if not card_holder_tax_id:
                card_holder_tax_id = str(customer_data.get('tax_id', '')).replace('.', '').replace('-', '').replace('/', '').strip()
            
            # Validar que temos token do cartão (obrigatório)
            if not payment_data.get('card_token'):
                raise Exception("Token do cartão é obrigatório para pagamento com cartão de crédito")
            
            # Para cartão, usar token (única forma suportada)
            charge["payment_method"].update({
                "capture": True,  # Campo obrigatório: captura imediata
                "card": {
                    "id": payment_data.get('card_token'),  # ID do token do cartão
                    "security_code": payment_data.get('security_code', ''),  # CVV ainda necessário
                    "holder": {
                        "name": payment_data.get('card_holder_name', '') or customer_data.get('name', ''),
                        "tax_id": card_holder_tax_id
                    }
                },
                "installments": payment_data.get('installments', 1)
            })
        elif payment_method_type == 'PIX':
            charge["payment_method"].update({
                "pix": {
                    "expiration_date": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                }
            })
        elif payment_method_type == 'BOLETO':
            charge["payment_method"].update({
                "boleto": {
                    "due_date": (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%d'),
                    "instruction_lines": {
                        "line_1": "Não receber após o vencimento",
                        "line_2": "LhamaBanana - Sua Loja de Roupas"
                    },
                    "holder": {
                        "name": customer_data.get('name', ''),
                        "tax_id": customer_data.get('tax_id', '').replace('.', '').replace('-', '').replace('/', ''),
                        "email": customer_data.get('email', ''),
                        "address": shipping_address
                    }
                }
            })
        
        # Montar payload final
        payload = {
            "reference_id": f"lhama-banana-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer": customer,
            "items": items,
            "shipping": {
                "address": shipping_address
            },
            "charges": [charge],
            "notification_urls": [
                current_app.config.get('PAGBANK_NOTIFICATION_URL', 'http://localhost:5000/pagbank/notification')
            ]
        }
        
        return payload
        
    except Exception as e:
        current_app.logger.error(f"Erro ao criar payload PagBank: {e}")
        raise Exception(f"Erro ao preparar dados para PagBank: {e}")
