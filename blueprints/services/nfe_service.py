"""
Serviço para integração com API de emissão de Nota Fiscal Eletrônica (NFe)
"""
from typing import Optional, Dict, List
from ..services import get_db
from flask import current_app
import json

def check_and_emit_nfe(venda_id: int) -> Optional[Dict]:
    """
    Verifica se deve emitir NFe para uma venda e cria registro na tabela notas_fiscais.
    Esta função é chamada quando o status do pedido muda para 'processando_envio'.
    
    Args:
        venda_id: ID da venda/pedido
        
    Returns:
        Dict com informações da nota fiscal ou None se não foi possível criar
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verificar se já existe nota fiscal para esta venda
        cur.execute("""
            SELECT id, status_emissao 
            FROM notas_fiscais 
            WHERE venda_id = %s
        """, (venda_id,))
        
        existing_nfe = cur.fetchone()
        if existing_nfe and existing_nfe[1] in ['emitida', 'processando']:
            # Já existe NFe emitida ou em processamento
            current_app.logger.info(f"NFe já existe para venda {venda_id} com status {existing_nfe[1]}")
            return None
        
        # Buscar dados completos da venda
        cur.execute("""
            SELECT 
                v.id, v.codigo_pedido, v.valor_total, v.valor_frete, v.valor_desconto,
                v.fiscal_tipo, v.fiscal_cpf_cnpj, v.fiscal_nome_razao_social,
                v.fiscal_inscricao_estadual, v.fiscal_inscricao_municipal,
                v.fiscal_rua, v.fiscal_numero, v.fiscal_complemento,
                v.fiscal_bairro, v.fiscal_cidade, v.fiscal_estado, v.fiscal_cep,
                v.rua_entrega, v.numero_entrega, v.complemento_entrega,
                v.bairro_entrega, v.cidade_entrega, v.estado_entrega, v.cep_entrega
            FROM vendas v
            WHERE v.id = %s
        """, (venda_id,))
        
        venda_data = cur.fetchone()
        if not venda_data:
            current_app.logger.error(f"Venda {venda_id} não encontrada")
            return None
        
        # Verificar se tem dados fiscais
        if not venda_data[5] or not venda_data[6]:  # fiscal_tipo ou fiscal_cpf_cnpj
            current_app.logger.warning(f"Venda {venda_id} não possui dados fiscais completos")
            # Criar registro com status erro
            cur.execute("""
                INSERT INTO notas_fiscais (venda_id, codigo_pedido, status_emissao, erro_mensagem)
                VALUES (%s, %s, 'erro', 'Dados fiscais incompletos')
                RETURNING id
            """, (venda_id, venda_data[1]))
            nfe_id = cur.fetchone()[0]
            conn.commit()
            return {'id': nfe_id, 'status': 'erro', 'erro': 'Dados fiscais incompletos'}
        
        # Buscar itens da venda
        cur.execute("""
            SELECT 
                iv.quantidade, iv.preco_unitario, iv.subtotal,
                iv.nome_produto_snapshot, iv.sku_produto_snapshot,
                p.ncm, p.codigo_sku
            FROM itens_venda iv
            LEFT JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = %s
            ORDER BY iv.id
        """, (venda_id,))
        
        itens = cur.fetchall()
        
        if not itens:
            current_app.logger.error(f"Venda {venda_id} não possui itens")
            return None
        
        # Criar registro de NFe com status pendente
        cur.execute("""
            INSERT INTO notas_fiscais (venda_id, codigo_pedido, status_emissao)
            VALUES (%s, %s, 'pendente')
            RETURNING id
        """, (venda_id, venda_data[1]))
        
        nfe_id = cur.fetchone()[0]
        conn.commit()
        
        current_app.logger.info(f"Registro de NFe criado para venda {venda_id} (NFe ID: {nfe_id})")
        
        # Tentar emitir NF-e via Bling
        try:
            from .bling_nfe_service import emit_nfe_for_order
            bling_result = emit_nfe_for_order(venda_id)
            
            if bling_result.get('success'):
                current_app.logger.info(
                    f"✅ NF-e emitida via Bling para venda {venda_id}. "
                    f"Status: {bling_result.get('nfe_situacao')}"
                )
                # Situações que indicam nota autorizada: 5=AUTORIZADA, 6=EMITIDA_DANFE, 7=REGISTRADA
                nfe_situacao = bling_result.get('nfe_situacao', '')
                situacoes_autorizadas = ['EMITIDA', 'AUTORIZADA', 'AUTORIZADO', 'EMITIDA_DANFE', 'REGISTRADA']
                status_emitida = 'emitida' if nfe_situacao.upper() in [s.upper() for s in situacoes_autorizadas] else 'processando'
                
                return {
                    'id': nfe_id,
                    'venda_id': venda_id,
                    'codigo_pedido': venda_data[1],
                    'status': status_emitida,
                    'nfe_numero': bling_result.get('nfe_numero'),
                    'nfe_chave_acesso': bling_result.get('nfe_chave_acesso'),
                    'message': 'NF-e emitida via Bling com sucesso'
                }
            else:
                current_app.logger.warning(
                    f"⚠️ Falha ao emitir NF-e via Bling para venda {venda_id}: {bling_result.get('error')}. "
                    f"Registro criado com status 'pendente' para retry posterior."
                )
                return {
                    'id': nfe_id,
                    'venda_id': venda_id,
                    'codigo_pedido': venda_data[1],
                    'status': 'pendente',
                    'error': bling_result.get('error'),
                    'message': 'Registro criado. NF-e será emitida quando pedido estiver no Bling.'
                }
        except Exception as bling_error:
            current_app.logger.warning(
                f"⚠️ Erro ao tentar emitir NF-e via Bling: {bling_error}. "
                f"Registro criado com status 'pendente'."
            )
            return {
                'id': nfe_id,
                'venda_id': venda_id,
                'codigo_pedido': venda_data[1],
                'status': 'pendente',
                'message': 'Registro criado. NF-e será emitida quando pedido estiver no Bling.'
            }
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar registro de NFe para venda {venda_id}: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None
    finally:
        cur.close()


def get_nfe_by_venda_id(venda_id: int) -> Optional[Dict]:
    """
    Busca informações da NFe de uma venda
    
    Args:
        venda_id: ID da venda
        
    Returns:
        Dict com dados da NFe ou None se não encontrada
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT 
                id, venda_id, codigo_pedido, numero_nfe, serie_nfe, chave_acesso,
                status_emissao, api_response, erro_mensagem,
                data_emissao, data_cancelamento, criado_em, atualizado_em
            FROM notas_fiscais
            WHERE venda_id = %s
            ORDER BY criado_em DESC
            LIMIT 1
        """, (venda_id,))
        
        nfe_data = cur.fetchone()
        if not nfe_data:
            return None
        
        return {
            'id': nfe_data[0],
            'venda_id': nfe_data[1],
            'codigo_pedido': nfe_data[2],
            'numero_nfe': nfe_data[3],
            'serie_nfe': nfe_data[4],
            'chave_acesso': nfe_data[5],
            'status_emissao': nfe_data[6],
            'api_response': nfe_data[7] if nfe_data[7] else {},
            'erro_mensagem': nfe_data[8],
            'data_emissao': str(nfe_data[9]) if nfe_data[9] else None,
            'data_cancelamento': str(nfe_data[10]) if nfe_data[10] else None,
            'criado_em': str(nfe_data[11]) if nfe_data[11] else None,
            'atualizado_em': str(nfe_data[12]) if nfe_data[12] else None
        }
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar NFe para venda {venda_id}: {e}")
        return None
    finally:
        cur.close()



