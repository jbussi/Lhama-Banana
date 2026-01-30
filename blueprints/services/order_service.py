"""
Serviços para gerenciar pedidos (orders) com token público

ARQUITETURA:
===========
O webhook do PagBank é a ÚNICA fonte de verdade do status do pagamento.
Status inicial SEMPRE deve ser PENDENTE no checkout.

IMPORTANTE: A tabela vendas.status_pedido é a fonte de verdade do status.
A tabela orders.status é sincronizada automaticamente quando buscar o pedido.
"""
import uuid
import psycopg2.extras
from typing import Optional, Dict
from flask import g, current_app
from .db import get_db


def map_venda_status_to_order_status(venda_status: str, status_pagamento: Optional[str] = None) -> str:
    """
    Mapeia o status da tabela vendas (status_pedido) para o status da tabela orders.
    
    A tabela vendas tem status mais detalhados, enquanto orders tem status simplificados.
    
    Args:
        venda_status: Status da tabela vendas (status_pedido)
        status_pagamento: Status do pagamento (PAID, PENDING, etc.)
    
    Returns:
        Status mapeado para a tabela orders
    """
    # Mapeamento de status_pedido para status da tabela orders
    # IMPORTANTE: 'pagamento_aprovado' só aparece quando situação Bling for "Em andamento" (ID 15)
    status_map = {
        # Status de pagamento
        'pendente': 'PENDENTE',
        'pendente_pagamento': 'PENDENTE',
        
        # Status de processamento
        'pagamento_aprovado': 'APROVADO',  # "Em andamento" no Bling (ID 15) - APROVADO só aqui
        'sincronizado_bling': 'PAGO',  # "Em aberto" no Bling - ainda não está em processamento
        'em_processamento': 'APROVADO',  # Outros status de processamento
        'processando_envio': 'APROVADO',
        
        # Status de NF-e
        'nfe_aguardando_aprovacao': 'APROVADO',
        'nfe_autorizada': 'APROVADO',
        'nfe_enviada_email': 'APROVADO',
        
        # Status de envio
        'estoque_baixado': 'APROVADO',
        'etiqueta_solicitada': 'APROVADO',
        'etiqueta_gerada': 'NA TRANSPORTADORA',
        'rastreamento_atualizado': 'NA TRANSPORTADORA',
        'pronto_envio': 'NA TRANSPORTADORA',
        'enviado': 'NA TRANSPORTADORA',
        
        # Status final
        'entregue': 'ENTREGUE',
        
        # Status de cancelamento
        'cancelado_pelo_cliente': 'CANCELADO',
        'cancelado_pelo_vendedor': 'CANCELADO',
        'devolvido': 'CANCELADO',
        'reembolsado': 'CANCELADO',
        
        # Status de erro (tratar como APROVADO para não bloquear visualização)
        'erro_nfe_timeout': 'APROVADO',
        'erro_processamento': 'APROVADO',
        'erro_etiqueta': 'APROVADO',
        'erro_estoque': 'APROVADO'
    }
    
    # Se status_pagamento for PAID, garantir que não fique como PENDENTE
    if status_pagamento == 'PAID' and venda_status in ['pendente', 'pendente_pagamento']:
        return 'PAGO'
    
    # Retornar status mapeado ou PENDENTE como fallback
    return status_map.get(venda_status, 'PENDENTE')


