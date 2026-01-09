"""
Service para integração Financeira com Bling
=============================================

Sincroniza informações financeiras entre:
- Pagamentos confirmados (PagBank)
- Contas a Receber no Bling

Funcionalidades:
- Criar contas a receber no Bling quando pagamento é confirmado
- Vincular conta a receber ao pedido
- Atualizar status de recebimento
- Sincronizar parcelas (cartão parcelado)
"""
from flask import current_app
from typing import Dict, Optional
from .db import get_db
from .bling_order_service import get_bling_order_by_local_id
from .bling_api_service import make_bling_api_request
import psycopg2.extras
from datetime import datetime, timedelta
import json


def create_account_receivable_for_order(venda_id: int, pagamento_id: int = None) -> Dict:
    """
    Cria conta a receber no Bling para um pedido/venda
    
    A conta a receber será vinculada ao pedido e criada com base no pagamento confirmado.
    
    Args:
        venda_id: ID da venda local
        pagamento_id: ID do pagamento (opcional, busca automaticamente se não fornecido)
    
    Returns:
        Dict com resultado da criação
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # 1. Buscar dados da venda
        cur.execute("""
            SELECT 
                v.id, v.codigo_pedido, v.valor_total, v.data_venda,
                v.fiscal_cpf_cnpj, v.fiscal_nome_razao_social
            FROM vendas v
            WHERE v.id = %s
        """, (venda_id,))
        
        venda = cur.fetchone()
        if not venda:
            return {
                'success': False,
                'error': f'Venda {venda_id} não encontrada'
            }
        
        # 2. Buscar dados do pagamento (se não fornecido, busca o pagamento confirmado)
        if pagamento_id:
            cur.execute("""
                SELECT id, valor_pago, forma_pagamento_tipo, parcelas, 
                       valor_parcela, status_pagamento, pago_em
                FROM pagamentos
                WHERE id = %s AND venda_id = %s
            """, (pagamento_id, venda_id))
        else:
            cur.execute("""
                SELECT id, valor_pago, forma_pagamento_tipo, parcelas,
                       valor_parcela, status_pagamento, pago_em
                FROM pagamentos
                WHERE venda_id = %s 
                  AND status_pagamento IN ('PAID', 'AUTHORIZED')
                ORDER BY pago_em DESC NULLS LAST, id DESC
                LIMIT 1
            """, (venda_id,))
        
        pagamento = cur.fetchone()
        if not pagamento:
            return {
                'success': False,
                'error': 'Pagamento confirmado não encontrado para esta venda'
            }
        
        # 3. Verificar se pedido existe no Bling
        bling_pedido = get_bling_order_by_local_id(venda_id)
        if not bling_pedido:
            return {
                'success': False,
                'error': 'Pedido não encontrado no Bling. Sincronize o pedido primeiro.',
                'hint': 'Use /api/bling/pedidos/sync/{venda_id} para sincronizar o pedido'
            }
        
        bling_pedido_id = bling_pedido['bling_pedido_id']
        
        # 4. Verificar se conta a receber já existe
        # (evitar duplicação)
        existing_ar = get_account_receivable_by_order(venda_id)
        if existing_ar:
            current_app.logger.info(
                f"ℹ️ Conta a receber já existe para venda {venda_id} (Bling ID: {existing_ar.get('bling_id')})"
            )
            return {
                'success': True,
                'action': 'exists',
                'bling_conta_receber_id': existing_ar.get('bling_id'),
                'message': 'Conta a receber já existe'
            }
        
        # 5. Preparar dados da conta a receber
        valor_total = float(venda['valor_total'])
        data_vencimento = pagamento['pago_em'] if pagamento['pago_em'] else datetime.now()
        
        # Para PIX: vencimento é hoje (já pago)
        # Para cartão parcelado: criar múltiplas contas a receber
        # Para boleto: usar data de vencimento do boleto (já passou se foi pago)
        
        forma_pagamento = pagamento['forma_pagamento_tipo']
        parcelas = pagamento['parcelas'] or 1
        
        if forma_pagamento == 'PIX':
            # PIX: conta a receber com vencimento hoje (já paga)
            contas_a_criar = [{
                'data_vencimento': data_vencimento.strftime('%Y-%m-%d'),
                'valor': valor_total,
                'numero_documento': f"PED-{venda['codigo_pedido']}",
                'observacoes': f"Pagamento PIX - Pedido {venda['codigo_pedido']}"
            }]
        elif forma_pagamento == 'CREDIT_CARD' and parcelas > 1:
            # Cartão parcelado: criar múltiplas contas a receber
            valor_parcela = float(pagamento['valor_parcela'] or (valor_total / parcelas))
            contas_a_criar = []
            
            for parcela_num in range(1, parcelas + 1):
                vencimento = data_vencimento + timedelta(days=30 * (parcela_num - 1))
                contas_a_criar.append({
                    'data_vencimento': vencimento.strftime('%Y-%m-%d'),
                    'valor': valor_parcela if parcela_num < parcelas else (valor_total - (valor_parcela * (parcelas - 1))),
                    'numero_documento': f"PED-{venda['codigo_pedido']}-{parcela_num}/{parcelas}",
                    'observacoes': f"Cartão parcelado {parcela_num}x - Pedido {venda['codigo_pedido']}"
                })
        else:
            # Boleto ou cartão à vista: uma conta a receber
            contas_a_criar = [{
                'data_vencimento': data_vencimento.strftime('%Y-%m-%d'),
                'valor': valor_total,
                'numero_documento': f"PED-{venda['codigo_pedido']}",
                'observacoes': f"Pagamento {forma_pagamento} - Pedido {venda['codigo_pedido']}"
            }]
        
        # 6. Criar contas a receber no Bling
        contas_criadas = []
        erros = []
        
        for conta_data in contas_a_criar:
            try:
                # Preparar payload para Bling
                # O Bling espera contas a receber vinculadas a contatos (clientes)
                # Primeiro, buscar ID do cliente no Bling
                cliente_id = get_bling_client_id_for_order(venda_id)
                
                if not cliente_id:
                    # Tentar criar cliente se não existir
                    try:
                        from .bling_client_service import sync_client_for_order
                        cliente_result = sync_client_for_order(venda_id)
                        if cliente_result.get('success'):
                            cliente_id = cliente_result.get('bling_client_id')
                    except Exception as client_error:
                        current_app.logger.warning(f"⚠️ Erro ao sincronizar cliente: {client_error}")
                
                if not cliente_id:
                    erros.append(f"Cliente não encontrado/criado no Bling para venda {venda_id}")
                    continue
                
                # Preparar payload
                payload = {
                    "dataEmissao": conta_data['data_vencimento'],
                    "vencimento": conta_data['data_vencimento'],
                    "valor": conta_data['valor'],
                    "numero": conta_data['numero_documento'],
                    "dataPagamento": data_vencimento.strftime('%Y-%m-%d') if forma_pagamento == 'PIX' else None,
                    "competencia": data_vencimento.strftime('%Y-%m-%d'),
                    "historico": conta_data['observacoes'],
                    "categoria": {
                        "id": get_bling_category_id()  # Categoria de vendas
                    },
                    "cliente": {
                        "id": cliente_id
                    },
                    "vendedor": {
                        "id": get_bling_seller_id()  # Vendedor padrão (opcional)
                    },
                    "origem": {
                        "id": bling_pedido_id,
                        "tipo": "Venda"
                    }
                }
                
                # Remover campos None
                payload = {k: v for k, v in payload.items() if v is not None}
                
                current_app.logger.info(
                    f"💰 Criando conta a receber no Bling para venda {venda_id}: "
                    f"R$ {conta_data['valor']:.2f} - Venc: {conta_data['data_vencimento']}"
                )
                
                response = make_bling_api_request(
                    'POST',
                    '/contas/receber',
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    conta_id = data.get('data', {}).get('id') if isinstance(data.get('data'), dict) else data.get('id')
                    
                    contas_criadas.append({
                        'bling_id': conta_id,
                        'numero_documento': conta_data['numero_documento'],
                        'valor': conta_data['valor']
                    })
                    
                    # Salvar referência local
                    save_account_receivable_reference(venda_id, conta_id, conta_data['numero_documento'])
                    
                    current_app.logger.info(
                        f"✅ Conta a receber criada no Bling: ID {conta_id} "
                        f"(Documento: {conta_data['numero_documento']})"
                    )
                else:
                    error_text = response.text
                    erros.append(f"Erro HTTP {response.status_code}: {error_text}")
                    current_app.logger.error(
                        f"❌ Erro ao criar conta a receber no Bling: {response.status_code} - {error_text}"
                    )
                    
            except Exception as e:
                erros.append(str(e))
                current_app.logger.error(
                    f"❌ Erro ao criar conta a receber: {e}", exc_info=True
                )
        
        if contas_criadas:
            return {
                'success': True,
                'action': 'created',
                'contas_criadas': contas_criadas,
                'erros': erros if erros else None,
                'message': f'{len(contas_criadas)} conta(s) a receber criada(s) no Bling'
            }
        else:
            return {
                'success': False,
                'error': 'Falha ao criar contas a receber',
                'erros': erros
            }
            
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao criar conta a receber para venda {venda_id}: {e}", exc_info=True
        )
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        cur.close()


def get_account_receivable_by_order(venda_id: int) -> Optional[Dict]:
    """
    Busca conta a receber vinculada a um pedido
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Verificar se há referência salva
        cur.execute("""
            SELECT bling_conta_receber_id, numero_documento
            FROM bling_contas_receber
            WHERE venda_id = %s
            LIMIT 1
        """, (venda_id,))
        
        result = cur.fetchone()
        if result:
            return {
                'bling_id': result['bling_conta_receber_id'],
                'numero_documento': result['numero_documento']
            }
        
        return None
        
    except Exception as e:
        current_app.logger.warning(f"⚠️ Erro ao buscar conta a receber: {e}")
        return None
    finally:
        cur.close()


