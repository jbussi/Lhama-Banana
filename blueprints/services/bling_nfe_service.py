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
from .bling_order_service import get_bling_order_by_local_id, get_order_for_bling_sync, get_payment_method_id_from_bling
import psycopg2.extras
from datetime import datetime, timedelta
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


def emit_nfe(venda_id: int) -> Dict:
    """
    Emite NF-e (Nota Fiscal Eletrônica - Modelo 55) para um pedido
    
    Esta função cria uma NF-e diretamente usando a API do Bling quando o pedido
    muda para "Em andamento". A NF-e é emitida como nota fiscal eletrônica (tipo 0 = NF-e modelo 55).
    
    Args:
        venda_id: ID da venda local
    
    Returns:
        Dict com resultado da emissão
    """
    try:
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
            
            # Buscar ID da forma de pagamento no Bling
            forma_pagamento_id = get_payment_method_id_from_bling(forma_pagamento_tipo)
            
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
                    "valor": valor_parcela_final,
                    "observacoes": f"Parcela {i + 1}/{num_parcelas} - {forma_pagamento_tipo}"
                }
                
                if forma_pagamento_id:
                    parcela["formaPagamento"] = {"id": forma_pagamento_id}
                
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
                "valor": valor_total_nota,
                "observacoes": "Pagamento à vista"
            }
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
        
        # Buscar contato completo da transportadora no Bling usando CNPJ
        transportadora_bling = None
        if transportadora_cnpj:
            try:
                from .bling_contact_service import find_contact_in_bling
                transportadora_bling = find_contact_in_bling(transportadora_cnpj)
                if transportadora_bling:
                    current_app.logger.info(
                        f"✅ Contato da transportadora encontrado no Bling: {transportadora_bling.get('nome')} "
                        f"(ID: {transportadora_bling.get('id')})"
                    )
                    # Usar dados completos do Bling
                    transportadora_nome = transportadora_bling.get('nome') or transportadora_nome
                    transportadora_cnpj = transportadora_bling.get('numeroDocumento') or transportadora_cnpj
                    transportadora_ie = transportadora_bling.get('ie') or transportadora_ie
                    
                    # Endereço do Bling
                    # A API do Bling pode retornar endereço em diferentes formatos
                    endereco_bling = transportadora_bling.get('endereco', {})
                    if endereco_bling:
                        # Tentar formato com 'geral' e 'cobranca'
                        geral = endereco_bling.get('geral') or endereco_bling.get('cobranca') or {}
                        # Se não tiver 'geral'/'cobranca', pode estar direto no objeto
                        if not geral and isinstance(endereco_bling, dict):
                            # Verificar se os campos estão diretamente no endereco_bling
                            if endereco_bling.get('endereco'):
                                geral = endereco_bling
                        
                        if geral:
                            transportadora_endereco = geral.get('endereco') or transportadora_endereco
                            transportadora_numero = str(geral.get('numero', '')).strip() or transportadora_numero
                            transportadora_complemento = geral.get('complemento') or transportadora_complemento
                            transportadora_bairro = geral.get('bairro') or transportadora_bairro
                            transportadora_municipio = geral.get('municipio') or transportadora_municipio
                            transportadora_uf = geral.get('uf') or transportadora_uf
                            # CEP pode vir com ou sem formatação
                            cep_bling = geral.get('cep') or ''
                            if cep_bling:
                                transportadora_cep = cep_bling.replace('-', '').replace(' ', '')
                else:
                    current_app.logger.warning(
                        f"⚠️ Transportadora não encontrada no Bling (CNPJ: {transportadora_cnpj}). "
                        f"Usando dados da tabela vendas."
                    )
            except Exception as e:
                current_app.logger.warning(
                    f"⚠️ Erro ao buscar transportadora no Bling: {e}. Usando dados da tabela vendas."
                )
        
        # Buscar ID do serviço no Bling baseado no código do Melhor Envio escolhido no checkout
        if melhor_envio_service_id:
            try:
                # Buscar serviços do Melhor Envio no Bling
                response = make_bling_api_request(
                    'GET',
                    '/logisticas/servicos',
                    params={
                        'tipoIntegracao': 'MelhorEnvio',
                        'limite': 100
                    }
                )
                
                if response.status_code == 200:
                    servicos_data = response.json().get('data', [])
                    
                    # Procurar serviço com código correspondente ao melhor_envio_service_id
                    # Preferir serviços da loja (LhamaBanana) se existirem
                    servico_bling = None
                    
                    # Primeiro, tentar encontrar serviço específico da loja
                    for servico in servicos_data:
                        if (servico.get('codigo') == str(melhor_envio_service_id) and 
                            'LhamaBanana' in servico.get('descricao', '')):
                            servico_bling = servico
                            break
                    
                    # Se não encontrou específico, usar qualquer serviço com o código
                    if not servico_bling:
                        for servico in servicos_data:
                            if servico.get('codigo') == str(melhor_envio_service_id):
                                servico_bling = servico
                                break
                    
                    if servico_bling:
                        servico_postagem_id = servico_bling.get('id')
                        servico_postagem_nome = melhor_envio_service_name or servico_bling.get('descricao')
                        current_app.logger.info(
                            f"📦 Serviço de postagem encontrado: {servico_postagem_nome} "
                            f"(Melhor Envio ID: {melhor_envio_service_id}, Bling ID: {servico_postagem_id})"
                        )
                    else:
                        current_app.logger.warning(
                            f"⚠️ Serviço Melhor Envio {melhor_envio_service_id} não encontrado no Bling"
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
        if valor_frete > 0:
            transporte_data = {
                "fretePorConta": 0,  # 0 = Por conta do destinatário
                "frete": valor_frete
            }
            
            # Adicionar dados completos da transportadora escolhida no checkout
            if transportadora_nome:
                transportador_data = {
                    "nome": transportadora_nome
                }
                
                # CNPJ
                if transportadora_cnpj:
                    # Limpar formatação do CNPJ
                    cnpj_limpo = str(transportadora_cnpj).replace('.', '').replace('-', '').replace('/', '')
                    transportador_data["numeroDocumento"] = cnpj_limpo
                
                # Inscrição Estadual
                if transportadora_ie:
                    transportador_data["ie"] = transportadora_ie
                
                # Endereço completo da transportadora
                if transportadora_endereco or transportadora_numero:
                    endereco_transportadora = {
                        "endereco": transportadora_endereco or "",
                        "numero": transportadora_numero or "",
                    }
                    
                    if transportadora_complemento:
                        endereco_transportadora["complemento"] = transportadora_complemento
                    
                    if transportadora_bairro:
                        endereco_transportadora["bairro"] = transportadora_bairro
                    
                    if transportadora_municipio:
                        endereco_transportadora["municipio"] = transportadora_municipio
                    
                    if transportadora_uf:
                        endereco_transportadora["uf"] = transportadora_uf.upper()
                    
                    if transportadora_cep:
                        # Limpar formatação do CEP
                        cep_limpo = str(transportadora_cep).replace('-', '').replace(' ', '')
                        endereco_transportadora["cep"] = cep_limpo
                    
                    transportador_data["endereco"] = endereco_transportadora
                
                transporte_data["transportador"] = transportador_data
                
                current_app.logger.info(
                    f"🚚 Transportadora adicionada ao transporte: {transportadora_nome} "
                    f"(CNPJ: {transportadora_cnpj}, IE: {transportadora_ie}, UF: {transportadora_uf})"
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
        
        # Adicionar transporte se houver frete
        if transporte_data:
            nfe_payload["transporte"] = transporte_data
        
        # Adicionar observações
        codigo_pedido = venda_data.get('codigo_pedido', '')
        observacoes = f"Pedido originado do site LhamaBanana. Código: {codigo_pedido}"
        if servico_postagem_nome:
            observacoes += f" | Serviço de postagem: {servico_postagem_nome}"
        if transportadora_nome:
            observacoes += f" | Transportadora: {transportadora_nome}"
        nfe_payload["observacoes"] = observacoes
        
        current_app.logger.info(f"📄 Emitindo NF-e (Modelo 55) para venda {venda_id}...")
        current_app.logger.debug(f"Payload NF-e: {json.dumps(nfe_payload, indent=2, ensure_ascii=False)}")
        
        # Enviar requisição para API do Bling
        response = make_bling_api_request(
            'POST',
            '/nfe',
            json=nfe_payload
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            nfe_data = data.get('data', {})
            
            # Extrair informações da NF-e
            nfe_id = nfe_data.get('id')
            nfe_numero = nfe_data.get('numero')
            nfe_chave_acesso = nfe_data.get('chaveAcesso')
            nfe_situacao = nfe_data.get('situacao', 'PENDENTE')
            
            current_app.logger.info(
                f"✅ NF-e emitida com sucesso para venda {venda_id}. "
                f"ID: {nfe_id}, Número: {nfe_numero}, Status: {nfe_situacao}"
            )
            
            # Salvar informações da NF-e
            # Buscar pedido Bling relacionado se existir
            bling_pedido = get_bling_order_by_local_id(venda_id)
            pedido_bling_id = bling_pedido.get('bling_pedido_id') if bling_pedido else None
            
            save_nfe_info(venda_id, pedido_bling_id, nfe_id, nfe_numero, nfe_chave_acesso, None, nfe_situacao, data)
            
            return {
                'success': True,
                'nfe_id': nfe_id,
                'nfe_numero': nfe_numero,
                'nfe_chave_acesso': nfe_chave_acesso,
                'nfe_situacao': nfe_situacao,
                'message': 'NF-e emitida com sucesso'
            }
        else:
            error_text = response.text
            current_app.logger.error(
                f"❌ Erro ao emitir NF-e para venda {venda_id}: {response.status_code} - {error_text}"
            )
            
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

