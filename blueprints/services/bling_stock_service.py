"""
Service para gerenciamento de estoque com Bling
================================================

Gerencia sincronização de estoque considerando:
- Vendas confirmadas (atualizar Bling)
- Cancelamentos (reverter estoque)
- Consistência entre sistemas
"""
from flask import current_app
from typing import Dict, Optional, List
from .db import get_db
from .bling_product_service import sync_stock_to_bling, sync_stock_from_bling
import psycopg2.extras


def update_stock_after_sale(venda_id: int, sync_to_bling: bool = True) -> Dict:
    """
    Atualiza estoque no Bling após venda confirmada
    
    Quando uma venda é confirmada (pagamento aprovado), o estoque já foi
    decrementado localmente. Esta função sincroniza o estoque com o Bling.
    
    Args:
        venda_id: ID da venda
        sync_to_bling: Se True, sincroniza estoque para Bling
        
    Returns:
        Dict com resultado da operação
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar itens da venda
        cur.execute("""
            SELECT iv.produto_id, iv.quantidade, p.codigo_sku
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = %s
        """, (venda_id,))
        
        itens = cur.fetchall()
        
        if not itens:
            return {
                'success': False,
                'error': f'Nenhum item encontrado para venda {venda_id}'
            }
        
        results = []
        
        for item in itens:
            produto_id = item['produto_id']
            quantidade = item['quantidade']
            
            try:
                # Buscar estoque atual local
                cur.execute("""
                    SELECT p.estoque, bp.bling_id, bp.status_sincronizacao
                    FROM produtos p
                    LEFT JOIN bling_produtos bp ON p.id = bp.produto_id
                    WHERE p.id = %s
                """, (produto_id,))
                
                produto_data = cur.fetchone()
                
                if not produto_data:
                    results.append({
                        'produto_id': produto_id,
                        'success': False,
                        'error': 'Produto não encontrado'
                    })
                    continue
                
                estoque_atual = produto_data['estoque']
                bling_id = produto_data['bling_id']
                esta_sincronizado = produto_data['status_sincronizacao'] == 'sync'
                
                # Log da operação
                current_app.logger.info(
                    f"📦 Atualizando estoque após venda {venda_id}: "
                    f"Produto {produto_id} (SKU: {item['codigo_sku']}), "
                    f"Estoque local: {estoque_atual}"
                )
                
                # Se produto está sincronizado com Bling e sync_to_bling=True, atualizar Bling
                if esta_sincronizado and sync_to_bling and bling_id:
                    sync_result = sync_stock_to_bling(produto_id=produto_id)
                    
                    if sync_result.get('success') or sync_result.get('success', 0) > 0:
                        current_app.logger.info(
                            f"✅ Estoque do produto {produto_id} sincronizado com Bling após venda {venda_id}"
                        )
                        results.append({
                            'produto_id': produto_id,
                            'success': True,
                            'estoque_local': estoque_atual,
                            'bling_synced': True
                        })
                    else:
                        current_app.logger.warning(
                            f"⚠️ Falha ao sincronizar estoque do produto {produto_id} com Bling: "
                            f"{sync_result.get('error', 'Erro desconhecido')}"
                        )
                        results.append({
                            'produto_id': produto_id,
                            'success': True,  # Local já atualizado, apenas falhou no Bling
                            'estoque_local': estoque_atual,
                            'bling_synced': False,
                            'error': sync_result.get('error')
                        })
                else:
                    # Produto não sincronizado com Bling - apenas log
                    if not esta_sincronizado:
                        current_app.logger.debug(
                            f"ℹ️ Produto {produto_id} não está sincronizado com Bling. "
                            f"Estoque local atualizado para {estoque_atual}"
                        )
                    results.append({
                        'produto_id': produto_id,
                        'success': True,
                        'estoque_local': estoque_atual,
                        'bling_synced': False,
                        'reason': 'Produto não sincronizado com Bling'
                    })
                    
            except Exception as e:
                current_app.logger.error(
                    f"❌ Erro ao atualizar estoque do produto {item['produto_id']} após venda {venda_id}: {e}",
                    exc_info=True
                )
                results.append({
                    'produto_id': item['produto_id'],
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'venda_id': venda_id,
            'total_itens': len(itens),
            'results': results
        }
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao atualizar estoque após venda {venda_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'venda_id': venda_id
        }
    finally:
        cur.close()


def revert_stock_on_cancellation(venda_id: int, sync_to_bling: bool = True) -> Dict:
    """
    Reverte estoque quando pedido é cancelado/devolvido/reembolsado
    
    Quando um pedido é cancelado, o estoque deve ser revertido (incrementado)
    tanto localmente quanto no Bling.
    
    Args:
        venda_id: ID da venda cancelada
        sync_to_bling: Se True, sincroniza estoque para Bling após reverter
        
    Returns:
        Dict com resultado da operação
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar itens da venda
        cur.execute("""
            SELECT iv.produto_id, iv.quantidade, p.codigo_sku, p.estoque
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = %s
        """, (venda_id,))
        
        itens = cur.fetchall()
        
        if not itens:
            return {
                'success': False,
                'error': f'Nenhum item encontrado para venda {venda_id}'
            }
        
        results = []
        
        for item in itens:
            produto_id = item['produto_id']
            quantidade = item['quantidade']
            estoque_anterior = item['estoque']
            
            try:
                # Verificar se produto está sincronizado com Bling
                cur.execute("""
                    SELECT bp.bling_id, bp.status_sincronizacao
                    FROM bling_produtos bp
                    WHERE bp.produto_id = %s
                """, (produto_id,))
                
                bling_data = cur.fetchone()
                esta_sincronizado = bling_data and bling_data['status_sincronizacao'] == 'sync'
                bling_id = bling_data['bling_id'] if bling_data else None
                
                # Reverter estoque localmente (incrementar)
                cur.execute("""
                    UPDATE produtos
                    SET estoque = estoque + %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                    RETURNING estoque
                """, (quantidade, produto_id))
                
                novo_estoque = cur.fetchone()[0]
                conn.commit()
                
                current_app.logger.info(
                    f"🔄 Revertendo estoque do cancelamento {venda_id}: "
                    f"Produto {produto_id} (SKU: {item['codigo_sku']}), "
                    f"Quantidade: +{quantidade}, "
                    f"Estoque anterior: {estoque_anterior} → novo: {novo_estoque}"
                )
                
                # Se produto está sincronizado com Bling e sync_to_bling=True, atualizar Bling
                if esta_sincronizado and sync_to_bling and bling_id:
                    sync_result = sync_stock_to_bling(produto_id=produto_id)
                    
                    if sync_result.get('success') or sync_result.get('success', 0) > 0:
                        current_app.logger.info(
                            f"✅ Estoque do produto {produto_id} revertido e sincronizado com Bling após cancelamento {venda_id}"
                        )
                        results.append({
                            'produto_id': produto_id,
                            'success': True,
                            'quantidade_revertida': quantidade,
                            'estoque_anterior': estoque_anterior,
                            'estoque_novo': novo_estoque,
                            'bling_synced': True
                        })
                    else:
                        current_app.logger.warning(
                            f"⚠️ Falha ao sincronizar estoque revertido do produto {produto_id} com Bling: "
                            f"{sync_result.get('error', 'Erro desconhecido')}"
                        )
                        results.append({
                            'produto_id': produto_id,
                            'success': True,  # Local já revertido, apenas falhou no Bling
                            'quantidade_revertida': quantidade,
                            'estoque_novo': novo_estoque,
                            'bling_synced': False,
                            'error': sync_result.get('error')
                        })
                else:
                    # Produto não sincronizado com Bling - apenas revertido localmente
                    if not esta_sincronizado:
                        current_app.logger.debug(
                            f"ℹ️ Produto {produto_id} não está sincronizado com Bling. "
                            f"Estoque local revertido para {novo_estoque}"
                        )
                    results.append({
                        'produto_id': produto_id,
                        'success': True,
                        'quantidade_revertida': quantidade,
                        'estoque_novo': novo_estoque,
                        'bling_synced': False,
                        'reason': 'Produto não sincronizado com Bling'
                    })
                    
            except Exception as e:
                conn.rollback()
                current_app.logger.error(
                    f"❌ Erro ao reverter estoque do produto {item['produto_id']} após cancelamento {venda_id}: {e}",
                    exc_info=True
                )
                results.append({
                    'produto_id': item['produto_id'],
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'venda_id': venda_id,
            'total_itens': len(itens),
            'results': results
        }
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"❌ Erro ao reverter estoque após cancelamento {venda_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'venda_id': venda_id
        }
    finally:
        cur.close()


