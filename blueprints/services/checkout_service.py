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
        cur.execute("""
            INSERT INTO vendas (
                codigo_pedido, usuario_id, valor_total, valor_frete, valor_desconto,
                nome_recebedor, rua_entrega, numero_entrega, complemento_entrega, bairro_entrega,
                cidade_entrega, estado_entrega, cep_entrega,
                status_pedido, cliente_ip, user_agent
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            codigo_pedido, user_id, total_value, freight_value, discount_value,
            shipping_info.get('nome_recebedor'), shipping_info.get('rua'), shipping_info.get('numero'),
            shipping_info.get('complemento'), shipping_info.get('bairro'),
            shipping_info.get('cidade'), shipping_info.get('estado'), shipping_info.get('cep'),
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
            qrcode_link = pix_data.get('qr_code', {}).get('links', [{}])[0].get('href')
            qrcode_image = pix_data.get('qr_code', {}).get('links', [{}])[0].get('href')
            
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
        current_app.logger.debug(f"Payload PagBank: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            endpoint_url, 
            headers=headers, 
            json=payload,  # Usar json= ao invés de data=json.dumps()
            timeout=30
        )
        
        current_app.logger.info(f"Resposta PagBank - Status: {response.status_code}")
        
        # PagBank retorna 200 ou 201 para sucesso
        if response.status_code in [200, 201]:
            return response.json()
        else:
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {'error': response.text[:500]}
            
            current_app.logger.error(f"Erro PagBank: {response.status_code} - {error_data}")
            raise Exception(f"Erro na API do PagBank: {response.status_code} - {error_data}")
            
    except requests.exceptions.Timeout:
        raise Exception("Timeout na comunicação com PagBank")
    except requests.exceptions.ConnectionError:
        raise Exception("Erro de conexão com PagBank")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro ao comunicar com a API do PagBank: {e}")
    except json.JSONDecodeError as e:
        current_app.logger.error(f"Erro ao decodificar JSON da resposta PagBank: {e}")
        raise Exception("Resposta inválida do PagBank")

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
            # Para cartão, usar token se disponível, senão usar dados diretos (sandbox)
            if payment_data.get('card_token'):
                charge["payment_method"].update({
                    "card": {
                        "id": payment_data.get('card_token'),  # ID do token do cartão
                        "security_code": payment_data.get('security_code', ''),  # CVV ainda necessário
                        "holder": {
                            "name": payment_data.get('card_holder_name', ''),
                            "tax_id": payment_data.get('card_holder_cpf_cnpj', '').replace('.', '').replace('-', '').replace('/', '')
                        }
                    },
                    "installments": payment_data.get('installments', 1)
                })
            else:
                # Fallback para dados diretos (apenas sandbox/teste)
                charge["payment_method"].update({
                    "card": {
                        "number": payment_data.get('card_number', '').replace(' ', ''),
                        "exp_month": payment_data.get('card_exp_month', ''),
                        "exp_year": payment_data.get('card_exp_year', ''),
                        "security_code": payment_data.get('card_cvv', ''),
                        "holder": {
                            "name": payment_data.get('card_holder_name', ''),
                            "tax_id": payment_data.get('card_holder_cpf_cnpj', '').replace('.', '').replace('-', '').replace('/', '')
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
