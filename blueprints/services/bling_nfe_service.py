"""
Service para emissão de NF-e via Bling
========================================

Gerencia emissão automática de notas fiscais eletrônicas (NF-e) via API do Bling:
- Emissão automática após pagamento confirmado e pedido aprovado
- Consulta de status da NF-e
- Armazenamento de XML, chave de acesso, número
- Tratamento de erros fiscais
"""
from flask import current_app
from typing import Dict, Optional
from .db import get_db
from .bling_api_service import make_bling_api_request, BlingAPIError, BlingErrorType
from .bling_order_service import get_bling_order_by_local_id
import psycopg2.extras
from datetime import datetime
import json


def emit_nfe_via_bling(venda_id: int, pedido_bling_id: int) -> Dict:
    """
    Emite NF-e para um pedido no Bling
    
    O Bling gerencia a emissão de NF-e automaticamente quando solicitado.
    Esta função solicita a emissão da NF-e para o pedido.
    
    Args:
        venda_id: ID da venda local
        pedido_bling_id: ID do pedido no Bling
    
    Returns:
        Dict com resultado da emissão
    """
    try:
        # Solicitar emissão de NF-e para o pedido no Bling
        # O endpoint do Bling para emitir NF-e é POST /pedidos/vendas/{id}/gerar-nfe
        current_app.logger.info(f"📄 Solicitando emissão de NF-e para pedido Bling {pedido_bling_id} (venda {venda_id})...")
        
        response = make_bling_api_request(
            'POST',
            f'/pedidos/vendas/{pedido_bling_id}/gerar-nfe',
            json={}  # Bling pode não exigir body, ou pode exigir configurações
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            nfe_data = data.get('data', {})
            
            # Extrair informações da NF-e
            nfe_id = nfe_data.get('id') if isinstance(nfe_data, dict) else data.get('id')
            nfe_numero = nfe_data.get('numero') if isinstance(nfe_data, dict) else None
            nfe_chave_acesso = nfe_data.get('chaveAcesso') if isinstance(nfe_data, dict) else None
            nfe_situacao = nfe_data.get('situacao', 'PENDENTE') if isinstance(nfe_data, dict) else 'PENDENTE'
            nfe_xml = nfe_data.get('xml') if isinstance(nfe_data, dict) else None
            
            current_app.logger.info(
                f"✅ Emissão de NF-e solicitada para pedido {pedido_bling_id}. "
                f"Status: {nfe_situacao}, Número: {nfe_numero}"
            )
            
            # Salvar informações da NF-e
            save_nfe_info(venda_id, pedido_bling_id, nfe_id, nfe_numero, nfe_chave_acesso, nfe_xml, nfe_situacao, data)
            
            return {
                'success': True,
                'nfe_id': nfe_id,
                'nfe_numero': nfe_numero,
                'nfe_chave_acesso': nfe_chave_acesso,
                'nfe_situacao': nfe_situacao,
                'message': 'Emissão de NF-e solicitada com sucesso'
            }
        else:
            error_text = response.text
            current_app.logger.error(
                f"❌ Erro ao emitir NF-e para pedido {pedido_bling_id}: {response.status_code} - {error_text}"
            )
            
            # Salvar erro
            save_nfe_error(venda_id, f"Erro HTTP {response.status_code}: {error_text}")
            
            return {
                'success': False,
                'error': f"Erro HTTP {response.status_code}",
                'details': error_text
            }
            
    except BlingAPIError as e:
        current_app.logger.error(f"❌ Erro da API Bling ao emitir NF-e: {e}")
        save_nfe_error(venda_id, str(e))
        return {
            'success': False,
            'error': str(e),
            'error_type': e.error_type.value
        }
    except Exception as e:
        current_app.logger.error(f"❌ Erro inesperado ao emitir NF-e: {e}", exc_info=True)
        save_nfe_error(venda_id, str(e))
        return {
            'success': False,
            'error': str(e)
        }


def check_nfe_status(venda_id: int, pedido_bling_id: int) -> Dict:
    """
    Consulta status da NF-e de um pedido no Bling
    
    Args:
        venda_id: ID da venda local
        pedido_bling_id: ID do pedido no Bling
    
    Returns:
        Dict com status da NF-e
    """
    try:
        # Buscar pedido no Bling (inclui informações da NF-e)
        response = make_bling_api_request(
            'GET',
            f'/pedidos/vendas/{pedido_bling_id}'
        )
        
        if response.status_code == 200:
            data = response.json()
            pedido_data = data.get('data', {})
            
            # Extrair informações da NF-e do pedido
            nfe_data = pedido_data.get('notaFiscal', {})
            
            if nfe_data:
                nfe_id = nfe_data.get('id')
                nfe_numero = nfe_data.get('numero')
                nfe_chave_acesso = nfe_data.get('chaveAcesso')
                nfe_situacao = nfe_data.get('situacao', 'PENDENTE')
                nfe_xml = nfe_data.get('xml')
                
                # Atualizar informações da NF-e
                save_nfe_info(venda_id, pedido_bling_id, nfe_id, nfe_numero, nfe_chave_acesso, nfe_xml, nfe_situacao, nfe_data)
                
                return {
                    'success': True,
                    'nfe_id': nfe_id,
                    'nfe_numero': nfe_numero,
                    'nfe_chave_acesso': nfe_chave_acesso,
                    'nfe_situacao': nfe_situacao,
                    'has_xml': bool(nfe_xml)
                }
            else:
                return {
                    'success': True,
                    'nfe_situacao': 'NAO_EMITIDA',
                    'message': 'NF-e ainda não foi emitida para este pedido'
                }
        else:
            return {
                'success': False,
                'error': f"Erro HTTP {response.status_code}",
                'details': response.text
            }
            
    except BlingAPIError as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': e.error_type.value
        }
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao consultar status da NF-e: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def save_nfe_info(venda_id: int, pedido_bling_id: int, nfe_id: Optional[int],
                  nfe_numero: Optional[int], nfe_chave_acesso: Optional[str],
                  nfe_xml: Optional[str], nfe_situacao: str, api_response: Dict):
    """
    Salva informações da NF-e na tabela bling_pedidos e notas_fiscais
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Mapear situação do Bling para status local
        status_map = {
            'EMITIDA': 'emitida',
            'AUTORIZADA': 'emitida',
            'AUTORIZADO': 'emitida',
            'PENDENTE': 'processando',
            'PROCESSANDO': 'processando',
            'CANCELADA': 'cancelada',
            'CANCELADO': 'cancelada',
            'ERRO': 'erro',
            'REJEITADA': 'erro'
        }
        status_emissao = status_map.get(nfe_situacao.upper(), 'processando')
        
        # 1. Atualizar bling_pedidos
        cur.execute("""
            UPDATE bling_pedidos
            SET bling_nfe_id = %s,
                nfe_numero = %s,
                nfe_chave_acesso = %s,
                nfe_xml = %s,
                nfe_status = %s,
                updated_at = NOW()
            WHERE venda_id = %s
        """, (nfe_id, nfe_numero, nfe_chave_acesso, nfe_xml, nfe_situacao, venda_id))
        
        # 2. Atualizar ou criar registro em notas_fiscais
        cur.execute("""
            SELECT id FROM notas_fiscais WHERE venda_id = %s
        """, (venda_id,))
        
        existing = cur.fetchone()
        
        if existing:
            # Atualizar existente
            data_emissao = datetime.now() if status_emissao == 'emitida' else None
            cur.execute("""
                UPDATE notas_fiscais
                SET numero_nfe = %s,
                    serie_nfe = NULL,
                    chave_acesso = %s,
                    status_emissao = %s,
                    api_response = %s::jsonb,
                    data_emissao = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (
                str(nfe_numero) if nfe_numero else None,
                nfe_chave_acesso,
                status_emissao,
                json.dumps(api_response) if api_response else None,
                data_emissao,
                existing['id']
            ))
        else:
            # Criar novo registro
            data_emissao = datetime.now() if status_emissao == 'emitida' else None
            cur.execute("""
                INSERT INTO notas_fiscais (
                    venda_id, codigo_pedido, numero_nfe, chave_acesso,
                    status_emissao, api_response, data_emissao
                )
                SELECT 
                    %s, codigo_pedido, %s, %s, %s, %s::jsonb, %s
                FROM vendas
                WHERE id = %s
            """, (
                venda_id,
                str(nfe_numero) if nfe_numero else None,
                nfe_chave_acesso,
                status_emissao,
                json.dumps(api_response) if api_response else None,
                data_emissao,
                venda_id
            ))
        
        conn.commit()
        current_app.logger.info(f"✅ Informações da NF-e salvas para venda {venda_id}")
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"❌ Erro ao salvar informações da NF-e: {e}", exc_info=True)
        raise
    finally:
        cur.close()


