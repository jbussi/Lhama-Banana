"""
Serviços de checkout e integração com PagBank

ARQUITETURA DE PAGAMENTO:
========================
O webhook do PagBank é a ÚNICA fonte de verdade do status do pagamento.

REGRAS ARQUITETURAIS:
- A resposta do /orders é apenas uma intenção de pagamento, não confirmação
- Status inicial SEMPRE é PENDING/AWAITING_PAYMENT
- Toda mudança de estado vem exclusivamente do webhook
- IDs do PagBank (order_id, charge_id) são usados apenas para reconciliação
- Backend nunca considera pagamento confirmado fora do webhook
- Frontend nunca valida pagamento, apenas faz polling do status

FLUXO:
1. Checkout cria pedido com status PENDING
2. Backend chama /orders do PagBank
3. Backend salva apenas IDs retornados (order_id, charge_id)
4. Webhook recebe notificação e atualiza status final
"""
import requests
import json
from flask import g, current_app
import datetime
import os
import re
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple

# --- Funções de interação com o banco de dados ---
def create_order_and_items(user_id: Optional[int], cart_items: List[Dict], shipping_info: Dict, 
                          total_value: float, freight_value: float, discount_value: float, 
                          client_ip: str, user_agent: str, fiscal_data: Optional[Dict] = None, 
                          cupom_id: Optional[int] = None) -> Tuple[int, str]:
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
        # 1. Verificar se a coluna usuario_id existe, se não, criar
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'vendas' 
            AND column_name = 'usuario_id'
        """)
        usuario_id_exists = cur.fetchone() is not None
        
        if not usuario_id_exists:
            current_app.logger.info("Coluna usuario_id não existe na tabela vendas. Criando...")
            try:
                cur.execute("""
                    ALTER TABLE vendas 
                    ADD COLUMN usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas (usuario_id)
                """)
                conn.commit()
                current_app.logger.info("Coluna usuario_id criada com sucesso")
            except Exception as alter_error:
                conn.rollback()
                current_app.logger.warning(f"Erro ao criar coluna usuario_id (pode já existir): {alter_error}")
        
        # 2. Gerar um código de pedido único
        codigo_pedido = f"LB-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex().upper()}"

        # 3. Inserir na tabela 'vendas'
        # Verificar se há endereco_id no shipping_info (quando usuário usa endereço salvo)
        endereco_id = shipping_info.get('endereco_id')
        
        # Preparar dados fiscais se fornecidos
        fiscal_values = []
        fiscal_columns = ''
        if fiscal_data:
            fiscal_columns = """,
                fiscal_tipo, fiscal_cpf_cnpj, fiscal_nome_razao_social,
                fiscal_inscricao_estadual, fiscal_inscricao_municipal,
                fiscal_rua, fiscal_numero, fiscal_complemento,
                fiscal_bairro, fiscal_cidade, fiscal_estado, fiscal_cep"""
            endereco_fiscal = fiscal_data.get('endereco', {})
            fiscal_values = [
                fiscal_data.get('tipo'),
                fiscal_data.get('cpf_cnpj'),
                fiscal_data.get('nome_razao_social'),
                fiscal_data.get('inscricao_estadual'),
                fiscal_data.get('inscricao_municipal'),
                endereco_fiscal.get('rua'),
                endereco_fiscal.get('numero'),
                endereco_fiscal.get('complemento'),
                endereco_fiscal.get('bairro'),
                endereco_fiscal.get('cidade'),
                endereco_fiscal.get('estado'),
                endereco_fiscal.get('cep')
            ]
        
        # Construir query dinamicamente
        base_columns = """
            codigo_pedido, usuario_id, valor_total, valor_frete, valor_desconto,
            endereco_entrega_id, nome_recebedor, rua_entrega, numero_entrega, complemento_entrega, 
            bairro_entrega, cidade_entrega, estado_entrega, cep_entrega, telefone_entrega, email_entrega,
            status_pedido, cliente_ip, user_agent"""
        
        base_values = "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
        
        # Adicionar cupom_id se fornecido
        if cupom_id:
            base_columns += ", cupom_id"
            base_values += ", %s"
        
        if fiscal_data:
            fiscal_placeholders = ', ' + ', '.join(['%s'] * len(fiscal_values))
            query = f"""
                INSERT INTO vendas (
                    {base_columns}{fiscal_columns}
                ) VALUES (
                    {base_values}{fiscal_placeholders}
                )
                RETURNING id;
            """
            params_list = [
                codigo_pedido, user_id, total_value, freight_value, discount_value,
                endereco_id,
                shipping_info.get('nome_recebedor'), shipping_info.get('rua'), shipping_info.get('numero'),
                shipping_info.get('complemento'), shipping_info.get('bairro'),
                shipping_info.get('cidade'), shipping_info.get('estado'), shipping_info.get('cep'),
                shipping_info.get('telefone'), shipping_info.get('email'),
                'pendente_pagamento',
                client_ip, user_agent
            ]
            if cupom_id:
                params_list.append(cupom_id)
            params = tuple(params_list) + tuple(fiscal_values)
        else:
            query = f"""
                INSERT INTO vendas (
                    {base_columns}
                ) VALUES (
                    {base_values}
                )
                RETURNING id;
            """
            params_list = [
                codigo_pedido, user_id, total_value, freight_value, discount_value,
                endereco_id,
                shipping_info.get('nome_recebedor'), shipping_info.get('rua'), shipping_info.get('numero'),
                shipping_info.get('complemento'), shipping_info.get('bairro'),
                shipping_info.get('cidade'), shipping_info.get('estado'), shipping_info.get('cep'),
                shipping_info.get('telefone'), shipping_info.get('email'),
                'pendente_pagamento',
                client_ip, user_agent
            ]
            if cupom_id:
                params_list.append(cupom_id)
            params = tuple(params_list)
        
        cur.execute(query, params)
        venda_id = cur.fetchone()[0]

        # 3. Verificar se as colunas venda_id e produto_id existem em itens_venda
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'itens_venda' 
            AND column_name IN ('venda_id', 'produto_id')
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        has_venda_id = 'venda_id' in existing_columns
        has_produto_id = 'produto_id' in existing_columns
        
        if not has_venda_id:
            current_app.logger.info("Coluna venda_id não existe em itens_venda. Criando...")
            try:
                cur.execute("""
                    ALTER TABLE itens_venda 
                    ADD COLUMN venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE
                """)
                conn.commit()
                has_venda_id = True
                current_app.logger.info("Coluna venda_id criada com sucesso")
            except Exception as alter_error:
                conn.rollback()
                current_app.logger.warning(f"Erro ao criar coluna venda_id: {alter_error}")
        
        if not has_produto_id:
            current_app.logger.info("Coluna produto_id não existe em itens_venda. Criando...")
            try:
                cur.execute("""
                    ALTER TABLE itens_venda 
                    ADD COLUMN produto_id INTEGER REFERENCES produtos(id) ON DELETE SET NULL
                """)
                conn.commit()
                has_produto_id = True
                current_app.logger.info("Coluna produto_id criada com sucesso")
            except Exception as alter_error:
                conn.rollback()
                current_app.logger.warning(f"Erro ao criar coluna produto_id: {alter_error}")
        
        # 4. Inserir na tabela 'itens_venda' e decrementar estoque
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

        # 5. Registrar uso do cupom se fornecido
        if cupom_id and user_id:
            try:
                # Buscar CPF do usuário
                cur.execute("SELECT cpf FROM usuarios WHERE id = %s", (user_id,))
                user_cpf_result = cur.fetchone()
                user_cpf = None
                if user_cpf_result and user_cpf_result[0]:
                    # Limpar CPF (remover formatação)
                    user_cpf = re.sub(r'[^0-9]', '', user_cpf_result[0])
                
                # Registrar uso do cupom
                cur.execute("""
                    INSERT INTO cupom_usado (cupom_id, usuario_id, venda_id, valor_desconto_aplicado, cpf_usuario)
                    VALUES (%s, %s, %s, %s, %s)
                """, (cupom_id, user_id, venda_id, discount_value, user_cpf))
                
                # Atualizar contador de uso do cupom
                cur.execute("""
                    UPDATE cupom 
                    SET uso_atual = uso_atual + 1 
                    WHERE id = %s
                """, (cupom_id,))
                
                conn.commit()
                current_app.logger.info(f"Uso do cupom {cupom_id} registrado para venda {venda_id}")
            except Exception as cupom_error:
                conn.rollback()
                current_app.logger.error(f"Erro ao registrar uso do cupom: {cupom_error}")
                # Não falhar o pedido por erro no registro do cupom
                conn.commit()
        else:
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
        # Verificar se a coluna venda_id existe, se não, criar
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pagamentos' 
            AND column_name = 'venda_id'
        """)
        venda_id_exists = cur.fetchone() is not None
        
        if not venda_id_exists:
            current_app.logger.info("Coluna venda_id não existe na tabela pagamentos. Criando...")
            try:
                cur.execute("""
                    ALTER TABLE pagamentos 
                    ADD COLUMN venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pagamentos_venda_id ON pagamentos (venda_id)
                """)
                conn.commit()
                current_app.logger.info("Coluna venda_id criada com sucesso na tabela pagamentos")
            except Exception as alter_error:
                conn.rollback()
                current_app.logger.warning(f"Erro ao criar coluna venda_id (pode já existir): {alter_error}")
        
        # Parse da resposta do PagBank
        order_id = pagseguro_response.get('id')  # ID do pedido (ORDE_...)
        
        # Para PIX, a resposta tem qr_codes diretamente, não charges
        # Para outros métodos, a resposta tem charges
        qr_codes = pagseguro_response.get('qr_codes', [])
        charges = pagseguro_response.get('charges', [])
        
        # Determinar tipo de pagamento e extrair dados
        if qr_codes and len(qr_codes) > 0:
            # PIX: usar qr_codes
            payment_type = 'PIX'
            charge_id = None  # PIX não tem charge_id
            # IMPORTANTE: Não usamos o status da resposta do PagBank aqui.
            # O status inicial é SEMPRE PENDING/AWAITING_PAYMENT.
            # O webhook do PagBank é a ÚNICA fonte de verdade do status do pagamento.
            status = 'PENDING'  # Status inicial fixo - webhook atualizará quando necessário
            
            # Para PIX, o valor pode vir do qr_code ou do amount no nível raiz
            qr_code = qr_codes[0]
            amount_data = qr_code.get('amount', {})
            if not amount_data:
                # Tentar amount no nível raiz
                amount_data = pagseguro_response.get('amount', {})
            value = amount_data.get('value', 0) / 100 if amount_data else 0  # PagBank retorna em centavos
        elif charges and len(charges) > 0:
            # CREDIT_CARD ou BOLETO: usar charges
            charge = charges[0]  # Primeira cobrança
            charge_id = charge.get('id')  # ID da cobrança (CHAR_...) - usado no webhook
            payment_method = charge.get('payment_method', {})
            payment_type = payment_method.get('type', 'UNKNOWN')
            # IMPORTANTE: Não usamos o status da resposta do PagBank aqui.
            # O status inicial é SEMPRE PENDING/AWAITING_PAYMENT.
            # O webhook do PagBank é a ÚNICA fonte de verdade do status do pagamento.
            status = 'PENDING'  # Status inicial fixo - webhook atualizará quando necessário
            amount = charge.get('amount', {})
            value = amount.get('value', 0) / 100  # PagBank retorna em centavos
        else:
            raise Exception("Resposta do PagBank não contém informações de cobrança (charges) nem QR codes (qr_codes)")
        
        # Informações específicas por tipo de pagamento
        qrcode_link = None
        qrcode_image = None
        boleto_link = None
        barcode_data = None
        card_brand = None
        installments = 1
        
        if payment_type == 'PIX':
            # Para PIX, os dados vêm em qr_codes no nível raiz da resposta, não dentro de charges
            # A resposta do PagBank para PIX tem estrutura:
            # {
            #   "qr_codes": [{
            #     "id": "...",
            #     "text": "...",  // Código PIX completo
            #     "expiration_date": "...",
            #     "links": [{"rel": "QRCODE.PNG", "href": "..."}, ...]
            #   }]
            # }
            qr_codes = pagseguro_response.get('qr_codes', [])
            qrcode_text = ''
            
            if qr_codes and len(qr_codes) > 0:
                qr_code = qr_codes[0]
                qrcode_text = qr_code.get('text', '')  # Código PIX completo
                
                # Buscar link do QR code PNG
                links = qr_code.get('links', [])
                qrcode_link = None
                qrcode_image = None
                
                for link in links:
                    if link.get('rel') == 'QRCODE.PNG':
                        qrcode_image = link.get('href', '')
                        qrcode_link = link.get('href', '')  # Usar mesmo link para ambos
                    elif link.get('rel') == 'QRCODE.BASE64':
                        # Se não tiver PNG, usar BASE64 como fallback
                        if not qrcode_image:
                            qrcode_image = link.get('href', '')
                
                # Se não encontrou links, tentar estrutura alternativa
                if not qrcode_link:
                    qrcode_link = qr_code.get('href', '')
                    qrcode_image = qr_code.get('href', '')
                
                current_app.logger.info(f"[PagBank] QR Code PIX extraído: text={qrcode_text[:50] if qrcode_text else 'N/A'}..., link={qrcode_link}")
            else:
                qrcode_text = ''
                qrcode_link = None
                qrcode_image = None
            
        elif payment_type == 'BOLETO':
            # Para boleto, os links vêm em charges.links, não em boleto.links
            # E o barcode vem em boleto.barcode ou boleto.formatted_barcode
            boleto_data = payment_method.get('boleto', {})
            
            # Buscar links do charge (não do boleto)
            # Os links podem estar em charges.links ou em boleto.links
            charge_links = []
            if charges and len(charges) > 0:
                charge_links = charges[0].get('links', [])
            
            # Tentar também em boleto_data.links como fallback
            boleto_links = boleto_data.get('links', [])
            
            # Usar links do charge primeiro, depois do boleto
            all_links = charge_links if charge_links else boleto_links
            boleto_link = all_links[0].get('href', '') if all_links else None
            
            # Buscar código de barras (priorizar formatted_barcode por ser mais legível)
            barcode_data = None
            if boleto_data.get('formatted_barcode'):
                # Priorizar formatted_barcode (com pontuação, mais legível)
                barcode_data = boleto_data.get('formatted_barcode', '')
            elif isinstance(boleto_data.get('barcode'), dict):
                # Se for objeto, extrair content
                barcode_data = boleto_data.get('barcode', {}).get('content', '')
            elif boleto_data.get('barcode'):
                # Se for string direta
                barcode_data = boleto_data.get('barcode', '')
            
        elif payment_type == 'CREDIT_CARD':
            # Para CREDIT_CARD, charge já foi extraído acima
            if charges and len(charges) > 0:
                charge = charges[0]
                payment_method = charge.get('payment_method', {})
                card_data = payment_method.get('card', {})
                card_brand = card_data.get('brand', '')
                installments = charge.get('installments', 1)
            else:
                card_brand = None
                installments = 1

        # Verificar se a coluna pagbank_order_id existe, se não, criar
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pagamentos' 
            AND column_name = 'pagbank_order_id'
        """)
        order_id_col_exists = cur.fetchone() is not None
        
        if not order_id_col_exists:
            current_app.logger.info("Coluna pagbank_order_id não existe na tabela pagamentos. Criando...")
            try:
                cur.execute("""
                    ALTER TABLE pagamentos 
                    ADD COLUMN pagbank_order_id VARCHAR(100)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pagamentos_order_id ON pagamentos (pagbank_order_id)
                """)
                conn.commit()
                current_app.logger.info("Coluna pagbank_order_id criada com sucesso")
            except Exception as alter_error:
                conn.rollback()
                current_app.logger.warning(f"Erro ao criar coluna pagbank_order_id (pode já existir): {alter_error}")
        
        # Verificar se a coluna pagbank_charge_id existe, se não, criar
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pagamentos' 
            AND column_name = 'pagbank_charge_id'
        """)
        charge_id_col_exists = cur.fetchone() is not None
        
        if not charge_id_col_exists:
            current_app.logger.info("Coluna pagbank_charge_id não existe na tabela pagamentos. Criando...")
            try:
                cur.execute("""
                    ALTER TABLE pagamentos 
                    ADD COLUMN pagbank_charge_id VARCHAR(100)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_pagamentos_charge_id ON pagamentos (pagbank_charge_id)
                """)
                conn.commit()
                current_app.logger.info("Coluna pagbank_charge_id criada com sucesso")
            except Exception as alter_error:
                conn.rollback()
                current_app.logger.warning(f"Erro ao criar coluna pagbank_charge_id (pode já existir): {alter_error}")
        
        # Inserir pagamento com todos os IDs do PagBank
        # pagbank_transaction_id = order_id (para compatibilidade)
        # pagbank_order_id = order_id (ID do pedido)
        # pagbank_charge_id = charge_id (ID da cobrança - usado no webhook)
        cur.execute("""
            INSERT INTO pagamentos (
                venda_id, pagbank_transaction_id, pagbank_order_id, pagbank_charge_id,
                forma_pagamento_tipo, bandeira_cartao, parcelas, valor_pago, status_pagamento,
                pagbank_qrcode_link, pagbank_qrcode_image, pagbank_boleto_link, 
                pagbank_barcode_data, json_resposta_api
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            venda_id, 
            order_id,      # pagbank_transaction_id (mantido para compatibilidade)
            order_id,      # pagbank_order_id (ID do pedido)
            charge_id,     # pagbank_charge_id (ID da cobrança - usado no webhook)
            payment_type,
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
        
        # Verificar se notification_urls está presente no payload
        if 'notification_urls' in payload:
            current_app.logger.info(f"[PagBank] ✅ notification_urls presente no payload: {payload['notification_urls']}")
        else:
            current_app.logger.warning(f"[PagBank] ⚠️ notification_urls NÃO está presente no payload!")
            current_app.logger.warning(f"[PagBank] Webhook não será chamado pelo PagBank!")
        
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
                
                # Validar que a resposta contém charges ou qr_codes (para PIX)
                charges = response_data.get('charges', [])
                qr_codes = response_data.get('qr_codes', [])
                
                if not charges and not qr_codes:
                    raise Exception("Resposta do PagBank não contém informações de cobrança (charges) nem QR codes (qr_codes)")
                
                if qr_codes:
                    current_app.logger.info(f"Resposta PagBank válida: {len(qr_codes)} QR code(s) PIX")
                else:
                    current_app.logger.info(f"Resposta PagBank válida: {len(charges)} charge(s)")
                
                # Verificar se notification_urls foi aceita na resposta
                notification_urls_in_response = response_data.get('notification_urls', [])
                if notification_urls_in_response:
                    current_app.logger.info(f"[PagBank] ✅ notification_urls aceita pelo PagBank: {notification_urls_in_response}")
                    current_app.logger.info(f"[PagBank] Webhook será chamado automaticamente quando o status mudar")
                else:
                    current_app.logger.warning(f"[PagBank] ⚠️ notification_urls NÃO está na resposta do PagBank!")
                    current_app.logger.warning(f"[PagBank] Payload enviado tinha notification_urls: {payload.get('notification_urls', 'NÃO ENVIADO')}")
                    current_app.logger.warning(f"[PagBank] Webhook NÃO será chamado automaticamente. Verifique a configuração da URL.")
                
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
        
        # Adicionar dados específicos do método de pagamento
        payment_method_type = payment_data.get('payment_method', 'CREDIT_CARD').upper()
        
        # Para PIX, usar estrutura diferente (qr_codes ao invés de charges)
        if payment_method_type == 'PIX':
            # PIX usa qr_codes diretamente no payload, não dentro de charges
            # Calcular data de expiração (padrão: 1 dia)
            expiration_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S-03:00')
            
            # Montar payload com qr_codes para PIX
            payload = {
                "reference_id": f"lhama-banana-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                "customer": customer,
                "items": items,
                "qr_codes": [
                    {
                        "amount": {
                            "value": int(payment_data.get('total_value', 0) * 100)  # Em centavos
                        },
                        "expiration_date": expiration_date
                    }
                ],
                "shipping": {
                    "address": shipping_address
                }
            }
        else:
            # Para outros métodos (CREDIT_CARD, BOLETO), usar charges
            # Preparar cobrança
            charge = {
                "reference_id": f"order-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": f"Pedido LhamaBanana - {len(cart_items)} item(s)",
                "amount": {
                    "value": int(payment_data.get('total_value', 0) * 100),  # Em centavos
                    "currency": "BRL"
                },
                "payment_method": {
                    "type": payment_method_type
                }
            }
            
            if payment_method_type == 'CREDIT_CARD':
                # SEGURANÇA: Dados do cartão são validados no endpoint isolado /api/pagbank/validate-card
                # e recuperados temporariamente apenas para envio ao PagBank (não são armazenados)
                # Como o endpoint /cards do PagBank retorna 403, enviamos dados diretamente no payload
                
                # Limpar e validar tax_id do portador do cartão
                card_holder_tax_id = str(payment_data.get('card_holder_cpf_cnpj', '')).replace('.', '').replace('-', '').replace('/', '').strip()
                # Se não tiver tax_id, usar o do cliente como fallback
                if not card_holder_tax_id:
                    card_holder_tax_id = str(customer_data.get('tax_id', '')).replace('.', '').replace('-', '').replace('/', '').strip()
                
                # Converter exp_year para inteiro
                exp_year_str = str(payment_data.get('card_exp_year', ''))
                if len(exp_year_str) == 2:
                    current_year_prefix = str(datetime.datetime.now().year)[:2]
                    exp_year_int = int(current_year_prefix + exp_year_str)
                elif len(exp_year_str) == 4:
                    exp_year_int = int(exp_year_str)
                else:
                    exp_year_int = int(exp_year_str) if exp_year_str.isdigit() else datetime.datetime.now().year
                
                # Converter exp_month para inteiro
                exp_month_str = str(payment_data.get('card_exp_month', '')).strip()
                exp_month_int = int(exp_month_str) if exp_month_str.isdigit() else 12
                
                # Enviar dados do cartão diretamente ao PagBank (endpoint /cards não funciona)
                # Dados foram validados no endpoint isolado e são usados apenas uma vez aqui
                charge["payment_method"].update({
                    "capture": True,
                    "card": {
                        "number": payment_data.get('card_number', '').replace(' ', '').replace('-', ''),
                        "exp_month": exp_month_int,
                        "exp_year": exp_year_int,
                        "security_code": payment_data.get('card_cvv', ''),
                        "holder": {
                            "name": payment_data.get('card_holder_name', '') or customer_data.get('name', ''),
                            "tax_id": card_holder_tax_id
                        }
                    },
                    "installments": payment_data.get('installments', 1)
                })
            elif payment_method_type == 'BOLETO':
                # Validar valor mínimo de R$0,20 para boleto
                total_value_cents = int(payment_data.get('total_value', 0) * 100)
                if total_value_cents < 20:
                    raise Exception("O valor mínimo para pagamento via boleto é R$ 0,20")
                
                # Calcular data de vencimento (padrão: 3 dias)
                due_date = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
                days_until_expiration = 3
                
                # Preparar endereço do holder (formato específico para boleto)
                holder_address = {
                    "street": shipping_info.get('rua', ''),
                    "number": shipping_info.get('numero', ''),
                    "postal_code": shipping_info.get('cep', '').replace('-', ''),
                    "locality": shipping_info.get('bairro', ''),
                    "city": shipping_info.get('cidade', ''),
                    "region": shipping_info.get('estado', ''),
                    "region_code": shipping_info.get('estado', ''),
                    "country": "Brasil"
                }
                
                # Adicionar complemento se existir
                if shipping_info.get('complemento'):
                    holder_address["complement"] = shipping_info.get('complemento')
                
                charge["payment_method"].update({
                    "boleto": {
                        "template": "PROPOSTA",  # Tipo de boleto: PROPOSTA (padrão) ou COBRANCA
                        "due_date": due_date,
                        "days_until_expiration": str(days_until_expiration),
                        "instruction_lines": {
                            "line_1": "Não receber após o vencimento",
                            "line_2": "LhamaBanana - Sua Loja de Roupas"
                        },
                        "holder": {
                            "name": customer_data.get('name', ''),
                            "tax_id": customer_data.get('tax_id', '').replace('.', '').replace('-', '').replace('/', ''),
                            "email": customer_data.get('email', ''),
                            "address": holder_address
                        }
                    }
                })
            
            # Montar payload final com charges (para CREDIT_CARD e BOLETO)
            payload = {
                "reference_id": f"lhama-banana-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                "customer": customer,
                "items": items,
                "shipping": {
                    "address": shipping_address
                },
                "charges": [charge]
            }
        
        # Adicionar URL de notificação (OBRIGATÓRIO para webhooks funcionarem)
        # Usar valor hardcoded diretamente do config.py, ignorando variável de ambiente
        # URL do ngrok hardcoded (valor correto do config.py)
        notification_url = 'https://efractory-burdenless-kathlene.ngrok-free.dev/api/webhook/pagbank'
        
        current_app.logger.info(f"[PagBank] ✅ Usando URL de notificação (hardcoded do config.py): {notification_url}")
        
        # Remover barra final se houver
        notification_url = notification_url.rstrip('/')
        
        # Adicionar ao payload
        payload["notification_urls"] = [notification_url]
        current_app.logger.info(f"[PagBank] ✅ URL de notificação adicionada ao payload: {notification_url}")
        current_app.logger.info(f"[PagBank] Payload inclui notification_urls: {payload.get('notification_urls', [])}")
        
        return payload
        
    except Exception as e:
        current_app.logger.error(f"Erro ao criar payload PagBank: {e}")
        raise Exception(f"Erro ao preparar dados para PagBank: {e}")
