"""
Serviços para gerenciar pedidos (orders) com token público
"""
import uuid
import psycopg2.extras
from typing import Optional, Dict
from flask import g, current_app
from .db import get_db


def create_order(venda_id: int, valor: float, status: str = 'CRIADO') -> Dict:
    """
    Cria um registro na tabela orders com token público
    
    Args:
        venda_id: ID da venda na tabela vendas
        valor: Valor total do pedido
        status: Status inicial do pedido (padrão: CRIADO)
        
    Returns:
        Dicionário com id, public_token e status do pedido criado
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Gerar token público único
        public_token = uuid.uuid4()
        
        cur.execute("""
            INSERT INTO orders (venda_id, public_token, status, valor)
            VALUES (%s, %s, %s, %s)
            RETURNING id, public_token, status, valor, criado_em, atualizado_em
        """, (venda_id, public_token, status, valor))
        
        result = cur.fetchone()
        conn.commit()
        
        order_data = {
            'id': str(result[0]),
            'public_token': str(result[1]),
            'status': result[2],
            'valor': float(result[3]),
            'criado_em': result[4].isoformat() if result[4] else None,
            'atualizado_em': result[5].isoformat() if result[5] else None
        }
        
        current_app.logger.info(f"Order criado: {order_data['id']} com token {order_data['public_token']}")
        return order_data
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar order: {e}")
        raise e
    finally:
        cur.close()


def get_order_by_token(public_token: str) -> Optional[Dict]:
    """
    Busca um pedido pelo token público
    
    Args:
        public_token: Token público do pedido
        
    Returns:
        Dicionário com dados do pedido ou None se não encontrado
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                o.id,
                o.venda_id,
                o.public_token,
                o.status,
                o.valor,
                o.criado_em,
                o.atualizado_em,
                v.codigo_pedido,
                v.data_venda,
                v.status_pedido as venda_status,
                p.status_pagamento,
                p.forma_pagamento_tipo,
                p.pagbank_qrcode_link,
                p.pagbank_qrcode_image,
                p.pagbank_boleto_link,
                p.pagbank_barcode_data,
                p.pagbank_boleto_expires_at,
                p.json_resposta_api
            FROM orders o
            LEFT JOIN vendas v ON o.venda_id = v.id
            LEFT JOIN pagamentos p ON v.id = p.venda_id
            WHERE o.public_token = %s
        """, (public_token,))
        
        result = cur.fetchone()
        
        if not result:
            return None
        
        # Extrair código PIX do JSON se disponível
        pix_qr_code_text = None
        json_resposta = result.get('json_resposta_api')
        if json_resposta and isinstance(json_resposta, dict):
            # Tentar extrair código PIX do JSON
            charges = json_resposta.get('charges', [])
            if charges:
                charge = charges[0]
                payment_method = charge.get('payment_method', {})
                if payment_method.get('type') == 'PIX':
                    pix_data = payment_method.get('pix', {})
                    qr_codes = pix_data.get('qr_codes', [])
                    if not qr_codes:
                        qr_codes = pix_data.get('qr_code', [])
                    if qr_codes and len(qr_codes) > 0:
                        pix_qr_code_text = qr_codes[0].get('text')
        
        # Converter para dicionário
        order_data = {
            'id': str(result['id']),
            'venda_id': result['venda_id'],
            'public_token': str(result['public_token']),
            'status': result['status'],
            'valor': float(result['valor']),
            'criado_em': result['criado_em'].isoformat() if result['criado_em'] else None,
            'atualizado_em': result['atualizado_em'].isoformat() if result['atualizado_em'] else None,
            'codigo_pedido': result['codigo_pedido'],
            'data_venda': result['data_venda'].isoformat() if result['data_venda'] else None,
            'venda_status': result['venda_status'],
            'status_pagamento': result['status_pagamento'],
            'forma_pagamento': result['forma_pagamento_tipo'],
            'pix_qr_code_link': result['pagbank_qrcode_link'],
            'pix_qr_code_image': result['pagbank_qrcode_image'],
            'pix_qr_code_text': pix_qr_code_text,
            'boleto_link': result['pagbank_boleto_link'],
            'boleto_barcode': result['pagbank_barcode_data'],
            'boleto_expires_at': result['pagbank_boleto_expires_at'].isoformat() if result['pagbank_boleto_expires_at'] else None
        }
        
        return order_data
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar order por token: {e}")
        raise e
    finally:
        cur.close()


def update_order_status(public_token: str, status: str) -> bool:
    """
    Atualiza o status de um pedido
    
    Args:
        public_token: Token público do pedido
        status: Novo status do pedido
        
    Returns:
        True se atualizado com sucesso, False caso contrário
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE orders
            SET status = %s, atualizado_em = NOW()
            WHERE public_token = %s
            RETURNING id
        """, (status, public_token))
        
        result = cur.fetchone()
        conn.commit()
        
        if result:
            current_app.logger.info(f"Status do order {public_token} atualizado para {status}")
            return True
        else:
            current_app.logger.warning(f"Order não encontrado para token {public_token}")
            return False
            
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao atualizar status do order: {e}")
        raise e
    finally:
        cur.close()


def delete_order_token(public_token: str) -> bool:
    """
    Remove o token público de um pedido (usado quando pedido é entregue)
    
    Args:
        public_token: Token público do pedido
        
    Returns:
        True se removido com sucesso, False caso contrário
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Não deleta o registro, apenas remove o token (seta para NULL)
        # Isso mantém o histórico mas impede acesso futuro
        cur.execute("""
            UPDATE orders
            SET public_token = NULL, atualizado_em = NOW()
            WHERE public_token = %s
            RETURNING id
        """, (public_token,))
        
        result = cur.fetchone()
        conn.commit()
        
        if result:
            current_app.logger.info(f"Token público removido do order {public_token}")
            return True
        else:
            current_app.logger.warning(f"Order não encontrado para token {public_token}")
            return False
            
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao remover token do order: {e}")
        raise e
    finally:
        cur.close()


def get_order_by_venda_id(venda_id: int) -> Optional[Dict]:
    """
    Busca um pedido pelo ID da venda
    
    Args:
        venda_id: ID da venda
        
    Returns:
        Dicionário com dados do pedido ou None se não encontrado
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                id, venda_id, public_token, status, valor, criado_em, atualizado_em
            FROM orders
            WHERE venda_id = %s
            ORDER BY criado_em DESC
            LIMIT 1
        """, (venda_id,))
        
        result = cur.fetchone()
        
        if not result:
            return None
        
        return {
            'id': str(result['id']),
            'venda_id': result['venda_id'],
            'public_token': str(result['public_token']) if result['public_token'] else None,
            'status': result['status'],
            'valor': float(result['valor']),
            'criado_em': result['criado_em'].isoformat() if result['criado_em'] else None,
            'atualizado_em': result['atualizado_em'].isoformat() if result['atualizado_em'] else None
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar order por venda_id: {e}")
        raise e
    finally:
        cur.close()