def save_nfe_error(venda_id: int, error_message: str):
    """
    Salva erro de emissão de NF-e
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Atualizar ou criar registro com erro
        cur.execute("""
            SELECT id FROM notas_fiscais WHERE venda_id = %s
        """, (venda_id,))
        
        existing = cur.fetchone()
        
        if existing:
            cur.execute("""
                UPDATE notas_fiscais
                SET status_emissao = 'erro',
                    erro_mensagem = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (error_message, existing[0]))
        else:
            cur.execute("""
                INSERT INTO notas_fiscais (
                    venda_id, codigo_pedido, status_emissao, erro_mensagem
                )
                SELECT 
                    %s, codigo_pedido, 'erro', %s
                FROM vendas
                WHERE id = %s
            """, (venda_id, error_message, venda_id))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"❌ Erro ao salvar erro de NF-e: {e}", exc_info=True)
    finally:
        cur.close()


def emit_nfe_for_order(venda_id: int) -> Dict:
    """
    Emite NF-e para uma venda, verificando todas as condições necessárias
    
    Condições:
    1. Pagamento confirmado (status processando_envio ou superior)
    2. Pedido existe no Bling
    3. Dados fiscais completos
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da emissão
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # 1. Verificar status da venda
        cur.execute("""
            SELECT status_pedido, fiscal_cpf_cnpj, fiscal_nome_razao_social
            FROM vendas
            WHERE id = %s
        """, (venda_id,))
        
        venda = cur.fetchone()
        
        if not venda:
            return {
                'success': False,
                'error': f'Venda {venda_id} não encontrada'
            }
        
        # 2. Verificar se pagamento foi confirmado
        status_pedido = venda['status_pedido']
        if status_pedido not in ['processando_envio', 'enviado', 'entregue']:
            return {
                'success': False,
                'error': f'Venda {venda_id} ainda não está pronta para emissão de NF-e. Status: {status_pedido}',
                'current_status': status_pedido
            }
        
        # 3. Verificar dados fiscais
        if not venda['fiscal_cpf_cnpj'] or not venda['fiscal_nome_razao_social']:
            return {
                'success': False,
                'error': 'Dados fiscais incompletos. Não é possível emitir NF-e.'
            }
        
        # 4. Verificar se pedido existe no Bling
        bling_pedido = get_bling_order_by_local_id(venda_id)
        
        if not bling_pedido:
            return {
                'success': False,
                'error': 'Pedido não encontrado no Bling. Sincronize o pedido primeiro.',
                'hint': 'Use /api/bling/pedidos/sync/{venda_id} para sincronizar o pedido'
            }
        
        pedido_bling_id = bling_pedido['bling_pedido_id']
        
        # 5. Verificar se NF-e já foi emitida
        if bling_pedido.get('bling_nfe_id'):
            current_app.logger.info(
                f"ℹ️ NF-e já existe para venda {venda_id}. "
                f"Consultando status atual..."
            )
            return check_nfe_status(venda_id, pedido_bling_id)
        
        # 6. Emitir NF-e
        current_app.logger.info(
            f"📄 Emitindo NF-e para venda {venda_id} (pedido Bling: {pedido_bling_id})..."
        )
        
        return emit_nfe_via_bling(venda_id, pedido_bling_id)
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao emitir NF-e para venda {venda_id}: {e}", exc_info=True)
        save_nfe_error(venda_id, str(e))
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        cur.close()

