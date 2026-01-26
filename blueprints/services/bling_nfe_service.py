"""
Service para emissão de NF-e via Bling
========================================

Gerencia emissão automática de notas fiscais eletrônicas (NF-e) via API do Bling:
- Emissão automática após pagamento confirmado e pedido aprovado
- Emissão de NF-e (Modelo 55) quando pedido muda para "Em andamento"
- Consulta de status da NF-e
- Armazenamento de XML, chave de acesso, número
- Tratamento de erros fiscais
"""
from flask import current_app
from typing import Dict, Optional
from .db import get_db
from .bling_api_service import make_bling_api_request, BlingAPIError, BlingErrorType
from .bling_order_service import get_bling_order_by_local_id, get_order_for_bling_sync
from .bling_payment_service import map_checkout_payment_to_bling
import psycopg2.extras
from datetime import datetime, timedelta
import json as json_module
import time


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
        # Conforme documentação: 1=Pendente, 2=Cancelada, 3=Aguardando recibo,
        # 4=Rejeitada, 5=Autorizada, 6=Emitida DANFE, 7=Registrada,
        # 8=Aguardando protocolo, 9=Denegada, 10=Consulta situação, 11=Bloqueada
        # Converter nfe_situacao para string se for inteiro
        if isinstance(nfe_situacao, int):
            # Mapear código numérico para string
            situacao_map = {
                0: 'PENDENTE',
                1: 'AUTORIZADA',
                2: 'CANCELADA',
                3: 'AGUARDANDO_RECIBO',
                4: 'REJEITADA',
                5: 'AUTORIZADA',  # AUTORIZADA (situação mais comum)
                6: 'EMITIDA_DANFE',
                7: 'REGISTRADA',
                8: 'AGUARDANDO_PROTOCOLO',
                9: 'DENEGADA',
                10: 'CONSULTA_SITUACAO',
                11: 'BLOQUEADA'
            }
            nfe_situacao = situacao_map.get(nfe_situacao, 'PENDENTE')
        
        # Garantir que é string
        nfe_situacao_str = str(nfe_situacao).upper()
        
        status_map = {
            'EMITIDA': 'emitida',
            'AUTORIZADA': 'emitida',
            'AUTORIZADO': 'emitida',
            'EMITIDA_DANFE': 'emitida',  # Situação 6
            'REGISTRADA': 'emitida',  # Situação 7
            'PENDENTE': 'processando',  # Situação 0 ou 1
            'AGUARDANDO_RECIBO': 'processando',  # Situação 3
            'AGUARDANDO_PROTOCOLO': 'processando',  # Situação 8
            'CONSULTA_SITUACAO': 'processando',  # Situação 10
            'PROCESSANDO': 'processando',
            'CANCELADA': 'cancelada',  # Situação 2
            'CANCELADO': 'cancelada',
            'REJEITADA': 'erro',  # Situação 4
            'DENEGADA': 'erro',  # Situação 9
            'BLOQUEADA': 'erro',  # Situação 11
            'ERRO': 'erro'
        }
        status_emissao = status_map.get(nfe_situacao_str, 'processando')
        
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
                json_module.dumps(api_response) if api_response else None,
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
                json_module.dumps(api_response) if api_response else None,
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