def create_order(venda_id: int, valor: float, status: str = 'PENDENTE') -> Dict:
    """
    Cria um registro na tabela orders com token público
    
    IMPORTANTE: No checkout, o status inicial deve SEMPRE ser 'PENDENTE'.
    O webhook do PagBank é a única fonte de verdade para atualização do status.
    
    Args:
        venda_id: ID da venda na tabela vendas
        valor: Valor total do pedido
        status: Status inicial do pedido (padrão: PENDENTE)
        
    Returns:
        Dicionário com id, public_token e status do pedido criado
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verificar se a tabela orders existe, se não, criar
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'orders'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            current_app.logger.info("Tabela orders não existe. Criando...")
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
                        public_token UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
                        status VARCHAR(50) NOT NULL DEFAULT 'CRIADO' CHECK (status IN (
                            'CRIADO', 
                            'PENDENTE', 
                            'PAGO', 
                            'APROVADO', 
                            'CANCELADO', 
                            'EXPIRADO', 
                            'NA TRANSPORTADORA', 
                            'ENTREGUE'
                        )),
                        valor DECIMAL(10, 2) NOT NULL,
                        token_expires_at TIMESTAMP,
                        criado_em TIMESTAMP DEFAULT NOW(),
                        atualizado_em TIMESTAMP DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_orders_venda_id ON orders (venda_id)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_orders_public_token ON orders (public_token)
                """)
                conn.commit()
                current_app.logger.info("Tabela orders criada com sucesso")
            except Exception as create_error:
                conn.rollback()
                current_app.logger.warning(f"Erro ao criar tabela orders (pode já existir): {create_error}")
        
        # Gerar token público único (convertido para string)
        public_token = str(uuid.uuid4())
        
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
        # Verificar se a tabela etiquetas_frete e a tabela de link existem
        cur.execute("""
            SELECT 
                EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'etiquetas_frete'
                ) as tabela_existe,
                EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'etiquetas_frete_venda_lnk'
                ) as link_existe
        """)
        result_check = cur.fetchone()
        etiquetas_table_exists = result_check[0] if result_check else False
        link_table_exists = result_check[1] if result_check else False
        
        # Construir a query base
        base_query = """
            SELECT 
                o.id,
                o.venda_id,
                o.public_token,
                o.status,
                o.valor,
                o.criado_em,
                o.atualizado_em,
                v.codigo_pedido,
                COALESCE(v.data_venda, v.created_at, o.criado_em) as data_venda,
                v.status_pedido as venda_status,
                p.status_pagamento,
                p.forma_pagamento_tipo,
                p.pagbank_qrcode_link,
                p.pagbank_qrcode_image,
                p.pagbank_boleto_link,
                p.pagbank_barcode_data,
                p.pagbank_boleto_expires_at,
                p.json_resposta_api
        """
        
        # Adicionar campos de etiquetas_frete apenas se ambas as tabelas existirem
        # Nota: etiquetas_frete usa tabela de link (etiquetas_frete_venda_lnk) para relacionar com vendas
        if etiquetas_table_exists and link_table_exists:
            base_query += """,
                e.url_rastreamento,
                e.codigo_rastreamento,
                e.transportadora_nome,
                e.status_etiqueta
            FROM orders o
            LEFT JOIN vendas v ON o.venda_id = v.id
            LEFT JOIN pagamentos p ON v.id = p.venda_id
            LEFT JOIN (
                SELECT DISTINCT ON (lnk.venda_id)
                    lnk.venda_id,
                    ef.url_rastreamento,
                    ef.codigo_rastreamento,
                    ef.transportadora_nome,
                    ef.status_etiqueta
                FROM etiquetas_frete_venda_lnk lnk
                INNER JOIN etiquetas_frete ef ON lnk.etiqueta_frete_id = ef.id
                WHERE lnk.venda_id IS NOT NULL
                ORDER BY lnk.venda_id, ef.created_at DESC NULLS LAST
            ) e ON v.id = e.venda_id
            WHERE o.public_token = %s
            """
        else:
            # Se a tabela não existir, usar NULL para os campos de etiqueta
            base_query += """,
                NULL as url_rastreamento,
                NULL as codigo_rastreamento,
                NULL as transportadora_nome,
                NULL as status_etiqueta
            FROM orders o
            LEFT JOIN vendas v ON o.venda_id = v.id
            LEFT JOIN pagamentos p ON v.id = p.venda_id
            WHERE o.public_token = %s
            """
        
        cur.execute(base_query, (public_token,))
        
        result = cur.fetchone()
        
        if not result:
            return None
        
        # Extrair código PIX do JSON se disponível
        pix_qr_code_text = None
        json_resposta = result.get('json_resposta_api')
        
        # Se json_resposta é string, fazer parse
        if json_resposta and isinstance(json_resposta, str):
            import json
            try:
                json_resposta = json.loads(json_resposta)
            except (json.JSONDecodeError, TypeError):
                json_resposta = None
        
        if json_resposta and isinstance(json_resposta, dict):
            # Para PIX, os dados vêm em qr_codes no nível raiz, não dentro de charges
            qr_codes = json_resposta.get('qr_codes', [])
            if qr_codes and len(qr_codes) > 0:
                # PIX: extrair do qr_codes no nível raiz
                pix_qr_code_text = qr_codes[0].get('text')
            else:
                # Fallback: tentar dentro de charges (estrutura alternativa)
                charges = json_resposta.get('charges', [])
                if charges:
                    charge = charges[0]
                    payment_method = charge.get('payment_method', {})
                    if payment_method.get('type') == 'PIX':
                        pix_data = payment_method.get('pix', {})
                        qr_codes_in_charge = pix_data.get('qr_codes', [])
                        if not qr_codes_in_charge:
                            qr_codes_in_charge = pix_data.get('qr_code', [])
                        if qr_codes_in_charge and len(qr_codes_in_charge) > 0:
                            pix_qr_code_text = qr_codes_in_charge[0].get('text')
        
        # IMPORTANTE: A fonte de verdade do status é a tabela vendas (status_pedido)
        # Mapear status_pedido da tabela vendas para o formato da tabela orders
        venda_status = result['venda_status'] or 'PENDENTE'
        status_pagamento = result['status_pagamento']
        
        # Mapear status_pedido para status da tabela orders
        status_mapped = map_venda_status_to_order_status(venda_status, status_pagamento)
        
        # Se o status na tabela orders estiver desatualizado, sincronizar
        if result['status'] != status_mapped:
            current_app.logger.info(
                f"🔄 Sincronizando status do order {result['public_token']}: "
                f"{result['status']} -> {status_mapped} (venda_status: {venda_status})"
            )
            try:
                cur.execute("""
                    UPDATE orders
                    SET status = %s, atualizado_em = NOW()
                    WHERE public_token = %s
                """, (status_mapped, public_token))
                conn.commit()
            except Exception as sync_error:
                current_app.logger.warning(f"Erro ao sincronizar status: {sync_error}")
                conn.rollback()
        
        # Converter para dicionário
        # Formatar datas para ISO string com timezone UTC explícito
        from datetime import datetime, timezone, timedelta
        
        def format_datetime_to_iso_utc(dt_value):
            """Converte datetime para ISO string com timezone UTC explícito"""
            if not dt_value:
                return None
            if hasattr(dt_value, 'isoformat'):
                # Se já tem timezone, usar diretamente
                if dt_value.tzinfo is None:
                    # Se não tem timezone, assumir UTC
                    dt_value = dt_value.replace(tzinfo=timezone.utc)
                return dt_value.isoformat()
            elif isinstance(dt_value, str):
                # Se já é string, verificar se tem timezone
                if 'Z' in dt_value or '+' in dt_value or dt_value.endswith('UTC'):
                    return dt_value
                else:
                    # Se não tem timezone, adicionar Z (UTC)
                    return dt_value + 'Z' if not dt_value.endswith('Z') else dt_value
            return None
        
        # Formatar data_venda para ISO string se for datetime
        # Usar COALESCE para garantir que sempre tenha uma data (data_venda, criado_em da venda, ou criado_em do order)
        data_venda_iso = None
        data_venda_raw = result.get('data_venda')
        if not data_venda_raw:
            # Fallback para criado_em da venda ou do order
            data_venda_raw = result.get('criado_em')
        
        data_venda_iso = format_datetime_to_iso_utc(data_venda_raw)
        
        # Formatar atualizado_em com timezone UTC explícito
        atualizado_em_iso = format_datetime_to_iso_utc(result.get('atualizado_em'))
        criado_em_iso = format_datetime_to_iso_utc(result.get('criado_em'))
        
        order_data = {
            'id': str(result['id']),
            'venda_id': result['venda_id'],
            'public_token': str(result['public_token']),
            'status': status_mapped,  # Usar status mapeado (sincronizado)
            'valor': float(result['valor']),
            'criado_em': criado_em_iso,
            'atualizado_em': atualizado_em_iso,
            'codigo_pedido': result['codigo_pedido'],
            'data_venda': data_venda_iso,  # Data formatada com timezone UTC explícito
            'venda_status': venda_status,  # Status original da tabela vendas
            'status_pagamento': status_pagamento,
            'forma_pagamento': result['forma_pagamento_tipo'],
            'pix_qr_code_link': result['pagbank_qrcode_link'],
            'pix_qr_code_image': result['pagbank_qrcode_image'],
            'pix_qr_code_text': pix_qr_code_text,
            'boleto_link': result['pagbank_boleto_link'],
            'boleto_barcode': result['pagbank_barcode_data'],
            'boleto_expires_at': result['pagbank_boleto_expires_at'].isoformat() if result['pagbank_boleto_expires_at'] else None,
            # Informações de rastreio (podem ser NULL se a tabela etiquetas_frete não existir)
            'url_rastreamento': result.get('url_rastreamento'),
            'codigo_rastreamento': result.get('codigo_rastreamento'),
            'transportadora_nome': result.get('transportadora_nome'),
            'status_etiqueta': result.get('status_etiqueta')
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


def sync_order_status_from_venda(venda_id: int) -> bool:
    """
    Sincroniza o status da tabela orders com o status da tabela vendas.
    Deve ser chamado sempre que o status_pedido da tabela vendas mudar.
    
    Args:
        venda_id: ID da venda
    
    Returns:
        True se sincronizado com sucesso, False caso contrário
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar status atual da venda e status do pagamento
        cur.execute("""
            SELECT 
                v.status_pedido,
                p.status_pagamento
            FROM vendas v
            LEFT JOIN pagamentos p ON v.id = p.venda_id
            WHERE v.id = %s
            ORDER BY p.criado_em DESC
            LIMIT 1
        """, (venda_id,))
        
        result = cur.fetchone()
        if not result:
            return False
        
        venda_status = result['status_pedido'] or 'pendente_pagamento'
        status_pagamento = result['status_pagamento']
        
        # Mapear para status da tabela orders
        status_mapped = map_venda_status_to_order_status(venda_status, status_pagamento)
        
        # Buscar order relacionado
        cur.execute("""
            SELECT public_token, status
            FROM orders
            WHERE venda_id = %s
            ORDER BY criado_em DESC
            LIMIT 1
        """, (venda_id,))
        
        order_result = cur.fetchone()
        if not order_result:
            # Não há order relacionado, não precisa sincronizar
            return True
        
        # Se o status estiver diferente, atualizar
        if order_result['status'] != status_mapped:
            cur.execute("""
                UPDATE orders
                SET status = %s, atualizado_em = NOW()
                WHERE public_token = %s
            """, (status_mapped, order_result['public_token']))
            conn.commit()
            current_app.logger.info(
                f"🔄 Status do order sincronizado: venda {venda_id}, "
                f"status {order_result['status']} -> {status_mapped} "
                f"(venda_status: {venda_status})"
            )
        
        return True
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao sincronizar status do order: {e}")
        return False
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