def handle_order_status_change(venda_id: int, old_status: str, new_status: str) -> Dict:
    """
    Gerencia mudança de status do pedido e atualiza estoque conforme necessário
    
    Regras:
    - Se mudou para 'processando_envio' (pagamento confirmado): estoque já foi decrementado, apenas sincronizar Bling
    - Se mudou para cancelado/devolvido/reembolsado: reverter estoque
    - Outros status: não afetam estoque
    
    Args:
        venda_id: ID da venda
        old_status: Status anterior
        new_status: Novo status
        
    Returns:
        Dict com resultado da operação
    """
    # Status que requerem sincronização de estoque (já decrementado)
    sync_stock_statuses = ['processando_envio', 'enviado', 'entregue']
    
    # Status que requerem reversão de estoque
    revert_stock_statuses = [
        'cancelado_pelo_cliente',
        'cancelado_pelo_vendedor',
        'devolvido',
        'reembolsado'
    ]
    
    # Se mudou para status que requer sincronização (estoque já foi decrementado na criação)
    if new_status in sync_stock_statuses and old_status not in sync_stock_statuses:
        current_app.logger.info(
            f"📦 Pedido {venda_id} mudou para {new_status}. "
            f"Sincronizando estoque com Bling..."
        )
        return update_stock_after_sale(venda_id, sync_to_bling=True)
    
    # Se mudou para status de cancelamento (reverter estoque)
    elif new_status in revert_stock_statuses and old_status not in revert_stock_statuses:
        current_app.logger.info(
            f"🔄 Pedido {venda_id} mudou para {new_status}. "
            f"Revertendo estoque..."
        )
        return revert_stock_on_cancellation(venda_id, sync_to_bling=True)
    
    # Outros status não afetam estoque
    else:
        current_app.logger.debug(
            f"ℹ️ Mudança de status do pedido {venda_id} "
            f"({old_status} → {new_status}) não requer alteração de estoque"
        )
        return {
            'success': True,
            'venda_id': venda_id,
            'message': 'Mudança de status não requer alteração de estoque',
            'old_status': old_status,
            'new_status': new_status
        }


def ensure_stock_consistency(produto_id: Optional[int] = None) -> Dict:
    """
    Garante consistência de estoque entre LhamaBanana e Bling
    
    Compara estoque local com estoque do Bling e sincroniza se necessário.
    Por padrão, o Bling é considerado fonte de verdade para estoque.
    
    Args:
        produto_id: ID do produto (None = todos os produtos sincronizados)
        
    Returns:
        Dict com resultado da verificação e sincronização
    """
    current_app.logger.info(
        f"🔍 Verificando consistência de estoque{f' (produto {produto_id})' if produto_id else ' (todos os produtos)'}..."
    )
    
    # Sincronizar do Bling para local (Bling é fonte de verdade)
    result = sync_stock_from_bling(produto_id=produto_id)
    
    if result.get('success') or result.get('success', 0) > 0:
        current_app.logger.info(
            f"✅ Consistência de estoque verificada: "
            f"{result.get('success', 0)} produtos sincronizados"
        )
    else:
        current_app.logger.warning(
            f"⚠️ Alguns produtos podem estar inconsistentes: "
            f"{result.get('errors', 0)} erros durante sincronização"
        )
    
    return result

