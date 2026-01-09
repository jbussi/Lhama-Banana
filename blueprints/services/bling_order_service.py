"""
Service para sincronização de pedidos/vendas com Bling
=======================================================

Este módulo implementa a sincronização de vendas do LhamaBanana para o Bling.
"""
from flask import current_app
from typing import Dict, Optional, List
import time
import json
import psycopg2.extras
from .db import get_db
from .bling_api_service import make_bling_api_request


def get_order_for_bling_sync(venda_id: int) -> Optional[Dict]:
    """
    Busca venda completa do banco com todas as informações necessárias para Bling
    
    Returns:
        Dict com dados da venda ou None se não encontrado
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar dados da venda
        cur.execute("""
            SELECT 
                v.id,
                v.codigo_pedido,
                v.valor_total,
                v.valor_frete,
                v.valor_desconto,
                v.valor_subtotal,
                v.status_pedido,
                v.data_venda,
                -- Dados de entrega
                v.nome_recebedor,
                v.rua_entrega,
                v.numero_entrega,
                v.complemento_entrega,
                v.bairro_entrega,
                v.cidade_entrega,
                v.estado_entrega,
                v.cep_entrega,
                v.telefone_entrega,
                v.email_entrega,
                -- Dados fiscais
                v.fiscal_tipo,
                v.fiscal_cpf_cnpj,
                v.fiscal_nome_razao_social,
                v.fiscal_inscricao_estadual,
                v.fiscal_rua,
                v.fiscal_numero,
                v.fiscal_complemento,
                v.fiscal_bairro,
                v.fiscal_cidade,
                v.fiscal_estado,
                v.fiscal_cep,
                -- Dados do usuário (se existir)
                u.nome as usuario_nome,
                u.email as usuario_email
            FROM vendas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.id = %s
        """, (venda_id,))
        
        venda = cur.fetchone()
        
        if not venda:
            return None
        
        # Buscar itens da venda
        cur.execute("""
            SELECT 
                iv.id,
                iv.produto_id,
                iv.quantidade,
                iv.preco_unitario,
                iv.subtotal,
                iv.nome_produto_snapshot,
                iv.sku_produto_snapshot,
                -- Buscar referência Bling do produto
                bp.bling_id as bling_produto_id,
                bp.bling_codigo as bling_produto_codigo
            FROM itens_venda iv
            LEFT JOIN bling_produtos bp ON iv.produto_id = bp.produto_id
            WHERE iv.venda_id = %s
        """, (venda_id,))
        
        itens = cur.fetchall()
        
        venda_dict = dict(venda)
        venda_dict['itens'] = [dict(item) for item in itens]
        
        return venda_dict
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar venda {venda_id}: {e}")
        return None
    finally:
        cur.close()


def calculate_cfop(estado_emitente: str, estado_destinatario: str, tipo_operacao: str = 'venda') -> str:
    """
    Calcula CFOP baseado na natureza da transação
    
    CFOP (Código Fiscal de Operações e Prestações):
    - Depende do estado de origem (emitente/loja) e destino (cliente)
    - Venda dentro do mesmo estado: CFOP 5102
    - Venda interestadual: CFOP 6108
    - Outras operações podem ter CFOPs diferentes
    
    Args:
        estado_emitente: UF do estado da loja (ex: 'SP')
        estado_destinatario: UF do estado do cliente (ex: 'RJ')
        tipo_operacao: Tipo de operação ('venda', 'compra', etc.)
    
    Returns:
        CFOP (4 dígitos) como string
    """
    estado_emitente = estado_emitente.upper().strip()
    estado_destinatario = estado_destinatario.upper().strip()
    
    # Mesmo estado
    if estado_emitente == estado_destinatario:
        if tipo_operacao == 'venda':
            return '5102'  # Venda de produção do estabelecimento dentro do estado
        elif tipo_operacao == 'compra':
            return '1102'  # Compra para industrialização no mesmo estado
        else:
            return '5102'  # Default para venda
    
    # Interestadual
    else:
        if tipo_operacao == 'venda':
            return '6108'  # Venda de produção do estabelecimento para outro estado
        elif tipo_operacao == 'compra':
            return '2102'  # Compra para industrialização em outro estado
        else:
            return '6108'  # Default para venda


def map_order_to_bling_format(venda: Dict) -> Dict:
    """
    Mapeia venda do formato LhamaBanana para formato Bling
    
    Inclui cálculo automático de CFOP baseado na natureza da transação.
    CFOP é atributo do pedido/NF, não do produto.
    
    Args:
        venda: Dict com dados da venda do banco
    
    Returns:
        Dict formatado para API do Bling
    """
    # Dados do cliente
    nome_cliente = venda.get('nome_recebedor') or venda.get('usuario_nome') or 'Cliente'
    email_cliente = venda.get('email_entrega') or venda.get('usuario_email') or ''
    telefone_cliente = venda.get('telefone_entrega') or ''
    
    # CPF/CNPJ
    cpf_cnpj = venda.get('fiscal_cpf_cnpj', '').replace('.', '').replace('-', '').replace('/', '')
    tipo_pessoa = 'J' if len(cpf_cnpj) == 14 else 'F'
    
    # Estado do cliente (destinatário)
    estado_cliente = venda.get('estado_entrega', '').upper().strip()
    
    # Estado da loja (emitente) - configurável via config ou usar padrão SP
    estado_loja = current_app.config.get('BLING_EMITENTE_ESTADO', 'SP').upper().strip()
    
    # Calcular CFOP baseado na natureza da transação
    cfop = calculate_cfop(estado_loja, estado_cliente, tipo_operacao='venda')
    
    current_app.logger.info(
        f"📋 CFOP calculado para pedido {venda.get('id')}: {cfop} "
        f"(Loja: {estado_loja}, Cliente: {estado_cliente})"
    )
    
    # Montar endereço
    endereco_parts = [
        venda.get('rua_entrega', ''),
        venda.get('numero_entrega', ''),
        venda.get('complemento_entrega', '')
    ]
    endereco = ', '.join([p for p in endereco_parts if p])
    
    # Preparar itens
    itens_bling = []
    for item in venda.get('itens', []):
        bling_produto_id = item.get('bling_produto_id')
        
        if not bling_produto_id:
            current_app.logger.warning(
                f"Item {item.get('nome_produto_snapshot')} não está sincronizado com Bling. "
                f"Pedido pode falhar."
            )
            # Criar item sem referência (Bling tentará encontrar por código)
            item_bling = {
                "codigo": item.get('sku_produto_snapshot') or item.get('bling_produto_codigo'),
                "descricao": item.get('nome_produto_snapshot', 'Produto'),
                "quantidade": int(item.get('quantidade', 1)),
                "valor": float(item.get('preco_unitario', 0)),
                "desconto": 0
            }
        else:
            item_bling = {
                "idProduto": bling_produto_id,
                "codigo": item.get('bling_produto_codigo') or item.get('sku_produto_snapshot'),
                "descricao": item.get('nome_produto_snapshot', 'Produto'),
                "quantidade": int(item.get('quantidade', 1)),
                "valor": float(item.get('preco_unitario', 0)),
                "desconto": 0
            }
        
        # Adicionar CFOP a cada item (CFOP é atributo do item no pedido)
        item_bling["cfop"] = cfop
        
        itens_bling.append(item_bling)
    
    # Mapear status do pedido
    status_local = venda.get('status_pedido', 'pendente_pagamento')
    situacao_bling = map_status_to_bling_situacao(status_local)
    
    # Montar pedido no formato Bling
    pedido_bling = {
        "cliente": {
            "nome": nome_cliente,
            "tipoPessoa": tipo_pessoa,
            "cpf_cnpj": cpf_cnpj,
            "ie": venda.get('fiscal_inscricao_estadual') or "",
            "endereco": endereco,
            "numero": venda.get('numero_entrega', ''),
            "complemento": venda.get('complemento_entrega', ''),
            "bairro": venda.get('bairro_entrega', ''),
            "cidade": venda.get('cidade_entrega', ''),
            "uf": venda.get('estado_entrega', ''),
            "cep": venda.get('cep_entrega', '').replace('-', ''),
            "email": email_cliente,
            "celular": telefone_cliente
        },
        "itens": itens_bling,
        "parcelas": [
            {
                "dias": 0,  # Pagamento à vista
                "data": venda.get('data_venda').strftime('%Y-%m-%d') if venda.get('data_venda') else None,
                "valor": float(venda.get('valor_total', 0)),
                "observacoes": ""
            }
        ],
        "situacao": situacao_bling,
        "observacoes": f"Pedido originado do site LhamaBanana. Código: {venda.get('codigo_pedido')}"
    }
    
    # Adicionar desconto se houver
    desconto = float(venda.get('valor_desconto', 0))
    if desconto > 0:
        pedido_bling["desconto"] = desconto
        pedido_bling["descontoUnidade"] = "REAL"
    
    # Adicionar frete
    frete = float(venda.get('valor_frete', 0))
    if frete > 0:
        pedido_bling["transporte"] = {
            "frete": frete,
            "fretePorConta": "E"  # Emitente (loja)
        }
    
    return pedido_bling


def map_status_to_bling_situacao(status_local: str) -> str:
    """
    Mapeia status do pedido local para situação do Bling
    
    Bling situações:
    - "A" = Aberto
    - "E" = Em aberto
    - "B" = Baixado
    - "F" = Faturado
    - "C" = Cancelado
    - "P" = Pendente
    """
    status_map = {
        'pendente': 'P',
        'pendente_pagamento': 'P',
        'processando_envio': 'E',
        'enviado': 'E',
        'entregue': 'B',
        'cancelado_pelo_cliente': 'C',
        'cancelado_pelo_vendedor': 'C',
        'devolvido': 'C',
        'reembolsado': 'C'
    }
    
    return status_map.get(status_local, 'P')


def map_bling_situacao_to_status(situacao_bling: str) -> str:
    """
    Mapeia situação do Bling para status do pedido local
    """
    situacao_map = {
        'A': 'pendente_pagamento',
        'E': 'processando_envio',
        'B': 'entregue',
        'F': 'enviado',
        'C': 'cancelado_pelo_vendedor',
        'P': 'pendente_pagamento'
    }
    
    return situacao_map.get(situacao_bling, 'pendente_pagamento')


def sync_order_to_bling(venda_id: int) -> Dict:
    """
    Sincroniza pedido/venda para o Bling
    
    Garante que o cliente existe no Bling antes de criar o pedido.
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        # 1. Garantir que cliente existe no Bling
        from .bling_client_service import sync_client_for_order
        client_result = sync_client_for_order(venda_id)
        
        if not client_result.get('success'):
            current_app.logger.warning(
                f"⚠️ Falha ao sincronizar cliente para venda {venda_id}: {client_result.get('error')}. "
                f"Tentando criar pedido mesmo assim..."
            )
            # Não bloquear criação do pedido se falhar cliente, mas logar aviso
        
        # 2. Buscar venda do banco
        venda = get_order_for_bling_sync(venda_id)
        
        if not venda:
            return {
                'success': False,
                'error': f'Venda {venda_id} não encontrada'
            }
        
        # 3. Verificar se já existe no Bling
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT bling_pedido_id FROM bling_pedidos WHERE venda_id = %s
        """, (venda_id,))
        
        existing = cur.fetchone()
        cur.close()
        
        # 4. Mapear para formato Bling
        pedido_bling = map_order_to_bling_format(venda)
        
        if existing:
            # Atualizar pedido existente
            bling_pedido_id = existing['bling_pedido_id']
            response = make_bling_api_request(
                'PUT',
                f'/pedidos/vendas/{bling_pedido_id}',
                json=pedido_bling
            )
            action = 'update'
        else:
            # Criar novo pedido
            response = make_bling_api_request(
                'POST',
                '/pedidos/vendas',
                json=pedido_bling
            )
            action = 'create'
        
        if response.status_code in [200, 201]:
            data = response.json()
            bling_pedido = data.get('data', {})
            bling_pedido_id = bling_pedido.get('id') if isinstance(bling_pedido, dict) else data.get('id')
            
            if not bling_pedido_id:
                return {
                    'success': False,
                    'error': 'ID do pedido Bling não retornado na resposta'
                }
            
            # Salvar referência no banco
            save_bling_order_reference(venda_id, bling_pedido_id, action)
            
            # Registrar log
            from .bling_product_service import log_sync
            log_sync('pedido', venda_id, action, {
                'status': 'success',
                'bling_pedido_id': bling_pedido_id,
                'response': data
            })
            
            current_app.logger.info(
                f"✅ Pedido {venda_id} sincronizado com Bling: {bling_pedido_id} ({action})"
            )
            
            return {
                'success': True,
                'action': action,
                'bling_pedido_id': bling_pedido_id,
                'message': f'Pedido sincronizado com sucesso ({action})'
            }
        else:
            error_msg = response.text
            current_app.logger.error(
                f"❌ Erro ao sincronizar pedido {venda_id}: {response.status_code} - {error_msg}"
            )
            
            # Registrar log de erro
            from .bling_product_service import log_sync
            log_sync('pedido', venda_id, action, {
                'status': 'error',
                'error': f'HTTP {response.status_code}: {error_msg}'
            })
            
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code}',
                'details': error_msg
            }
            
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar pedido {venda_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def save_bling_order_reference(venda_id: int, bling_pedido_id: int, action: str):
    """
    Salva referência do pedido no Bling no banco
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO bling_pedidos (venda_id, bling_pedido_id, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
            ON CONFLICT (venda_id) 
            DO UPDATE SET 
                bling_pedido_id = EXCLUDED.bling_pedido_id,
                updated_at = NOW()
        """, (venda_id, bling_pedido_id))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao salvar referência do pedido Bling: {e}")
    finally:
        cur.close()


def get_bling_order_by_local_id(venda_id: int) -> Optional[Dict]:
    """
    Busca referência do pedido Bling pelo ID local
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                id,
                venda_id,
                bling_pedido_id,
                bling_nfe_id,
                nfe_numero,
                nfe_chave_acesso,
                nfe_status,
                created_at,
                updated_at
            FROM bling_pedidos
            WHERE venda_id = %s
        """, (venda_id,))
        
        return cur.fetchone()
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar pedido Bling: {e}")
        return None
    finally:
        cur.close()


def sync_order_status_from_bling(venda_id: int) -> Dict:
    """
    Sincroniza status do pedido do Bling para o banco local
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        # Buscar referência do pedido
        bling_order = get_bling_order_by_local_id(venda_id)
        
        if not bling_order:
            return {
                'success': False,
                'error': 'Pedido não sincronizado com Bling'
            }
        
        bling_pedido_id = bling_order['bling_pedido_id']
        
        # Buscar pedido no Bling
        response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code} ao buscar pedido no Bling'
            }
        
        data = response.json()
        pedido_bling = data.get('data', {})
        
        # Extrair status
        situacao_bling = pedido_bling.get('situacao', 'P')
        status_local = map_bling_situacao_to_status(situacao_bling)
        
        # Atualizar status no banco local
        conn = get_db()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE vendas
                SET status_pedido = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (status_local, venda_id))
            
            # Atualizar informações da NF-e se houver
            nfe_data = pedido_bling.get('notaFiscal', {})
            if nfe_data:
                nfe_id = nfe_data.get('id')
                nfe_numero = nfe_data.get('numero')
                nfe_chave_acesso = nfe_data.get('chaveAcesso')
                nfe_situacao = nfe_data.get('situacao', '')
                
                cur.execute("""
                    UPDATE bling_pedidos
                    SET bling_nfe_id = %s,
                        nfe_numero = %s,
                        nfe_chave_acesso = %s,
                        nfe_status = %s,
                        updated_at = NOW()
                    WHERE venda_id = %s
                """, (nfe_id, nfe_numero, nfe_chave_acesso, nfe_situacao, venda_id))
            
            conn.commit()
            
            # Registrar log
            from .bling_product_service import log_sync
            log_sync('pedido', venda_id, 'sync', {
                'status': 'success',
                'action': 'status_update',
                'status_anterior': bling_order.get('status'),
                'status_novo': status_local,
                'situacao_bling': situacao_bling
            })
            
            current_app.logger.info(
                f"✅ Status do pedido {venda_id} atualizado: {status_local} (Bling: {situacao_bling})"
            )
            
            return {
                'success': True,
                'status': status_local,
                'situacao_bling': situacao_bling,
                'message': 'Status atualizado com sucesso'
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar status do pedido {venda_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def sync_all_orders_status() -> Dict:
    """
    Sincroniza status de todos os pedidos sincronizados com Bling
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT venda_id FROM bling_pedidos
        """)
        
        venda_ids = [row[0] for row in cur.fetchall()]
        results = []
        
        for venda_id in venda_ids:
            try:
                result = sync_order_status_from_bling(venda_id)
                results.append({
                    'venda_id': venda_id,
                    'success': result.get('success'),
                    'status': result.get('status'),
                    'error': result.get('error')
                })
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                current_app.logger.error(f"Erro ao sincronizar status do pedido {venda_id}: {e}")
                results.append({
                    'venda_id': venda_id,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(venda_ids),
            'success': sum(1 for r in results if r.get('success')),
            'errors': sum(1 for r in results if not r.get('success')),
            'results': results
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar status dos pedidos: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'results': []
        }
    finally:
        cur.close()

