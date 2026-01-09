"""
Service para integração de Logística com Bling
===============================================

Sincroniza informações de logística entre:
- Melhor Envio (etiquetas, rastreamento)
- Bling (pedido com dados de envio)

Fluxo:
1. Etiqueta criada no Melhor Envio → Atualiza pedido no Bling com código de rastreamento
2. Status de entrega atualizado → Sincroniza status com Bling
3. Bling atualiza status → Atualiza sistema local (se necessário)
"""
from flask import current_app
from typing import Dict, Optional
from .db import get_db
from .bling_order_service import get_bling_order_by_local_id
from .bling_api_service import make_bling_api_request
import psycopg2.extras
import json


def sync_tracking_to_bling(venda_id: int, codigo_rastreamento: str, 
                           transportadora: str = None, url_rastreamento: str = None) -> Dict:
    """
    Sincroniza código de rastreamento com o pedido no Bling
    
    Quando uma etiqueta é criada/paga no Melhor Envio, atualiza o pedido no Bling
    com as informações de rastreamento.
    
    Args:
        venda_id: ID da venda local
        codigo_rastreamento: Código de rastreamento (ex: "AB123456789BR")
        transportadora: Nome da transportadora (opcional)
        url_rastreamento: URL de rastreamento (opcional)
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        # Verificar se pedido existe no Bling
        bling_pedido = get_bling_order_by_local_id(venda_id)
        
        if not bling_pedido:
            current_app.logger.warning(
                f"⚠️ Pedido {venda_id} não encontrado no Bling. "
                f"Código de rastreamento não será sincronizado."
            )
            return {
                'success': False,
                'error': 'Pedido não encontrado no Bling',
                'hint': 'Sincronize o pedido primeiro usando /api/bling/pedidos/sync/{venda_id}'
            }
        
        bling_pedido_id = bling_pedido['bling_pedido_id']
        
        # Buscar pedido atual no Bling
        response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro ao buscar pedido no Bling: HTTP {response.status_code}'
            }
        
        pedido_data = response.json().get('data', {})
        
        # Preparar dados de atualização
        # O Bling pode ter campo para código de rastreamento no pedido ou transporte
        update_data = {
            # Atualizar observações com código de rastreamento
            "observacoes": f"{pedido_data.get('observacoes', '')}\n\n📦 Código de Rastreamento: {codigo_rastreamento}"
        }
        
        # Se Bling suportar campo específico de rastreamento (verificar documentação)
        # update_data["codigoRastreamento"] = codigo_rastreamento
        
        # Se houver transporte, atualizar também
        if transportadora:
            if 'transporte' not in update_data:
                update_data['transporte'] = pedido_data.get('transporte', {})
            
            # Adicionar informações de transporte/rastreamento
            update_data['transporte']['codigoRastreamento'] = codigo_rastreamento
            if url_rastreamento:
                update_data['transporte']['urlRastreamento'] = url_rastreamento
        
        # Atualizar pedido no Bling
        current_app.logger.info(
            f"📦 Sincronizando código de rastreamento com Bling: "
            f"Pedido {bling_pedido_id} (venda {venda_id}), Código: {codigo_rastreamento}"
        )
        
        response = make_bling_api_request(
            'PUT',
            f'/pedidos/vendas/{bling_pedido_id}',
            json=update_data
        )
        
        if response.status_code in [200, 201]:
            current_app.logger.info(
                f"✅ Código de rastreamento sincronizado com Bling: {codigo_rastreamento}"
            )
            
            # Atualizar referência local se necessário
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            try:
                # Podemos armazenar código de rastreamento na tabela bling_pedidos se necessário
                # Por enquanto, está apenas nas observações do pedido no Bling
                conn.commit()
            except Exception as e:
                conn.rollback()
                current_app.logger.warning(f"⚠️ Erro ao atualizar referência local: {e}")
            finally:
                cur.close()
            
            return {
                'success': True,
                'message': 'Código de rastreamento sincronizado com Bling',
                'codigo_rastreamento': codigo_rastreamento,
                'bling_pedido_id': bling_pedido_id
            }
        else:
            error_text = response.text
            current_app.logger.error(
                f"❌ Erro ao sincronizar código de rastreamento: {response.status_code} - {error_text}"
            )
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code}',
                'details': error_text
            }
            
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao sincronizar código de rastreamento com Bling: {e}", exc_info=True
        )
        return {
            'success': False,
            'error': str(e)
        }


def sync_shipping_status_to_bling(venda_id: int, status_envio: str) -> Dict:
    """
    Sincroniza status de envio/entrega com o Bling
    
    Atualiza status do pedido no Bling baseado no status de entrega:
    - enviado → Status 'enviado' no Bling
    - entregue → Status 'entregue' no Bling
    
    Args:
        venda_id: ID da venda local
        status_envio: Status do envio ('enviado', 'entregue', etc.)
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        # Mapear status de envio para status do pedido
        status_map = {
            'enviado': 'enviado',
            'em_transito': 'enviado',
            'entregue': 'entregue',
            'cancelado': 'cancelado_pelo_vendedor'
        }
        
        novo_status = status_map.get(status_envio.lower())
        
        if not novo_status:
            return {
                'success': False,
                'error': f'Status de envio não mapeado: {status_envio}'
            }
        
        # Buscar referência do pedido no Bling
        bling_pedido = get_bling_order_by_local_id(venda_id)
        
        if not bling_pedido:
            return {
                'success': False,
                'error': 'Pedido não encontrado no Bling'
            }
        
        # Atualizar status do pedido local primeiro
        conn = get_db()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE vendas
                SET status_pedido = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (novo_status, venda_id))
            conn.commit()
            
            # Sincronizar status com Bling
            from .bling_order_service import sync_order_status_from_bling
            # Na verdade, vamos atualizar o Bling com o novo status
            # Buscar pedido no Bling e atualizar situação
            
            bling_pedido_id = bling_pedido['bling_pedido_id']
            
            # Buscar pedido atual
            response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
            
            if response.status_code == 200:
                pedido_data = response.json().get('data', {})
                
                # Mapear status local para situação Bling
                from .bling_order_service import map_status_to_bling_situacao
                # Importar diretamente a função
                situacao_bling = map_status_to_bling_situacao(novo_status)
                
                # Atualizar pedido no Bling
                update_data = {
                    "situacao": situacao_bling
                }
                
                response = make_bling_api_request(
                    'PUT',
                    f'/pedidos/vendas/{bling_pedido_id}',
                    json=update_data
                )
                
                if response.status_code in [200, 201]:
                    current_app.logger.info(
                        f"✅ Status de envio sincronizado com Bling: {status_envio} → {novo_status}"
                    )
                    return {
                        'success': True,
                        'status_local': novo_status,
                        'situacao_bling': situacao_bling,
                        'message': 'Status sincronizado com Bling'
                    }
            
            return {
                'success': False,
                'error': 'Erro ao atualizar status no Bling'
            }
            
        except Exception as e:
            conn.rollback()
            raise
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao sincronizar status de envio com Bling: {e}", exc_info=True
        )
        return {
            'success': False,
            'error': str(e)
        }


