"""
Service para sincronização de pedidos/vendas com Bling
=======================================================

Este módulo implementa a sincronização de vendas do LhamaBanana para o Bling.
"""
from flask import current_app
from typing import Dict, Optional, List
from datetime import datetime
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
                -- Dados da transportadora escolhida no checkout
                v.transportadora_nome,
                v.transportadora_cnpj,
                v.transportadora_ie,
                v.transportadora_uf,
                v.transportadora_municipio,
                v.transportadora_endereco,
                v.transportadora_numero,
                v.transportadora_complemento,
                v.transportadora_bairro,
                v.transportadora_cep,
                v.melhor_envio_service_id,
                v.melhor_envio_service_name,
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
        
        # Buscar itens da venda com preço normal do produto para calcular desconto
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
                bp.bling_codigo as bling_produto_codigo,
                -- Buscar preço normal do produto para calcular desconto promocional
                p.preco_venda as preco_venda_normal
            FROM itens_venda iv
            LEFT JOIN bling_produtos bp ON iv.produto_id = bp.produto_id
            LEFT JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = %s
        """, (venda_id,))
        
        itens = cur.fetchall()
        
        # Buscar dados de pagamento
        cur.execute("""
            SELECT 
                id,
                forma_pagamento_tipo,
                bandeira_cartao,
                parcelas,
                valor_parcela,
                valor_pago,
                status_pagamento
            FROM pagamentos
            WHERE venda_id = %s
            ORDER BY criado_em DESC
            LIMIT 1
        """, (venda_id,))
        
        pagamento = cur.fetchone()
        
        venda_dict = dict(venda)
        venda_dict['itens'] = [dict(item) for item in itens]
        venda_dict['pagamento'] = dict(pagamento) if pagamento else None
        
        return venda_dict
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar venda {venda_id}: {e}")
        return None
    finally:
        cur.close()


def get_payment_method_id_from_bling(forma_pagamento_tipo: str) -> Optional[int]:
    """
    Busca ID da forma de pagamento no Bling baseado no tipo local
    
    Args:
        forma_pagamento_tipo: Tipo de pagamento local (CREDIT_CARD, PIX, BOLETO)
    
    Returns:
        ID da forma de pagamento no Bling ou None se não encontrado
    """
    try:
        # Mapear tipo local para termos de busca no Bling
        search_terms = {
            'PIX': ['pix', 'pix instantâneo', 'pix instantaneo'],
            'CREDIT_CARD': ['cartão', 'cartao', 'credito', 'crédito', 'cartão de crédito'],
            'BOLETO': ['boleto', 'boleto bancário', 'boleto bancario']
        }
        
        search_term = search_terms.get(forma_pagamento_tipo, [forma_pagamento_tipo.lower()])
        
        # Buscar formas de pagamento no Bling
        response = make_bling_api_request(
            'GET',
            '/formas-pagamentos',
            params={'limite': 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            formas_pagamento = data.get('data', [])
            
            # Procurar forma de pagamento que corresponda ao tipo
            for forma in formas_pagamento:
                nome = forma.get('nome', '').lower()
                codigo = forma.get('codigo', '').lower()
                
                for term in search_term:
                    if term in nome or term in codigo:
                        bling_id = forma.get('id')
                        current_app.logger.info(f"✅ Forma de pagamento encontrada: {forma_pagamento_tipo} → Bling ID {bling_id} ({forma.get('nome')})")
                        return bling_id
            
            current_app.logger.warning(f"⚠️ Forma de pagamento não encontrada no Bling: {forma_pagamento_tipo}")
            return None
        else:
            current_app.logger.warning(f"⚠️ Erro ao buscar formas de pagamento no Bling: {response.status_code}")
            return None
            
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar forma de pagamento no Bling: {e}")
        return None


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
    cpf_cnpj_raw = venda.get('fiscal_cpf_cnpj') or ''
    cpf_cnpj = str(cpf_cnpj_raw).replace('.', '').replace('-', '').replace('/', '') if cpf_cnpj_raw else ''
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
        
        # Preço normal do produto (preco_venda) e preço efetivo vendido (preco_unitario)
        preco_venda_normal = float(item.get('preco_venda_normal') or item.get('preco_unitario', 0))
        preco_efetivo_vendido = float(item.get('preco_unitario', 0))
        quantidade = int(item.get('quantidade', 1))
        
        # Calcular desconto promocional por item se houver
        # Se preco_efetivo < preco_normal, significa que houve promoção
        if preco_efetivo_vendido < preco_venda_normal:
            desconto_por_unidade = preco_venda_normal - preco_efetivo_vendido
            desconto_total_item = desconto_por_unidade * quantidade
            current_app.logger.info(
                f"💰 Desconto promocional detectado: Produto {item.get('nome_produto_snapshot')} - "
                f"Preço normal: R$ {preco_venda_normal:.2f}, Preço vendido: R$ {preco_efetivo_vendido:.2f}, "
                f"Desconto: R$ {desconto_total_item:.2f}"
            )
        else:
            desconto_total_item = 0.0
        
        # Usar preço normal como valor base (Bling calculará o total com desconto)
        valor_base_item = preco_venda_normal
        
        if not bling_produto_id:
            current_app.logger.warning(
                f"Item {item.get('nome_produto_snapshot')} não está sincronizado com Bling. "
                f"Pedido pode falhar."
            )
            # Criar item sem referência (Bling tentará encontrar por código)
            item_bling = {
                "codigo": item.get('sku_produto_snapshot') or item.get('bling_produto_codigo'),
                "descricao": item.get('nome_produto_snapshot', 'Produto'),
                "quantidade": quantidade,
                "valor": valor_base_item,  # Preço normal
                "desconto": desconto_total_item,  # Desconto promocional
                "unidade": "UN"  # Unidade de medida
            }
        else:
            item_bling = {
                "produto": {
                    "id": bling_produto_id
                },
                "codigo": item.get('bling_produto_codigo') or item.get('sku_produto_snapshot'),
                "descricao": item.get('nome_produto_snapshot', 'Produto'),
                "quantidade": quantidade,
                "valor": valor_base_item,  # Preço normal
                "desconto": desconto_total_item,  # Desconto promocional
                "unidade": "UN"  # Unidade de medida
            }
        
        itens_bling.append(item_bling)
    
    # Mapear status do pedido
    status_local = venda.get('status_pedido', 'pendente_pagamento')
    situacao_bling = map_status_to_bling_situacao(status_local)
    
    # Buscar ID do cliente no Bling
    # O pedido deve referenciar o cliente pelo ID, não criar inline
    bling_client_id = None
    try:
        from .bling_client_service import sync_client_for_order
        client_result = sync_client_for_order(venda.get('id'))
        if client_result.get('success'):
            bling_client_id = client_result.get('bling_client_id')
            current_app.logger.info(f"✅ Cliente sincronizado no Bling: ID {bling_client_id}")
    except Exception as e:
        current_app.logger.warning(f"⚠️ Erro ao sincronizar cliente: {e}")
    
    if not bling_client_id:
        current_app.logger.error(f"❌ Cliente não encontrado/criado no Bling para venda {venda.get('id')}")
        raise ValueError("Cliente não encontrado no Bling. É necessário sincronizar o cliente antes de criar o pedido.")
    
    # Preparar data da parcela
    data_parcela = datetime.now().strftime('%Y-%m-%d')
    if venda.get('data_venda'):
        if hasattr(venda.get('data_venda'), 'strftime'):
            data_parcela = venda.get('data_venda').strftime('%Y-%m-%d')
        elif isinstance(venda.get('data_venda'), str):
            data_parcela = venda.get('data_venda')[:10]  # Pegar apenas YYYY-MM-DD se for string
    
    current_app.logger.info(f"📅 Data da parcela: {data_parcela}")
    
    # Preparar parcelas com informações de pagamento
    pagamento = venda.get('pagamento')
    parcelas_bling = []
    
    if pagamento:
        forma_pagamento_tipo = pagamento.get('forma_pagamento_tipo')
        num_parcelas = pagamento.get('parcelas', 1)
        valor_total = float(venda.get('valor_total', 0))
        valor_parcela = float(pagamento.get('valor_parcela', 0) or (valor_total / num_parcelas))
        
        # Buscar ID da forma de pagamento no Bling
        forma_pagamento_id = get_payment_method_id_from_bling(forma_pagamento_tipo)
        
        # Criar parcelas baseadas no pagamento
        if num_parcelas > 1:
            # Cartão parcelado: criar múltiplas parcelas
            from datetime import timedelta
            base_date = venda.get('data_venda') if venda.get('data_venda') else datetime.now()
            if isinstance(base_date, str):
                try:
                    base_date = datetime.strptime(base_date[:10], '%Y-%m-%d')
                except:
                    base_date = datetime.now()
            elif hasattr(base_date, 'date'):
                base_date = base_date.date()
                base_date = datetime.combine(base_date, datetime.min.time())
            
            for i in range(num_parcelas):
                vencimento = base_date + timedelta(days=30 * i)
                if isinstance(vencimento, datetime):
                    vencimento_str = vencimento.strftime('%Y-%m-%d')
                elif hasattr(vencimento, 'strftime'):
                    vencimento_str = vencimento.strftime('%Y-%m-%d')
                else:
                    vencimento_str = data_parcela
                
                # Última parcela pode ter valor diferente por arredondamento
                valor_parcela_final = valor_parcela if i < num_parcelas - 1 else (valor_total - (valor_parcela * (num_parcelas - 1)))
                
                parcela = {
                    "dataVencimento": vencimento_str,
                    "valor": valor_parcela_final,
                    "observacoes": f"Parcela {i + 1}/{num_parcelas} - {forma_pagamento_tipo}"
                }
                
                if forma_pagamento_id:
                    parcela["formaPagamento"] = {"id": forma_pagamento_id}
                
                parcelas_bling.append(parcela)
                
            current_app.logger.info(f"💰 Criando {num_parcelas} parcelas de R$ {valor_parcela:.2f} cada")
        else:
            # Pagamento à vista: uma parcela
            parcela = {
                "dataVencimento": data_parcela,
                "valor": valor_total,
                "observacoes": f"Pagamento {forma_pagamento_tipo}"
            }
            
            if forma_pagamento_id:
                parcela["formaPagamento"] = {"id": forma_pagamento_id}
            
            parcelas_bling.append(parcela)
            current_app.logger.info(f"💰 Criando 1 parcela de R$ {valor_total:.2f} ({forma_pagamento_tipo})")
    else:
        # Sem informações de pagamento: criar parcela padrão
        parcela = {
            "dataVencimento": data_parcela,
            "valor": float(venda.get('valor_total', 0)),
            "observacoes": ""
        }
        parcelas_bling.append(parcela)
        current_app.logger.warning(f"⚠️ Sem informações de pagamento - criando parcela padrão")
    
    # Montar pedido no formato Bling (API v3)
    pedido_bling = {
        "data": data_parcela,  # Data do pedido (obrigatório)
        "contato": {
            "id": bling_client_id,
            "tipoPessoa": tipo_pessoa,
            "numeroDocumento": cpf_cnpj
        },
        "itens": itens_bling,
        "parcelas": parcelas_bling,
        "observacoes": f"Pedido originado do site LhamaBanana. Código: {venda.get('codigo_pedido')}"
    }
    
    # Adicionar desconto se houver
    desconto = float(venda.get('valor_desconto', 0))
    if desconto > 0:
        pedido_bling["desconto"] = {
            "valor": desconto,
            "unidade": "REAL"
        }
    
    # Adicionar frete
    frete = float(venda.get('valor_frete', 0))
    if frete > 0:
        pedido_bling["transporte"] = {
            "frete": frete,
            "fretePorConta": 0  # 0 = Emitente (loja)
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
            error_msg = client_result.get('error', 'Erro desconhecido')
            error_details = client_result.get('details', {})
            
            current_app.logger.error(
                f"❌ Falha ao sincronizar cliente para venda {venda_id}: {error_msg}"
            )
            if error_details:
                current_app.logger.error(f"Detalhes do erro do cliente: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
            
            # Bloquear criação do pedido se o cliente não foi criado
            # O Bling requer que o cliente exista antes de criar o pedido
            return {
                'success': False,
                'error': f'Cliente não pôde ser sincronizado no Bling',
                'client_error': error_msg,
                'client_error_details': error_details,
                'message': 'Não é possível criar pedido no Bling sem cliente válido. Verifique os dados fiscais do cliente.'
            }
        
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
            error_data = {}
            
            # Tentar extrair detalhes do erro JSON
            try:
                error_json = response.json()
                error_data = error_json
                
                # Extrair mensagens de erro mais específicas
                if 'error' in error_json:
                    error_msg = error_json['error']
                elif 'message' in error_json:
                    error_msg = error_json['message']
                elif 'errors' in error_json:
                    # Bling pode retornar lista de erros
                    errors = error_json['errors']
                    if isinstance(errors, list) and len(errors) > 0:
                        error_msg = '; '.join([str(e) for e in errors])
                        error_data['validation_errors'] = errors
            except:
                pass  # Manter error_msg original se não for JSON
            
            current_app.logger.error(
                f"❌ Erro ao sincronizar pedido {venda_id}: {response.status_code} - {error_msg}"
            )
            current_app.logger.error(f"Detalhes completos do erro: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            current_app.logger.error(f"Response text completo: {response.text[:1000]}")
            
            # Registrar log de erro
            from .bling_product_service import log_sync
            log_sync('pedido', venda_id, action, {
                'status': 'error',
                'error': f'HTTP {response.status_code}: {error_msg}',
                'error_details': error_data,
                'response_text': response.text[:500]
            })
            
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code}',
                'message': error_msg,
                'details': error_data if error_data else error_msg
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


def update_order_situacao_to_verificado(venda_id: int) -> Dict:
    """
    Atualiza situação do pedido no Bling para "Verificado"
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da atualização
    """
    try:
        # Buscar referência do pedido no Bling
        bling_order = get_bling_order_by_local_id(venda_id)
        
        if not bling_order:
            return {
                'success': False,
                'error': 'Pedido não sincronizado com Bling'
            }
        
        bling_pedido_id = bling_order['bling_pedido_id']
        
        # Buscar ID da situação "Verificado" no banco
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            cur.execute("""
                SELECT bling_situacao_id, nome
                FROM bling_situacoes
                WHERE bling_situacao_id = 24 OR LOWER(nome) LIKE '%verificado%'
                LIMIT 1
            """)
            
            situacao_verificado = cur.fetchone()
            
            if not situacao_verificado:
                return {
                    'success': False,
                    'error': "Situação 'Verificado' não encontrada no banco"
                }
            
            situacao_id = situacao_verificado['bling_situacao_id']
            situacao_nome = situacao_verificado['nome']
            
        finally:
            cur.close()
        
        # Buscar pedido atual no Bling
        response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro ao buscar pedido no Bling: HTTP {response.status_code}'
            }
        
        data = response.json()
        pedido_bling = data.get('data', {})
        
        # Preparar dados para atualização
        situacao_atual = pedido_bling.get('situacao', {})
        
        update_data = {}
        
        if isinstance(situacao_atual, dict):
            update_data['situacao'] = {
                'id': situacao_id
            }
        else:
            update_data['situacao'] = situacao_id
        
        # Atualizar pedido no Bling
        response = make_bling_api_request(
            'PUT',
            f'/pedidos/vendas/{bling_pedido_id}',
            json=update_data
        )
        
        if response.status_code in [200, 201]:
            current_app.logger.info(
                f"✅ Situação do pedido {bling_pedido_id} atualizada para 'Verificado' no Bling"
            )
            
            # Atualizar situação no banco local também
            from .bling_situacao_service import update_pedido_situacao
            update_pedido_situacao(
                venda_id=venda_id,
                bling_situacao_id=situacao_id,
                bling_situacao_nome=situacao_nome
            )
            
            return {
                'success': True,
                'message': 'Situação atualizada para Verificado no Bling',
                'bling_pedido_id': bling_pedido_id,
                'situacao_id': situacao_id,
                'situacao_nome': situacao_nome
            }
        else:
            error_text = response.text
            current_app.logger.error(
                f"❌ Erro ao atualizar situação do pedido {bling_pedido_id} para Verificado: "
                f"HTTP {response.status_code} - {error_text}"
            )
            
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code}',
                'details': error_text
            }
            
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao atualizar situação para Verificado: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def update_order_situacao_to_logistica(venda_id: int) -> Dict:
    """
    Atualiza situação do pedido no Bling para "Logística"
    
    Quando a NFC-e é aprovada, o pedido deve mudar para "Logística" no Bling,
    o que dispara automaticamente: decremento de estoque, emissão de etiqueta, etc.
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da atualização
    """
    try:
        # Buscar referência do pedido no Bling
        bling_order = get_bling_order_by_local_id(venda_id)
        
        if not bling_order:
            return {
                'success': False,
                'error': 'Pedido não sincronizado com Bling'
            }
        
        bling_pedido_id = bling_order['bling_pedido_id']
        
        # Buscar ID da situação "Logística" no banco
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            cur.execute("""
                SELECT bling_situacao_id, nome
                FROM bling_situacoes
                WHERE LOWER(nome) LIKE '%logística%' OR LOWER(nome) LIKE '%logistica%'
                LIMIT 1
            """)
            
            situacao_logistica = cur.fetchone()
            
            if not situacao_logistica:
                current_app.logger.warning(
                    "Situação 'Logística' não encontrada no banco. "
                    "Tentando atualizar pedido sem ID de situação específico."
                )
                # Tentar atualizar usando o nome diretamente
                situacao_id = None
                situacao_nome = "Logística"
            else:
                situacao_id = situacao_logistica['bling_situacao_id']
                situacao_nome = situacao_logistica['nome']
            
        finally:
            cur.close()
        
        # Buscar pedido atual no Bling para ver situação atual
        response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro ao buscar pedido no Bling: HTTP {response.status_code}'
            }
        
        data = response.json()
        pedido_bling = data.get('data', {})
        
        # Preparar dados para atualização
        # O Bling aceita atualização de situação via PUT no pedido
        update_data = {}
        
        # Se temos o ID da situação, usar ele
        if situacao_id:
            # Tentar atualizar usando o campo situacao com ID
            # O formato pode variar, vamos tentar ambos
            situacao_atual = pedido_bling.get('situacao', {})
            
            if isinstance(situacao_atual, dict):
                update_data['situacao'] = {
                    'id': situacao_id
                }
            else:
                # Se situação é string ou número, tentar atualizar diretamente
                update_data['situacao'] = situacao_id
        
        # Se não temos ID, tentar atualizar pelo nome (pode não funcionar)
        if not update_data.get('situacao'):
            current_app.logger.warning(
                f"Não foi possível determinar ID da situação 'Logística'. "
                f"Tentando atualizar pedido {bling_pedido_id} sem mudar situação."
            )
            # Retornar sucesso parcial - o pedido já está no Bling
            return {
                'success': True,
                'message': 'Pedido encontrado no Bling, mas situação não atualizada (ID não encontrado)',
                'bling_pedido_id': bling_pedido_id,
                'situacao_atual': pedido_bling.get('situacao')
            }
        
        # Atualizar pedido no Bling
        response = make_bling_api_request(
            'PUT',
            f'/pedidos/vendas/{bling_pedido_id}',
            json=update_data
        )
        
        if response.status_code in [200, 201]:
            current_app.logger.info(
                f"✅ Situação do pedido {bling_pedido_id} atualizada para 'Logística' no Bling"
            )
            
            # Atualizar situação no banco local também
            from .bling_situacao_service import update_pedido_situacao
            update_pedido_situacao(
                venda_id=venda_id,
                bling_situacao_id=situacao_id,
                bling_situacao_nome=situacao_nome
            )
            
            return {
                'success': True,
                'message': 'Situação atualizada para Logística no Bling',
                'bling_pedido_id': bling_pedido_id,
                'situacao_id': situacao_id,
                'situacao_nome': situacao_nome
            }
        else:
            error_text = response.text
            current_app.logger.error(
                f"❌ Erro ao atualizar situação do pedido {bling_pedido_id}: "
                f"HTTP {response.status_code} - {error_text}"
            )
            
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code}',
                'details': error_text
            }
            
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao atualizar situação para Logística: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_order_by_nfe_id(nfe_id: int) -> Optional[Dict]:
    """
    Busca pedido local pelo ID da NFC-e no Bling
    
    Args:
        nfe_id: ID da NFC-e no Bling
    
    Returns:
        Dict com dados do pedido ou None se não encontrado
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                bp.id,
                bp.venda_id,
                bp.bling_pedido_id,
                bp.bling_nfe_id,
                bp.nfe_numero,
                bp.nfe_chave_acesso,
                bp.nfe_status,
                v.codigo_pedido,
                v.status_pedido
            FROM bling_pedidos bp
            JOIN vendas v ON bp.venda_id = v.id
            WHERE bp.bling_nfe_id = %s
        """, (nfe_id,))
        
        return cur.fetchone()
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar pedido por NFC-e ID {nfe_id}: {e}")
        return None
    finally:
        cur.close()


def approve_order_in_bling(venda_id: int) -> Dict:
    """
    Aprova pedido no Bling mudando situação para 'E' (Em aberto)
    
    Esta função permite que a loja aprove manualmente um pedido que foi pago
    e precisa de aprovação antes de processar/envio.
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da aprovação
    """
    try:
        # Buscar referência do pedido no Bling
        bling_order = get_bling_order_by_local_id(venda_id)
        
        if not bling_order:
            return {
                'success': False,
                'error': 'Pedido não sincronizado com Bling. Sincronize o pedido primeiro.'
            }
        
        bling_pedido_id = bling_order['bling_pedido_id']
        
        # Buscar pedido atual no Bling
        response = make_bling_api_request('GET', f'/pedidos/vendas/{bling_pedido_id}')
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro ao buscar pedido no Bling: HTTP {response.status_code}'
            }
        
        data = response.json()
        pedido_bling = data.get('data', {})
        
        # Verificar situação atual
        situacao_atual = pedido_bling.get('situacao', 'P')
        
        if situacao_atual == 'E':
            # Já está aprovado
            return {
                'success': True,
                'message': 'Pedido já está aprovado no Bling',
                'situacao': 'E',
                'bling_pedido_id': bling_pedido_id
            }
        
        if situacao_atual == 'B' or situacao_atual == 'F':
            return {
                'success': False,
                'error': f'Não é possível aprovar pedido na situação atual: {situacao_atual}'
            }
        
        # Atualizar pedido para situação 'E' (Em aberto = Aprovado)
        # Precisamos enviar o pedido completo, apenas mudando a situação
        pedido_atualizado = {
            **pedido_bling,
            'situacao': 'E'  # Em aberto = Aprovado
        }
        
        # Remover campos que não devem ser enviados no PUT
        campos_para_remover = ['id', 'numero', 'numeroLoja', 'data', 'dataSaida', 'dataPrevista']
        for campo in campos_para_remover:
            pedido_atualizado.pop(campo, None)
        
        response = make_bling_api_request(
            'PUT',
            f'/pedidos/vendas/{bling_pedido_id}',
            json=pedido_atualizado
        )
        
        if response.status_code in [200, 201]:
            # Atualizar status local para refletir aprovação
            conn = get_db()
            cur = conn.cursor()
            
            try:
                cur.execute("""
                    UPDATE vendas 
                    SET status_pedido = 'processando_envio',
                        updated_at = NOW()
                    WHERE id = %s
                """, (venda_id,))
                conn.commit()
                
                current_app.logger.info(
                    f"✅ Pedido {venda_id} aprovado no Bling (ID: {bling_pedido_id})"
                )
                
                return {
                    'success': True,
                    'message': 'Pedido aprovado com sucesso no Bling',
                    'bling_pedido_id': bling_pedido_id,
                    'situacao_anterior': situacao_atual,
                    'situacao_nova': 'E',
                    'status_local_atualizado': 'processando_envio'
                }
            finally:
                cur.close()
        else:
            error_text = response.text
            current_app.logger.error(
                f"❌ Erro ao aprovar pedido {venda_id} no Bling: {response.status_code} - {error_text}"
            )
            
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code}',
                'details': error_text
            }
            
    except Exception as e:
        current_app.logger.error(f"Erro ao aprovar pedido {venda_id}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def sync_all_orders_to_bling(only_pending: bool = False) -> Dict:
    """
    Sincroniza todos os pedidos para o Bling
    
    Args:
        only_pending: Se True, sincroniza apenas pedidos que ainda não foram sincronizados
    
    Returns:
        Dict com resultado da sincronização
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        if only_pending:
            # Buscar apenas pedidos que não foram sincronizados
            cur.execute("""
                SELECT v.id
                FROM vendas v
                LEFT JOIN bling_pedidos bp ON v.id = bp.venda_id
                WHERE bp.venda_id IS NULL
                ORDER BY v.id DESC
            """)
        else:
            # Buscar todos os pedidos
            cur.execute("""
                SELECT v.id
                FROM vendas v
                ORDER BY v.id DESC
            """)
        
        venda_ids = [row['id'] for row in cur.fetchall()]
        results = []
        
        current_app.logger.info(f"Iniciando sincronização de {len(venda_ids)} pedidos para o Bling...")
        
        for venda_id in venda_ids:
            try:
                result = sync_order_to_bling(venda_id)
                results.append({
                    'venda_id': venda_id,
                    'success': result.get('success'),
                    'bling_pedido_id': result.get('bling_pedido_id'),
                    'action': result.get('action'),
                    'error': result.get('error'),
                    'message': result.get('message')
                })
                
                # Rate limiting - aguardar 0.5s entre requisições
                time.sleep(0.5)
                
            except Exception as e:
                current_app.logger.error(f"Erro ao sincronizar pedido {venda_id}: {e}")
                results.append({
                    'venda_id': venda_id,
                    'success': False,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r.get('success'))
        error_count = len(results) - success_count
        
        current_app.logger.info(
            f"✅ Sincronização concluída: {success_count} sucessos, {error_count} erros de {len(venda_ids)} pedidos"
        )
        
        return {
            'total': len(venda_ids),
            'success': success_count,
            'errors': error_count,
            'results': results
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar pedidos: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'results': []
        }
    finally:
        cur.close()