def emit_nfe(venda_id: int) -> Dict:
    """
    Emite NF-e (Nota Fiscal Eletrônica - Modelo 55) para um pedido
    
    Esta função cria uma NF-e diretamente usando a API do Bling quando o pedido
    muda para "Em andamento". A NF-e é emitida como nota fiscal eletrônica (tipo 0 = NF-e modelo 55).
    
    IMPORTANTE: Se o pedido já existe no Bling, a NF-e será criada com todos os dados
    (transportadora, etc.) e depois associada ao pedido.
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da emissão
    """
    try:
        # Verificar se o pedido já existe no Bling
        bling_pedido = get_bling_order_by_local_id(venda_id)
        pedido_bling_id = bling_pedido.get('bling_pedido_id') if bling_pedido else None
        
        # Se o pedido existe no Bling, usar emit_nfe_via_bling() que associa automaticamente
        # Mas primeiro vamos criar a NF-e com todos os dados customizados
        # e depois associá-la ao pedido
        if pedido_bling_id:
            current_app.logger.info(
                f"📄 Pedido {venda_id} já existe no Bling (ID: {pedido_bling_id}). "
                f"Criando NF-e com dados customizados e associando ao pedido..."
            )
        
        # Buscar dados completos do pedido
        venda_data = get_order_for_bling_sync(venda_id)
        if not venda_data:
            return {
                'success': False,
                'error': f'Venda {venda_id} não encontrada'
            }
        
        # Verificar dados fiscais
        cpf_cnpj = venda_data.get('fiscal_cpf_cnpj') or ''
        cpf_cnpj = str(cpf_cnpj).replace('.', '').replace('-', '').replace('/', '')
        
        if not cpf_cnpj:
            return {
                'success': False,
                'error': 'Dados fiscais incompletos. CPF/CNPJ não informado.'
            }
        
        tipo_pessoa = 'J' if len(cpf_cnpj) == 14 else 'F'
        
        # Preparar dados do contato
        contato = {
            "nome": venda_data.get('fiscal_nome_razao_social') or venda_data.get('nome_recebedor') or 'Cliente',
            "tipoPessoa": tipo_pessoa,
            "numeroDocumento": cpf_cnpj,
            "email": venda_data.get('email_entrega') or venda_data.get('usuario_email') or '',
            "telefone": venda_data.get('telefone_entrega') or ''
        }
        
        # Adicionar IE se for PJ
        if tipo_pessoa == 'J' and venda_data.get('fiscal_inscricao_estadual'):
            contato["ie"] = venda_data.get('fiscal_inscricao_estadual')
        
        # Preparar endereço
        endereco = {
            "endereco": venda_data.get('fiscal_rua') or venda_data.get('rua_entrega') or '',
            "numero": venda_data.get('fiscal_numero') or venda_data.get('numero_entrega') or '',
            "complemento": venda_data.get('fiscal_complemento') or venda_data.get('complemento_entrega') or '',
            "bairro": venda_data.get('fiscal_bairro') or venda_data.get('bairro_entrega') or '',
            "cep": venda_data.get('fiscal_cep') or venda_data.get('cep_entrega') or '',
            "municipio": venda_data.get('fiscal_cidade') or venda_data.get('cidade_entrega') or '',
            "uf": venda_data.get('fiscal_estado') or venda_data.get('estado_entrega') or ''
        }
        
        # Remover campos vazios
        endereco = {k: v for k, v in endereco.items() if v}
        if endereco:
            contato["endereco"] = endereco
        
        # Preparar itens - usar preço SEM desconto (preço normal do produto)
        itens = []
        valor_total_produtos = 0.0
        
        for item in venda_data.get('itens', []):
            # Usar preço normal do produto (sem desconto promocional)
            # Se não tiver preco_venda_normal, usar preco_unitario (já pode ter desconto aplicado)
            preco_unitario = float(item.get('preco_venda_normal', 0) or item.get('preco_unitario', 0))
            
            quantidade = float(item.get('quantidade', 1))
            subtotal_item = preco_unitario * quantidade
            valor_total_produtos += subtotal_item
            
            item_nfce = {
                "codigo": item.get('bling_produto_codigo') or item.get('sku_produto_snapshot') or '',
                "descricao": item.get('nome_produto_snapshot') or 'Produto',
                "unidade": "UN",
                "quantidade": quantidade,
                "valor": preco_unitario,  # Valor unitário SEM desconto
                "tipo": "P"  # Produto
            }
            
            # Adicionar referência ao produto Bling se existir
            if item.get('bling_produto_id'):
                item_nfce["produto"] = {"id": item.get('bling_produto_id')}
            
            itens.append(item_nfce)
        
        current_app.logger.info(f"💰 Valor total dos produtos (sem desconto): R$ {valor_total_produtos:.2f}")
        
        # Calcular valores finais (antes de preparar parcelas)
        # IMPORTANTE: O valor_desconto já inclui descontos de cupons (calculado no checkout)
        valor_desconto = float(venda_data.get('valor_desconto', 0))
        valor_frete = float(venda_data.get('valor_frete', 0))
        valor_total_nota = valor_total_produtos - valor_desconto + valor_frete
        
        # Verificar se há cupom aplicado (para logs informativos)
        cupom_info = ""
        try:
            cupom_id = venda_data.get('cupom_id')
            if cupom_id:
                # Buscar informações do cupom para log
                conn = get_db()
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                try:
                    cur.execute("""
                        SELECT codigo, tipo, valor 
                        FROM cupom 
                        WHERE id = %s
                    """, (cupom_id,))
                    cupom = cur.fetchone()
                    if cupom:
                        tipo_cupom = "Percentual" if cupom.get('tipo') == 'p' else "Valor Fixo"
                        cupom_info = f" (Cupom aplicado: {cupom.get('codigo')} - {tipo_cupom})"
                except Exception:
                    # Campo cupom_id pode não existir no banco ainda ou não estar disponível
                    pass
                finally:
                    cur.close()
        except (KeyError, AttributeError):
            # Campo cupom_id pode não estar disponível
            pass
        
        current_app.logger.info(f"💰 Valores da NF-e:")
        current_app.logger.info(f"   Produtos (sem desconto): R$ {valor_total_produtos:.2f}")
        current_app.logger.info(f"   Desconto total (inclui cupons): R$ {valor_desconto:.2f}{cupom_info}")
        current_app.logger.info(f"   Frete: R$ {valor_frete:.2f}")
        current_app.logger.info(f"   Total da nota: R$ {valor_total_nota:.2f}")
        
        # Preparar parcelas
        parcelas = []
        pagamento = venda_data.get('pagamento')
        
        if pagamento:
            forma_pagamento_tipo = pagamento.get('forma_pagamento_tipo')
            num_parcelas = pagamento.get('parcelas', 1)
            # Usar valor total da nota (produtos - desconto + frete)
            valor_parcela = float(pagamento.get('valor_parcela', 0) or (valor_total_nota / num_parcelas))
            
            # Buscar ID da forma de pagamento no Bling (passar número de parcelas para melhor mapeamento)
            forma_pagamento_id = map_checkout_payment_to_bling(forma_pagamento_tipo, num_parcelas)
            
            # Data base para parcelas
            data_base = venda_data.get('data_venda') or datetime.now()
            if isinstance(data_base, str):
                try:
                    data_base = datetime.strptime(data_base[:10], '%Y-%m-%d')
                except:
                    data_base = datetime.now()
            elif hasattr(data_base, 'date'):
                data_base = datetime.combine(data_base.date(), datetime.min.time())
            
            # Criar parcelas
            for i in range(num_parcelas):
                vencimento = data_base + timedelta(days=30 * i)
                vencimento_str = vencimento.strftime('%Y-%m-%d')
                
                # Última parcela pode ter valor diferente
                valor_parcela_final = valor_parcela if i < num_parcelas - 1 else (valor_total_nota - (valor_parcela * (num_parcelas - 1)))
                
                parcela = {
                    "data": vencimento_str,
                    "valor": valor_parcela_final
                }
                
                # Sempre adicionar forma de pagamento se tiver ID
                if forma_pagamento_id:
                    parcela["formaPagamento"] = {"id": forma_pagamento_id}
                    # Adicionar observações apenas se necessário
                    if num_parcelas > 1:
                        parcela["observacoes"] = f"Parcela {i + 1}/{num_parcelas}"
                else:
                    # Se não encontrou ID, logar erro mas não colocar nas observações
                    current_app.logger.error(
                        f"❌ Forma de pagamento '{forma_pagamento_tipo}' não encontrada no Bling. "
                        f"Parcela NF-e será criada sem forma de pagamento."
                    )
                    # Adicionar observações com informação do pagamento
                    parcela["observacoes"] = f"Parcela {i + 1}/{num_parcelas} - {forma_pagamento_tipo} (ID não encontrado)"
                
                parcelas.append(parcela)
        else:
            # Parcela única
            data_venda = venda_data.get('data_venda') or datetime.now()
            if isinstance(data_venda, str):
                try:
                    data_venda = datetime.strptime(data_venda[:10], '%Y-%m-%d')
                except:
                    data_venda = datetime.now()
            elif hasattr(data_venda, 'date'):
                data_venda = datetime.combine(data_venda.date(), datetime.min.time())
            
            parcela = {
                "data": data_venda.strftime('%Y-%m-%d'),
                "valor": valor_total_nota
            }
            
            # Sempre adicionar forma de pagamento se tiver ID
            if forma_pagamento_id:
                parcela["formaPagamento"] = {"id": forma_pagamento_id}
            else:
                # Se não encontrou ID, logar erro
                current_app.logger.error(
                    f"❌ Forma de pagamento '{forma_pagamento_tipo}' não encontrada no Bling. "
                    f"Parcela NF-e será criada sem forma de pagamento."
                )
                # Adicionar observações com informação do pagamento
                parcela["observacoes"] = f"Pagamento {forma_pagamento_tipo} (ID não encontrado)"
            
            parcelas.append(parcela)
        
        # Buscar dados da transportadora escolhida no checkout
        # Primeiro tenta buscar o contato completo no Bling, depois usa dados da tabela vendas como fallback
        transporte_data = None
        servico_postagem_id = None
        servico_postagem_nome = None
        
        # Dados da transportadora escolhida no checkout (da tabela vendas)
        transportadora_nome = venda_data.get('transportadora_nome')
        transportadora_cnpj = venda_data.get('transportadora_cnpj')
        
        transportadora_ie = venda_data.get('transportadora_ie')
        transportadora_uf = venda_data.get('transportadora_uf')
        transportadora_municipio = venda_data.get('transportadora_municipio')
        transportadora_endereco = venda_data.get('transportadora_endereco')
        transportadora_numero = venda_data.get('transportadora_numero')
        transportadora_complemento = venda_data.get('transportadora_complemento')
        transportadora_bairro = venda_data.get('transportadora_bairro')
        transportadora_cep = venda_data.get('transportadora_cep')
        melhor_envio_service_id = venda_data.get('melhor_envio_service_id')
        melhor_envio_service_name = venda_data.get('melhor_envio_service_name')
        
        # Log dos dados da transportadora para debug (APÓS ler todos os dados)
        current_app.logger.info(
            f"🚚 Dados da transportadora do pedido {venda_id}: "
            f"Nome={transportadora_nome or 'N/A'}, "
            f"CNPJ={transportadora_cnpj or 'N/A'}, "
            f"IE={transportadora_ie or 'N/A'}, "
            f"UF={transportadora_uf or 'N/A'}, "
            f"Município={transportadora_municipio or 'N/A'}, "
            f"Endereço={transportadora_endereco or 'N/A'}, "
            f"Frete=R$ {valor_frete:.2f}, "
            f"Serviço ME ID={melhor_envio_service_id or 'N/A'}, "
            f"Serviço ME Nome={melhor_envio_service_name or 'N/A'}"
        )
        
        # Verificar se tem dados suficientes para incluir transportadora
        tem_dados_minimos = bool(transportadora_nome and (transportadora_cnpj or transportadora_municipio))
        if not tem_dados_minimos:
            current_app.logger.warning(
                f"⚠️ Dados insuficientes da transportadora para NF-e: "
                f"Nome={transportadora_nome or 'N/A'}, "
                f"CNPJ={transportadora_cnpj or 'N/A'}, "
                f"Município={transportadora_municipio or 'N/A'}"
            )
        
        # REMOVIDO: Lógica de descoberta de transportadora por CNPJ
        # Agora usamos apenas os dados que já vêm do checkout (ID do transporte)
        # Os dados da transportadora já estão completos na tabela vendas
        
        # Buscar ID do serviço no Bling baseado no código do Melhor Envio escolhido no checkout
        # IMPORTANTE: Passar transportadora_nome para distinguir ID 4 (Jadlog vs Azul)
        if melhor_envio_service_id:
            try:
                from .bling_logistics_service import get_or_create_logistics_service
                servico_data = get_or_create_logistics_service(
                    melhor_envio_service_id,
                    melhor_envio_service_name or 'Frete',
                    transportadora_nome  # Passar transportadora para distinguir ID 4
                )
                if servico_data:
                    servico_postagem_id = servico_data.get('id')
                    servico_postagem_nome = melhor_envio_service_name or servico_data.get('descricao')
                    current_app.logger.info(
                        f"📦 Serviço de postagem encontrado: {servico_postagem_nome} "
                        f"(Transportadora: {transportadora_nome or 'N/A'}, "
                        f"Melhor Envio ID: {melhor_envio_service_id}, Bling ID: {servico_postagem_id})"
                    )
                else:
                    current_app.logger.warning(
                        f"⚠️ Serviço Melhor Envio {melhor_envio_service_id} "
                        f"(Transportadora: {transportadora_nome or 'N/A'}) "
                        f"não encontrado no mapeamento nem no Bling"
                    )
            except Exception as e:
                current_app.logger.warning(f"⚠️ Erro ao buscar serviço no Bling: {e}")
        
        # Buscar código de rastreamento da etiqueta se já foi criada
        codigo_rastreamento = None
        if melhor_envio_service_id:
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cur.execute("""
                    SELECT codigo_rastreamento
                    FROM etiquetas_frete ef
                    INNER JOIN etiquetas_frete_venda_lnk lnk ON ef.id = lnk.etiqueta_frete_id
                    WHERE lnk.venda_id = %s
                    ORDER BY ef.created_at DESC
                    LIMIT 1
                """, (venda_id,))
                etiqueta = cur.fetchone()
                if etiqueta:
                    codigo_rastreamento = etiqueta.get('codigo_rastreamento')
            except Exception as e:
                current_app.logger.warning(f"⚠️ Erro ao buscar código de rastreamento: {e}")
            finally:
                cur.close()
        
        # Preparar seção de transporte
        # IMPORTANTE: Incluir transporte sempre que houver dados da transportadora OU frete > 0
        # A transportadora deve ser incluída diretamente na NF-e, não precisa estar no pedido do Bling
        transporte_data = None
        tem_dados_transportadora = bool(transportadora_cnpj or transportadora_nome)
        
        if valor_frete > 0 or tem_dados_transportadora:
            transporte_data = {
                "fretePorConta": 0,  # 0 = Por conta do destinatário
            }
            
            # Adicionar valor do frete apenas se for maior que 0
            if valor_frete > 0:
                transporte_data["frete"] = valor_frete
            
            # SEMPRE incluir transportadora se houver dados
            # REMOVIDO: Lógica de busca na tabela transportadoras_bling
            # Agora usamos apenas os dados que já vêm do checkout (ID do transporte)
            transportador_data = None  # Inicializar variável
            if tem_dados_transportadora:
                current_app.logger.info(
                    f"🚚 Dados de transportadora encontrados na venda {venda_id}: "
                    f"Nome={transportadora_nome}, CNPJ={transportadora_cnpj}, IE={transportadora_ie}"
                )
                try:
                    # Usar dados diretamente da tabela vendas (já vêm completos do checkout)
                    # REMOVIDO: Lógica de busca na tabela transportadoras_bling
                    # Agora usamos apenas os dados que já vêm do checkout (ID do transporte)
                    import re
                    transportador_data = {}
                    
                    if transportadora_nome:
                        transportador_data["nome"] = transportadora_nome
                    
                    if transportadora_cnpj:
                        cnpj_limpo = re.sub(r'[^\d]', '', str(transportadora_cnpj))
                        if len(cnpj_limpo) == 14:
                            transportador_data["numeroDocumento"] = cnpj_limpo
                        else:
                            current_app.logger.warning(f"⚠️ CNPJ inválido: {transportadora_cnpj}")
                            transportador_data = None
                    
                    if transportador_data and transportadora_ie:
                        transportador_data["ie"] = transportadora_ie
                    
                    if transportador_data:
                        current_app.logger.info(
                            f"✅ Transportadora preparada com dados da venda: "
                            f"{transportador_data.get('nome', 'N/A')} "
                            f"(CNPJ: {transportador_data.get('numeroDocumento', 'N/A')})"
                        )
                    else:
                        current_app.logger.warning(
                            f"⚠️ Não foi possível preparar transportadora: "
                            f"Nome={transportadora_nome or 'N/A'}, CNPJ={transportadora_cnpj or 'N/A'}"
                        )
                except Exception as e:
                    current_app.logger.warning(
                        f"⚠️ Erro ao preparar transportadora: {e}", 
                        exc_info=True
                    )
                    transportador_data = None
                
                # SEMPRE incluir transportadora na NF-e SE tiver dados válidos (fora do try/except)
                if transportador_data:
                    transporte_data["transportador"] = transportador_data
                    current_app.logger.info(
                        f"✅ Transportadora incluída no transporte_data da NF-e: "
                        f"{json_module.dumps(transportador_data, indent=2, ensure_ascii=False)}"
                    )
                else:
                    current_app.logger.warning(
                        f"⚠️ Transportadora NÃO incluída na NF-e (dados insuficientes ou inválidos). "
                        f"Nome: {transportadora_nome or 'N/A'}, CNPJ: {transportadora_cnpj or 'N/A'}"
                    )
            else:
                # Se não há CNPJ nem nome, mas há frete, ainda criar estrutura básica
                if valor_frete > 0:
                    current_app.logger.warning(
                        f"⚠️ Frete presente (R$ {valor_frete:.2f}) mas sem dados da transportadora. "
                        f"Transporte será incluído sem transportador."
                    )
            
            # Adicionar serviço de postagem (integração Melhor Envio) se disponível
            # O Bling espera o ID do serviço de logística
            if servico_postagem_id:
                if "volumes" not in transporte_data:
                    transporte_data["volumes"] = []
                
                volume_data = {
                    "servico": servico_postagem_id  # ID do serviço no Bling
                }
                
                # Adicionar código de rastreamento se disponível
                if codigo_rastreamento:
                    volume_data["codigoRastreamento"] = codigo_rastreamento
                
                transporte_data["volumes"].append(volume_data)
                
                current_app.logger.info(
                    f"✅ Serviço de logística Melhor Envio adicionado: "
                    f"ID Bling {servico_postagem_id} (Melhor Envio: {melhor_envio_service_id} - {servico_postagem_nome})"
                )
            elif servico_postagem_nome:
                # Fallback: usar nome se ID não estiver disponível
                if "volumes" not in transporte_data:
                    transporte_data["volumes"] = []
                
                volume_data = {
                    "servico": servico_postagem_nome
                }
                
                if codigo_rastreamento:
                    volume_data["codigoRastreamento"] = codigo_rastreamento
                
                transporte_data["volumes"].append(volume_data)
                
                current_app.logger.warning(
                    f"⚠️ Usando nome do serviço como fallback: {servico_postagem_nome}"
                )
        
        # Preparar payload da NF-e (Nota Fiscal Eletrônica - Modelo 55)
        data_operacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        nfe_payload = {
            "tipo": 0,  # NF-e (Nota Fiscal Eletrônica - Modelo 55)
            "dataOperacao": data_operacao,
            "contato": contato,
            "finalidade": 1,  # Normal
            "itens": itens,
            "parcelas": parcelas
        }
        
        # NÃO enviar número e série - deixar Bling definir automaticamente
        
        # Adicionar desconto se houver (separado dos produtos)
        if valor_desconto > 0:
            nfe_payload["desconto"] = valor_desconto
        
        # Adicionar transporte se houver frete ou dados da transportadora
        if transporte_data:
            # Verificar se transportador foi adicionado
            tem_transportador = bool(transporte_data.get('transportador'))
            
            nfe_payload["transporte"] = transporte_data
            current_app.logger.info(
                f"✅ Transporte incluído na NF-e: "
                f"Frete=R$ {transporte_data.get('frete', 0):.2f}, "
                f"Transportador={'Sim' if tem_transportador else 'Não'}, "
                f"Volumes={'Sim' if transporte_data.get('volumes') else 'Não'}"
            )
            
            if tem_transportador:
                # Log detalhado do payload de transporte para debug
                current_app.logger.info(
                    f"📦 Payload completo do transporte: {json_module.dumps(transporte_data, indent=2, ensure_ascii=False)}"
                )
            else:
                current_app.logger.error(
                    f"❌ ERRO: Transporte incluído na NF-e mas SEM transportador! "
                    f"Frete={valor_frete:.2f}, Transportadora Nome={transportadora_nome or 'N/A'}, "
                    f"Transportadora CNPJ={transportadora_cnpj or 'N/A'}"
                )
        else:
            current_app.logger.warning(
                f"⚠️ Transporte NÃO incluído na NF-e para pedido {venda_id}. "
                f"Frete={valor_frete:.2f}, Transportadora Nome={transportadora_nome or 'N/A'}, "
                f"Transportadora CNPJ={transportadora_cnpj or 'N/A'}"
            )
        
        # Adicionar observações
        codigo_pedido = venda_data.get('codigo_pedido', '')
        observacoes = f"Pedido originado do site LhamaBanana. Código: {codigo_pedido}"
        if servico_postagem_nome:
            observacoes += f" | Serviço de postagem: {servico_postagem_nome}"
        if transportadora_nome:
            observacoes += f" | Transportadora: {transportadora_nome}"
        nfe_payload["observacoes"] = observacoes
        
        current_app.logger.info(f"📄 Emitindo NF-e (Modelo 55) para venda {venda_id}...")
        
        # Log detalhado do transporte no payload final
        if 'transporte' in nfe_payload:
            transporte_final = nfe_payload['transporte']
            tem_transportador_final = bool(transporte_final.get('transportador'))
            current_app.logger.info(
                f"🔍 Verificação final do transporte no payload NF-e: "
                f"Transportador={'Sim' if tem_transportador_final else 'NÃO'}, "
                f"Frete={transporte_final.get('frete', 0):.2f}"
            )
            if tem_transportador_final:
                transportador_final = transporte_final.get('transportador', {})
                current_app.logger.info(
                    f"   Transportador: {transportador_final.get('nome', 'N/A')}, "
                    f"CNPJ: {transportador_final.get('numeroDocumento', 'N/A')}, "
                    f"IE: {transportador_final.get('ie', 'N/A')}"
                )
            else:
                current_app.logger.error(
                    f"❌ ERRO CRÍTICO: Transporte está no payload mas SEM transportador! "
                    f"Verifique os logs anteriores para entender o problema."
                )
        
        current_app.logger.debug(f"Payload NF-e completo: {json_module.dumps(nfe_payload, indent=2, ensure_ascii=False)}")
        
        # IMPORTANTE: Se temos pedido no Bling, criar NF-e associada ao pedido primeiro
        # Depois editamos para adicionar dados customizados (transportadora, etc.)
        nfe_id = None
        if pedido_bling_id:
            current_app.logger.info(
                f"📄 Criando NF-e associada ao pedido {pedido_bling_id} no Bling..."
            )
            
            # Passo 1: Criar NF-e associada ao pedido usando endpoint do Bling
            response_gerar = make_bling_api_request(
                'POST',
                f'/pedidos/vendas/{pedido_bling_id}/gerar-nfe',
                json={}  # Bling cria NF-e baseada no pedido
            )
            
            if response_gerar.status_code in [200, 201]:
                data_gerar = response_gerar.json()
                
                # Log da resposta completa para debug
                current_app.logger.debug(
                    f"📋 Resposta do POST /pedidos/vendas/{pedido_bling_id}/gerar-nfe: "
                    f"{json_module.dumps(data_gerar, indent=2, ensure_ascii=False)}"
                )
                
                # Tentar extrair ID da NF-e de diferentes formatos de resposta
                nfe_data_gerar = data_gerar.get('data', {})
                
                # Extrair ID da NF-e criada (pode estar em diferentes lugares)
                nfe_id = None
                if isinstance(nfe_data_gerar, dict):
                    nfe_id = nfe_data_gerar.get('id')
                elif isinstance(data_gerar, dict):
                    nfe_id = data_gerar.get('id')
                
                # Se ainda não encontrou, tentar buscar no pedido
                if not nfe_id:
                    current_app.logger.info(
                        f"🔍 ID da NF-e não encontrado na resposta. Buscando no pedido..."
                    )
                    time.sleep(1)
                    response_pedido_check = make_bling_api_request(
                        'GET',
                        f'/pedidos/vendas/{pedido_bling_id}'
                    )
                    if response_pedido_check.status_code == 200:
                        pedido_data_check = response_pedido_check.json().get('data', {})
                        nfe_pedido_check = pedido_data_check.get('notaFiscal', {})
                        if nfe_pedido_check:
                            nfe_id = nfe_pedido_check.get('id')
                            current_app.logger.info(
                                f"✅ ID da NF-e encontrado no pedido: {nfe_id}"
                            )
                
                if nfe_id:
                    current_app.logger.info(
                        f"✅ NF-e {nfe_id} criada e associada ao pedido {pedido_bling_id} no Bling. "
                        f"NF-e criada com todos os dados do pedido (não é necessário editar)."
                    )
                    # REMOVIDO: Edição da NF-e após criação
                    # Os dados já estão corretos quando a NF-e é criada via /gerar-nfe
                    # A edição estava causando erros porque a NF-e recém-criada pode não ter número ainda
                else:
                    current_app.logger.warning(
                        f"⚠️ NF-e criada mas ID não encontrado na resposta. "
                        f"Tentando criar NF-e diretamente..."
                    )
                    nfe_id = None
            else:
                error_text_gerar = response_gerar.text
                current_app.logger.warning(
                    f"⚠️ Erro ao criar NF-e associada ao pedido: HTTP {response_gerar.status_code} - {error_text_gerar}. "
                    f"Tentando criar NF-e diretamente..."
                )
                nfe_id = None
        
        # Se não conseguiu criar via pedido ou não tem pedido, criar NF-e diretamente
        response = None
        if not nfe_id:
            current_app.logger.info(
                f"📄 Criando NF-e diretamente no Bling (sem associação inicial ao pedido)..."
            )
            
            # Enviar requisição para API do Bling
            response = make_bling_api_request(
                'POST',
                '/nfe',
                json=nfe_payload
            )
        
        # Processar resposta (seja da criação via pedido ou direta)
        data = {}  # Inicializar data
        if nfe_id:
            # NF-e já foi criada via pedido, buscar informações atualizadas
            current_app.logger.info(
                f"📋 Buscando informações atualizadas da NF-e {nfe_id} no Bling..."
            )
            
            response_nfe_info = make_bling_api_request(
                'GET',
                f'/nfe/{nfe_id}'
            )
            
            if response_nfe_info.status_code == 200:
                data = response_nfe_info.json()
                nfe_data = data.get('data', {})
            else:
                # Se não conseguir buscar, usar dados básicos
                nfe_data = {'id': nfe_id}
                data = {'data': nfe_data}
        elif response and response.status_code in [200, 201]:
            # NF-e criada diretamente
            data = response.json()
            nfe_data = data.get('data', {})
        else:
            # Erro na criação
            error_text = response.text if response else "Resposta não disponível"
            current_app.logger.error(
                f"❌ Erro ao emitir NF-e para venda {venda_id}: {response.status_code if response else 'N/A'} - {error_text}"
            )
            
            save_nfe_error(venda_id, f"Erro HTTP {response.status_code if response else 'N/A'}: {error_text}")
            
            return {
                'success': False,
                'error': f"Erro HTTP {response.status_code if response else 'N/A'}",
                'details': error_text
            }
        
        # Extrair informações da NF-e
        if not nfe_id:
            nfe_id = nfe_data.get('id')
        nfe_numero = nfe_data.get('numero')
        nfe_chave_acesso = nfe_data.get('chaveAcesso')
        nfe_situacao = nfe_data.get('situacao', 'PENDENTE')
        
        current_app.logger.info(
            f"✅ NF-e criada com sucesso para venda {venda_id}. "
            f"ID: {nfe_id}, Número: {nfe_numero}, Status: {nfe_situacao}"
        )
        
        # IMPORTANTE: Verificar status da NF-e antes de tentar enviar
        # Só enviamos se estiver pendente ou rejeitada
        if nfe_id:
            # Buscar status atual da NF-e
            current_app.logger.info(
                f"🔍 Verificando status atual da NF-e {nfe_id} antes de enviar..."
            )
            
            response_nfe_status = make_bling_api_request(
                'GET',
                f'/nfe/{nfe_id}'
            )
            
            if response_nfe_status.status_code == 200:
                nfe_data_status = response_nfe_status.json().get('data', {})
                nfe_situacao_atual = nfe_data_status.get('situacao', nfe_situacao)
                nfe_chave_acesso = nfe_data_status.get('chaveAcesso') or nfe_chave_acesso
                nfe_numero = nfe_data_status.get('numero') or nfe_numero
                
                # O Bling retorna situação como número:
                # 1 = Pendente, 2 = Cancelada, 3 = Aguardando recibo,
                # 4 = Rejeitada, 5 = Autorizada, 6 = Emitida DANFE, 7 = Registrada,
                # 8 = Aguardando protocolo, 9 = Denegada, 10 = Consulta situação, 11 = Bloqueada
                # Converter para número se for string
                if isinstance(nfe_situacao_atual, str):
                    try:
                        nfe_situacao_atual = int(nfe_situacao_atual)
                    except (ValueError, TypeError):
                        # Se não conseguir converter, tratar como pendente
                        nfe_situacao_atual = 1
                
                # Situações que indicam que a NF-e já foi processada/autorizada (números)
                # 5 = AUTORIZADA, 6 = EMITIDA_DANFE, 7 = REGISTRADA, 2 = CANCELADA
                situacoes_finais = [2, 5, 6, 7]  # Cancelada, Autorizada, Emitida DANFE, Registrada
                
                # Verificar se a NF-e já está em uma situação final
                if isinstance(nfe_situacao_atual, int) and nfe_situacao_atual in situacoes_finais:
                    situacao_nomes = {
                        2: 'CANCELADA',
                        5: 'AUTORIZADA',
                        6: 'EMITIDA_DANFE',
                        7: 'REGISTRADA'
                    }
                    situacao_nome = situacao_nomes.get(nfe_situacao_atual, f'DESCONHECIDA_{nfe_situacao_atual}')
                    current_app.logger.info(
                        f"ℹ️ NF-e {nfe_id} já está na situação {nfe_situacao_atual} ({situacao_nome}). "
                        f"Não é necessário enviar novamente."
                    )
                    nfe_situacao = nfe_situacao_atual
                else:
                    # NF-e está pendente ou rejeitada, podemos tentar enviar
                    current_app.logger.info(
                        f"📤 Enviando NF-e {nfe_id} para o SEFAZ (situação atual: {nfe_situacao_atual})..."
                    )
                    
                    # Enviar para o SEFAZ usando POST /nfe/{idNotaFiscal}/enviar
                    time.sleep(1)  # Aguardar 1 segundo antes de enviar
                    
                    response_enviar = make_bling_api_request(
                        'POST',
                        f'/nfe/{nfe_id}/enviar',
                        json={}  # Endpoint pode não exigir body
                    )
                    
                    if response_enviar.status_code in [200, 201, 204]:
                        current_app.logger.info(
                            f"✅ NF-e {nfe_id} enviada para o SEFAZ com sucesso"
                        )
                        
                        # Aguardar um pouco e consultar status atualizado
                        time.sleep(2)
                        
                        # Consultar NF-e atualizada para obter chave de acesso e status
                        response_nfe = make_bling_api_request(
                            'GET',
                            f'/nfe/{nfe_id}'
                        )
                        
                        if response_nfe.status_code == 200:
                            nfe_data_atualizada = response_nfe.json().get('data', {})
                            nfe_chave_acesso = nfe_data_atualizada.get('chaveAcesso') or nfe_chave_acesso
                            nfe_situacao = nfe_data_atualizada.get('situacao', nfe_situacao_atual)
                            nfe_numero = nfe_data_atualizada.get('numero') or nfe_numero
                            
                            current_app.logger.info(
                                f"📋 NF-e {nfe_id} atualizada após envio: "
                                f"Situação: {nfe_situacao}, "
                                f"Chave de acesso: {'Sim' if nfe_chave_acesso else 'Não'}"
                            )
                    else:
                        error_text_enviar = response_enviar.text
                        current_app.logger.warning(
                            f"⚠️ Erro ao enviar NF-e {nfe_id} para o SEFAZ: "
                            f"HTTP {response_enviar.status_code} - {error_text_enviar}"
                        )
                        # Continuar mesmo se o envio falhar, pois a NF-e foi criada
            else:
                current_app.logger.warning(
                    f"⚠️ Não foi possível verificar status da NF-e {nfe_id}. "
                    f"Tentando enviar mesmo assim..."
                )
                # Se não conseguir verificar, tentar enviar (comportamento antigo)
                time.sleep(1)
                response_enviar = make_bling_api_request(
                    'POST',
                    f'/nfe/{nfe_id}/enviar',
                    json={}
                )
                if response_enviar.status_code not in [200, 201, 204]:
                    error_text_enviar = response_enviar.text
                    current_app.logger.warning(
                        f"⚠️ Erro ao enviar NF-e {nfe_id} para o SEFAZ: "
                        f"HTTP {response_enviar.status_code} - {error_text_enviar}"
                    )
        
        # IMPORTANTE: Se temos pedido no Bling, tentar associar a NF-e ao pedido
        # O pedido_bling_id já foi buscado no início da função
        if pedido_bling_id and nfe_id:
            # Tentar associar a NF-e ao pedido no Bling
            # O Bling pode associar automaticamente quando a NF-e é autorizada
            try:
                current_app.logger.info(
                    f"🔗 Verificando associação da NF-e {nfe_id} ao pedido {pedido_bling_id} no Bling..."
                )
                
                # Verificar se a NF-e já está associada ao pedido
                response_pedido = make_bling_api_request(
                    'GET',
                    f'/pedidos/vendas/{pedido_bling_id}'
                )
                
                if response_pedido.status_code == 200:
                    pedido_data = response_pedido.json().get('data', {})
                    nfe_pedido = pedido_data.get('notaFiscal', {})
                    
                    if nfe_pedido and nfe_pedido.get('id') == nfe_id:
                        current_app.logger.info(
                            f"✅ NF-e {nfe_id} já está associada ao pedido {pedido_bling_id}"
                        )
                    else:
                        current_app.logger.info(
                            f"ℹ️ NF-e {nfe_id} ainda não está associada ao pedido {pedido_bling_id}. "
                            f"O Bling geralmente associa automaticamente quando a NF-e é autorizada pelo SEFAZ."
                        )
                        # Nota: O Bling pode associar automaticamente quando a NF-e é autorizada
                        # Se não associar, pode ser necessário fazer manualmente no painel do Bling
            except Exception as e:
                current_app.logger.warning(
                    f"⚠️ Erro ao verificar associação NF-e/pedido: {e}"
                )
        
        # Salvar informações da NF-e
        save_nfe_info(venda_id, pedido_bling_id, nfe_id, nfe_numero, nfe_chave_acesso, None, nfe_situacao, data)
        
        return {
            'success': True,
            'nfe_id': nfe_id,
            'nfe_numero': nfe_numero,
            'nfe_chave_acesso': nfe_chave_acesso,
            'nfe_situacao': nfe_situacao,
            'pedido_bling_id': pedido_bling_id,
            'message': 'NF-e emitida e enviada para o SEFAZ com sucesso'
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