def sync_label_created_to_bling(venda_id: int, etiqueta_data: Dict) -> Dict:
    """
    Sincroniza criação de etiqueta (Melhor Envio) com Bling
    
    Quando uma etiqueta é criada/paga no Melhor Envio, atualiza o pedido no Bling
    com informações de rastreamento.
    
    Args:
        venda_id: ID da venda local
        etiqueta_data: Dict com dados da etiqueta (codigo_rastreamento, transportadora, etc.)
    
    Returns:
        Dict com resultado da sincronização
    """
    codigo_rastreamento = etiqueta_data.get('codigo_rastreamento') or etiqueta_data.get('melhor_envio_protocol')
    transportadora = etiqueta_data.get('transportadora_nome')
    url_rastreamento = etiqueta_data.get('url_rastreamento')
    
    if not codigo_rastreamento:
        current_app.logger.warning(
            f"⚠️ Etiqueta criada para venda {venda_id} mas sem código de rastreamento. "
            f"Não será sincronizado com Bling."
        )
        return {
            'success': False,
            'error': 'Código de rastreamento não disponível'
        }
    
    return sync_tracking_to_bling(
        venda_id=venda_id,
        codigo_rastreamento=codigo_rastreamento,
        transportadora=transportadora,
        url_rastreamento=url_rastreamento
    )


def get_shipping_info_from_bling(venda_id: int) -> Optional[Dict]:
    """
    Busca informações de logística/rastreamento do pedido no Bling
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com informações de rastreamento se encontradas, None caso contrário
    """
    try:
        bling_pedido = get_bling_order_by_local_id(venda_id)
        
        if not bling_pedido:
            return None
        
        bling_pedido_id = bling_pedido['bling_pedido_id']
        
        # Buscar pedido no Bling
        response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
        
        if response.status_code != 200:
            return None
        
        pedido_data = response.json().get('data', {})
        
        # Extrair informações de transporte/rastreamento
        transporte = pedido_data.get('transporte', {})
        observacoes = pedido_data.get('observacoes', '')
        
        # Tentar extrair código de rastreamento das observações (se foi adicionado)
        codigo_rastreamento = None
        if 'Código de Rastreamento:' in observacoes:
            # Extrair código das observações
            import re
            match = re.search(r'Código de Rastreamento:\s*([A-Z0-9]+)', observacoes)
            if match:
                codigo_rastreamento = match.group(1)
        
        # Se Bling tiver campo específico (verificar API)
        if not codigo_rastreamento:
            codigo_rastreamento = transporte.get('codigoRastreamento')
        
        if codigo_rastreamento:
            return {
                'codigo_rastreamento': codigo_rastreamento,
                'url_rastreamento': transporte.get('urlRastreamento'),
                'transportadora': transporte.get('transportadora')
            }
        
        return None
        
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao buscar informações de logística do Bling: {e}", exc_info=True
        )
        return None