def save_account_receivable_reference(venda_id: int, bling_conta_id: int, numero_documento: str):
    """
    Salva referência de conta a receber criada no Bling
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Criar tabela se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bling_contas_receber (
                id SERIAL PRIMARY KEY,
                venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE UNIQUE NOT NULL,
                bling_conta_receber_id BIGINT NOT NULL,
                numero_documento VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Inserir ou atualizar referência
        cur.execute("""
            INSERT INTO bling_contas_receber (venda_id, bling_conta_receber_id, numero_documento)
            VALUES (%s, %s, %s)
            ON CONFLICT (venda_id) 
            DO UPDATE SET 
                bling_conta_receber_id = EXCLUDED.bling_conta_receber_id,
                numero_documento = EXCLUDED.numero_documento,
                updated_at = NOW()
        """, (venda_id, bling_conta_id, numero_documento))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"❌ Erro ao salvar referência de conta a receber: {e}", exc_info=True)
    finally:
        cur.close()


def get_bling_client_id_for_order(venda_id: int) -> Optional[int]:
    """
    Busca ID do cliente no Bling para um pedido
    """
    try:
        # Buscar cliente usando a função de sincronização de cliente
        from .bling_client_service import sync_client_for_order
        
        cliente_result = sync_client_for_order(venda_id)
        if cliente_result.get('success'):
            return cliente_result.get('bling_client_id')
        
        return None
            
    except Exception as e:
        current_app.logger.warning(f"⚠️ Erro ao buscar cliente no Bling: {e}")
        return None


def get_bling_category_id() -> Optional[int]:
    """
    Retorna ID da categoria de vendas no Bling
    Pode ser configurado via variável de ambiente ou buscar padrão
    """
    category_id = current_app.config.get('BLING_CATEGORIA_VENDAS_ID')
    if category_id:
        return int(category_id)
    
    # Tentar buscar categoria padrão "Vendas" via API
    try:
        response = make_bling_api_request('GET', '/categorias/receitas')
        if response.status_code == 200:
            data = response.json()
            categorias = data.get('data', [])
            
            # Procurar categoria "Vendas" ou similar
            for cat in categorias:
                if 'venda' in cat.get('nome', '').lower():
                    return cat.get('id')
            
            # Se não encontrar, retornar primeira categoria
            if categorias:
                return categorias[0].get('id')
    except:
        pass
    
    return None


def get_bling_seller_id() -> Optional[int]:
    """
    Retorna ID do vendedor padrão no Bling
    Pode ser configurado via variável de ambiente
    """
    seller_id = current_app.config.get('BLING_VENDEDOR_ID')
    if seller_id:
        return int(seller_id)
    return None


def sync_payment_to_financial(venda_id: int) -> Dict:
    """
    Sincroniza pagamento confirmado para o financeiro do Bling
    
    Esta função é chamada quando um pagamento é confirmado (webhook PagBank)
    e cria a conta a receber no Bling.
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        current_app.logger.info(
            f"💰 Sincronizando pagamento confirmado para Bling (venda {venda_id})..."
        )
        
        result = create_account_receivable_for_order(venda_id)
        
        if result.get('success'):
            if result.get('action') == 'created':
                current_app.logger.info(
                    f"✅ Conta(s) a receber criada(s) no Bling para venda {venda_id}"
                )
            else:
                current_app.logger.info(
                    f"ℹ️ Conta a receber já existe no Bling para venda {venda_id}"
                )
        else:
            current_app.logger.warning(
                f"⚠️ Falha ao criar conta a receber no Bling para venda {venda_id}: {result.get('error')}"
            )
        
        return result
        
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao sincronizar pagamento para Bling: {e}", exc_info=True
        )
        return {
            'success': False,
            'error': str(e)
        }

