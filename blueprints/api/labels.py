from flask import Blueprint, request, jsonify, current_app, g
from ..services.label_service import label_service
from ..services import get_db
import json
from typing import Dict, Optional
import psycopg2.extras

labels_api_bp = Blueprint('labels_api', __name__, url_prefix='/api/labels')

def save_label_to_db(venda_id: int, codigo_pedido: str, shipment_data: Dict, 
                     order_data: Dict, shipping_option: Dict) -> int:
    """
    Salva informações da etiqueta no banco de dados
    
    Returns:
        ID da etiqueta criada
    """
    conn = g.db
    cur = conn.cursor()
    
    try:
        # Extrair dados relevantes do shipment
        protocol = shipment_data.get('protocol') or shipment_data.get('protocolo')
        service_id = shipping_option.get('service')
        service_name = shipping_option.get('name', '')
        
        # Inserir etiqueta no banco
        cur.execute("""
            INSERT INTO etiquetas_frete (
                venda_id, codigo_pedido,
                melhor_envio_shipment_id, melhor_envio_protocol,
                melhor_envio_service_id, melhor_envio_service_name,
                status_etiqueta,
                transportadora_nome, transportadora_codigo,
                cep_origem, cep_destino,
                peso_total, valor_frete, dimensoes,
                url_rastreamento, codigo_rastreamento,
                dados_etiqueta_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            venda_id, codigo_pedido,
            shipment_data.get('id'), protocol,
            service_id, service_name,
            'criada',  # Status inicial
            shipment_data.get('company', {}).get('name', ''), shipment_data.get('company', {}).get('id', ''),
            shipping_option.get('cep_origem', '').replace('-', ''), order_data.get('cep', '').replace('-', ''),
            shipping_option.get('peso_total', 0), shipping_option.get('price', 0),
            json.dumps(shipping_option.get('dimensoes', {})),
            shipment_data.get('tracking', {}).get('url', ''), shipment_data.get('tracking', {}).get('code', ''),
            json.dumps(shipment_data)
        ))
        
        etiqueta_id = cur.fetchone()[0]
        conn.commit()
        
        current_app.logger.info(f"Etiqueta {etiqueta_id} salva no banco para venda {venda_id}")
        return etiqueta_id
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao salvar etiqueta no banco: {e}")
        raise
    finally:
        cur.close()

def create_label_automatically(venda_id: int) -> Optional[int]:
    """
    Cria etiqueta automaticamente quando o pedido é aprovado.
    Esta função é chamada quando o status do pedido muda para 'processando_envio'.
    
    Args:
        venda_id: ID da venda
        
    Returns:
        ID da etiqueta criada, ou None se houver erro ou se já existir etiqueta
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Verificar se já existe etiqueta para esta venda
        cur.execute("""
            SELECT id FROM etiquetas_frete 
            WHERE venda_id = %s 
            ORDER BY criado_em DESC 
            LIMIT 1
        """, (venda_id,))
        existing_label = cur.fetchone()
        
        if existing_label:
            current_app.logger.info(f"Etiqueta já existe para venda {venda_id} (ID: {existing_label[0]})")
            return existing_label[0]
        
        # Buscar dados da venda
        cur.execute("""
            SELECT 
                id, codigo_pedido, valor_total, valor_frete,
                nome_recebedor, rua_entrega, numero_entrega, complemento_entrega,
                bairro_entrega, cidade_entrega, estado_entrega, cep_entrega,
                telefone_entrega, email_entrega
            FROM vendas 
            WHERE id = %s
        """, (venda_id,))
        
        venda_row = cur.fetchone()
        if not venda_row:
            current_app.logger.error(f"Venda {venda_id} não encontrada para criar etiqueta")
            return None
        
        venda_data = dict(venda_row)
        
        # Buscar itens da venda para calcular peso e dimensões
        cur.execute("""
            SELECT 
                iv.quantidade, 
                iv.nome_produto_snapshot,
                iv.produto_id
            FROM itens_venda iv
            WHERE iv.venda_id = %s
        """, (venda_id,))
        
        itens = cur.fetchall()
        
        # Calcular peso total (usar padrão: 500g por item)
        peso_total = 0.5  # Padrão: 500g por item
        if itens:
            quantidade_total = sum(item['quantidade'] for item in itens)
            peso_total = max(quantidade_total * 0.5, 0.3)  # Mínimo de 300g
        
        # Usar dimensões padrão (pode ser ajustado depois com campos de produtos)
        dimensoes = {
            'altura': 10,
            'largura': 20,
            'comprimento': 30
        }
        
        # Ajustar dimensões baseado na quantidade de itens
        if itens:
            quantidade_total = sum(item['quantidade'] for item in itens)
            if quantidade_total > 1:
                # Para múltiplos itens, aumentar comprimento proporcionalmente
                dimensoes['comprimento'] = max(30, quantidade_total * 15)
        
        # Preparar dados para o Melhor Envio
        order_data = {
            'nome_recebedor': venda_data['nome_recebedor'],
            'rua': venda_data['rua_entrega'],
            'numero': venda_data['numero_entrega'],
            'complemento': venda_data['complemento_entrega'] or '',
            'bairro': venda_data['bairro_entrega'],
            'cidade': venda_data['cidade_entrega'],
            'estado': venda_data['estado_entrega'],
            'cep': venda_data['cep_entrega'],
            'telefone': venda_data.get('telefone_entrega', ''),
            'email': venda_data.get('email_entrega', ''),
            'valor_total': float(venda_data['valor_total']),
            'produtos': []  # Será preenchido se necessário
        }
        
        # Preparar shipping_option (usar valor_frete e dimensões calculadas)
        # Para service, usar padrão (1 = PAC) - pode ser ajustado depois
        cep_origem = current_app.config.get('MELHOR_ENVIO_CEP_ORIGEM', '').replace('-', '').replace(' ', '')
        shipping_option = {
            'service': 1,  # PAC padrão - pode ser ajustado no futuro
            'name': 'PAC',  # Nome padrão
            'dimensoes': dimensoes,
            'peso_total': peso_total,
            'price': float(venda_data['valor_frete']),
            'cep_origem': cep_origem
        }
        
        current_app.logger.info(f"🚀 Criando etiqueta automaticamente para venda {venda_id}")
        current_app.logger.info(f"   Peso: {peso_total}kg, Dimensões: {dimensoes}")
        
        # Criar envio no Melhor Envio
        shipment_data = label_service.create_shipment(
            venda_id=venda_id,
            order_data=order_data,
            shipping_option=shipping_option
        )
        
        # Salvar etiqueta no banco de dados diretamente
        protocol = shipment_data.get('protocol') or shipment_data.get('protocolo')
        service_id = shipping_option.get('service')
        service_name = shipping_option.get('name', '')
        
        cur.execute("""
            INSERT INTO etiquetas_frete (
                venda_id, codigo_pedido,
                melhor_envio_shipment_id, melhor_envio_protocol,
                melhor_envio_service_id, melhor_envio_service_name,
                status_etiqueta,
                transportadora_nome, transportadora_codigo,
                cep_origem, cep_destino,
                peso_total, valor_frete, dimensoes,
                url_rastreamento, codigo_rastreamento,
                dados_etiqueta_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            venda_id, venda_data['codigo_pedido'],
            shipment_data.get('id'), protocol,
            service_id, service_name,
            'criada',
            shipment_data.get('company', {}).get('name', ''), 
            shipment_data.get('company', {}).get('id', ''),
            shipping_option.get('cep_origem', '').replace('-', ''), 
            order_data.get('cep', '').replace('-', ''),
            shipping_option.get('peso_total', 0), 
            shipping_option.get('price', 0),
            json.dumps(shipping_option.get('dimensoes', {})),
            shipment_data.get('tracking', {}).get('url', ''), 
            shipment_data.get('tracking', {}).get('code', ''),
            json.dumps(shipment_data)
        ))
        
        etiqueta_id = cur.fetchone()[0]
        conn.commit()
        
        # Buscar dados completos da etiqueta para sincronizar com Bling
        cur.execute("""
            SELECT codigo_rastreamento, transportadora_nome, url_rastreamento
            FROM etiquetas_frete
            WHERE id = %s
        """, (etiqueta_id,))
        
        etiqueta_completa = cur.fetchone()
        
        current_app.logger.info(f"✅ Etiqueta {etiqueta_id} criada automaticamente para venda {venda_id}")
        
        # Sincronizar código de rastreamento com Bling (se disponível)
        if etiqueta_completa and etiqueta_completa[0]:  # codigo_rastreamento
            try:
                from ..services.bling_logistics_service import sync_tracking_to_bling
                bling_result = sync_tracking_to_bling(
                    venda_id=venda_id,
                    codigo_rastreamento=etiqueta_completa[0],
                    transportadora=etiqueta_completa[1],  # transportadora_nome
                    url_rastreamento=etiqueta_completa[2]  # url_rastreamento
                )
                if bling_result.get('success'):
                    current_app.logger.info(f"✅ Código de rastreamento sincronizado com Bling para venda {venda_id}")
                else:
                    current_app.logger.warning(f"⚠️ Falha ao sincronizar rastreamento com Bling: {bling_result.get('error')}")
            except Exception as bling_error:
                current_app.logger.warning(f"⚠️ Erro ao sincronizar rastreamento com Bling: {bling_error}")
        
        return etiqueta_id
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar etiqueta automaticamente para venda {venda_id}: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        # Não falhar o processo principal se houver erro na criação da etiqueta
        return None
    finally:
        cur.close()


def get_label_from_db(venda_id: Optional[int] = None, 
                     codigo_pedido: Optional[str] = None,
                     etiqueta_id: Optional[int] = None) -> Optional[Dict]:
    """
    Busca etiqueta no banco de dados
    """
    conn = g.db
    cur = conn.cursor()
    
    try:
        if etiqueta_id:
            cur.execute("""
                SELECT * FROM etiquetas_frete WHERE id = %s
            """, (etiqueta_id,))
        elif venda_id:
            cur.execute("""
                SELECT * FROM etiquetas_frete WHERE venda_id = %s ORDER BY criado_em DESC LIMIT 1
            """, (venda_id,))
        elif codigo_pedido:
            cur.execute("""
                SELECT * FROM etiquetas_frete WHERE codigo_pedido = %s ORDER BY criado_em DESC LIMIT 1
            """, (codigo_pedido,))
        else:
            return None
        
        row = cur.fetchone()
        if not row:
            return None
        
        # Converter row em dict
        columns = [desc[0] for desc in cur.description]
        label_data = dict(zip(columns, row))
        
        return label_data
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar etiqueta no banco: {e}")
        return None
    finally:
        cur.close()

@labels_api_bp.route('/create/<int:venda_id>', methods=['POST'])
def create_label(venda_id: int):
    """
    Cria uma etiqueta de frete para um pedido
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Dados da requisição ausentes"}), 400
        
        # Buscar dados do pedido no banco
        conn = g.db
        cur = conn.cursor()
        
        try:
            # Buscar dados da venda
            cur.execute("""
                SELECT 
                    id, codigo_pedido, valor_total, valor_frete,
                    nome_recebedor, rua_entrega, numero_entrega, complemento_entrega,
                    bairro_entrega, cidade_entrega, estado_entrega, cep_entrega
                FROM vendas WHERE id = %s
            """, (venda_id,))
            
            venda_row = cur.fetchone()
            if not venda_row:
                return jsonify({"erro": "Pedido não encontrado"}), 404
            
            # Converter para dict
            venda_columns = ['id', 'codigo_pedido', 'valor_total', 'valor_frete',
                           'nome_recebedor', 'rua_entrega', 'numero_entrega', 'complemento_entrega',
                           'bairro_entrega', 'cidade_entrega', 'estado_entrega', 'cep_entrega']
            venda_data = dict(zip(venda_columns, venda_row))
            
            # Buscar itens da venda para calcular peso e dimensões
            cur.execute("""
                SELECT 
                    iv.quantidade, iv.nome_produto_snapshot,
                    p.estoque, p.preco_venda
                FROM itens_venda iv
                LEFT JOIN produtos p ON iv.produto_id = p.id
                WHERE iv.venda_id = %s
            """, (venda_id,))
            
            itens = cur.fetchall()
            peso_total = len(itens) * 0.5  # Simulado: 500g por item
            valor_total = float(venda_data['valor_total'])
            
            # Preparar dados para o Melhor Envio
            order_data = {
                'nome_recebedor': venda_data['nome_recebedor'],
                'rua': venda_data['rua_entrega'],
                'numero': venda_data['numero_entrega'],
                'complemento': venda_data['complemento_entrega'] or '',
                'bairro': venda_data['bairro_entrega'],
                'cidade': venda_data['cidade_entrega'],
                'estado': venda_data['estado_entrega'],
                'cep': venda_data['cep_entrega'],
                'valor_total': valor_total,
                'produtos': []  # Será preenchido conforme necessário
            }
            
            shipping_option = data.get('shipping_option', {
                'service': 1,  # PAC padrão
                'dimensoes': {
                    'altura': 10,
                    'largura': 20,
                    'comprimento': 30
                },
                'peso_total': peso_total,
                'price': float(venda_data['valor_frete'])
            })
            
            # Criar envio no Melhor Envio
            shipment_data = label_service.create_shipment(
                venda_id=venda_id,
                order_data=order_data,
                shipping_option=shipping_option
            )
            
            # Salvar no banco de dados
            etiqueta_id = save_label_to_db(
                venda_id=venda_id,
                codigo_pedido=venda_data['codigo_pedido'],
                shipment_data=shipment_data,
                order_data=order_data,
                shipping_option=shipping_option
            )
            
            # Atualizar status do pedido
            cur.execute("""
                UPDATE vendas SET status_pedido = 'processando_envio' WHERE id = %s
            """, (venda_id,))
            conn.commit()
            
            # Verificar se precisa emitir NFe
            try:
                from ..services.nfe_service import check_and_emit_nfe
                nfe_result = check_and_emit_nfe(venda_id)
                if nfe_result:
                    current_app.logger.info(f"NFe registrada para venda {venda_id}: {nfe_result}")
            except Exception as nfe_error:
                current_app.logger.error(f"Erro ao processar NFe para venda {venda_id}: {nfe_error}")
                # Não falhar a criação da etiqueta por erro na NFe
            
            return jsonify({
                "success": True,
                "etiqueta_id": etiqueta_id,
                "shipment_id": shipment_data.get('id'),
                "protocol": shipment_data.get('protocol') or shipment_data.get('protocolo'),
                "mensagem": "Etiqueta criada com sucesso. Faça o checkout para pagar e gerar a etiqueta."
            }), 201
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao criar etiqueta: {e}")
            return jsonify({"erro": f"Erro ao criar etiqueta: {str(e)}"}), 500
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro na API de criação de etiqueta: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@labels_api_bp.route('/checkout/<int:etiqueta_id>', methods=['POST'])
def checkout_label(etiqueta_id: int):
    """
    Faz checkout (paga) de uma etiqueta no Melhor Envio
    """
    try:
        # Buscar etiqueta no banco
        etiqueta_data = get_label_from_db(etiqueta_id=etiqueta_id)
        if not etiqueta_data:
            return jsonify({"erro": "Etiqueta não encontrada"}), 404
        
        shipment_id = etiqueta_data['melhor_envio_shipment_id']
        if not shipment_id:
            return jsonify({"erro": "ID do envio não encontrado"}), 400
        
        # Fazer checkout no Melhor Envio
        checkout_result = label_service.checkout_shipment(shipment_id)
        
        # Atualizar status no banco
        conn = g.db
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE etiquetas_frete 
                SET status_etiqueta = 'paga', paga_em = NOW()
                WHERE id = %s
            """, (etiqueta_id,))
            conn.commit()
            
            return jsonify({
                "success": True,
                "mensagem": "Etiqueta paga com sucesso. Agora você pode gerar o link de impressão."
            }), 200
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao atualizar status da etiqueta: {e}")
            return jsonify({"erro": "Erro ao atualizar status"}), 500
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro no checkout da etiqueta: {e}")
        return jsonify({"erro": f"Erro ao fazer checkout: {str(e)}"}), 500

@labels_api_bp.route('/print/<int:etiqueta_id>', methods=['GET'])
def print_label(etiqueta_id: int):
    """
    Gera link para impressão da etiqueta
    """
    try:
        # Buscar etiqueta no banco
        etiqueta_data = get_label_from_db(etiqueta_id=etiqueta_id)
        if not etiqueta_data:
            return jsonify({"erro": "Etiqueta não encontrada"}), 404
        
        shipment_id = etiqueta_data['melhor_envio_shipment_id']
        if not shipment_id:
            return jsonify({"erro": "ID do envio não encontrado"}), 400
        
        # Gerar link de impressão
        print_data = label_service.print_label(shipment_id)
        
        # Atualizar URL da etiqueta no banco
        conn = g.db
        cur = conn.cursor()
        
        try:
            url_etiqueta = print_data.get('url') or print_data.get('link')
            
            # Buscar venda_id antes de atualizar
            cur.execute("""
                SELECT venda_id, codigo_rastreamento, transportadora_nome, url_rastreamento
                FROM etiquetas_frete
                WHERE id = %s
            """, (etiqueta_id,))
            
            etiqueta_info = cur.fetchone()
            venda_id = etiqueta_info[0] if etiqueta_info else None
            
            cur.execute("""
                UPDATE etiquetas_frete 
                SET url_etiqueta = %s, status_etiqueta = 'impressa', impressa_em = NOW()
                WHERE id = %s
            """, (url_etiqueta, etiqueta_id))
            
            # Atualizar status do pedido para 'enviado' quando etiqueta for impressa
            if venda_id:
                try:
                    cur.execute("""
                        UPDATE vendas
                        SET status_pedido = 'enviado',
                            data_envio = NOW(),
                            atualizado_em = NOW()
                        WHERE id = %s AND status_pedido = 'processando_envio'
                    """, (venda_id,))
                    
                    # Sincronizar status de envio com Bling
                    if cur.rowcount > 0:  # Se status foi atualizado
                        try:
                            from ..services.bling_logistics_service import sync_shipping_status_to_bling
                            bling_result = sync_shipping_status_to_bling(venda_id, 'enviado')
                            if bling_result.get('success'):
                                current_app.logger.info(f"✅ Status 'enviado' sincronizado com Bling para venda {venda_id}")
                        except Exception as bling_error:
                            current_app.logger.warning(f"⚠️ Erro ao sincronizar status com Bling: {bling_error}")
                    
                    # Sincronizar código de rastreamento se ainda não foi sincronizado
                    if etiqueta_info and etiqueta_info[1]:  # codigo_rastreamento
                        try:
                            from ..services.bling_logistics_service import sync_tracking_to_bling
                            sync_tracking_to_bling(
                                venda_id=venda_id,
                                codigo_rastreamento=etiqueta_info[1],
                                transportadora=etiqueta_info[2],
                                url_rastreamento=etiqueta_info[3]
                            )
                        except Exception as bling_error:
                            current_app.logger.warning(f"⚠️ Erro ao sincronizar rastreamento com Bling: {bling_error}")
                            
                except Exception as status_error:
                    current_app.logger.warning(f"⚠️ Erro ao atualizar status do pedido: {status_error}")
            
            conn.commit()
            
            return jsonify({
                "success": True,
                "url_etiqueta": url_etiqueta,
                "print_data": print_data
            }), 200
            
        except Exception as e:
            conn.rollback()
            current_app.logger.error(f"Erro ao atualizar URL da etiqueta: {e}")
            return jsonify({"erro": "Erro ao atualizar URL"}), 500
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar link de impressão: {e}")
        return jsonify({"erro": f"Erro ao gerar link: {str(e)}"}), 500

@labels_api_bp.route('/track/<int:etiqueta_id>', methods=['GET'])
def track_label(etiqueta_id: int):
    """
    Rastreia uma etiqueta
    """
    try:
        # Buscar etiqueta no banco
        etiqueta_data = get_label_from_db(etiqueta_id=etiqueta_id)
        if not etiqueta_data:
            return jsonify({"erro": "Etiqueta não encontrada"}), 404
        
        shipment_id = etiqueta_data['melhor_envio_shipment_id']
        if not shipment_id:
            return jsonify({"erro": "ID do envio não encontrado"}), 400
        
        # Rastrear no Melhor Envio
        tracking_data = label_service.track_shipment(shipment_id)
        
        return jsonify({
            "success": True,
            "tracking": tracking_data,
            "codigo_rastreamento": etiqueta_data.get('codigo_rastreamento'),
            "url_rastreamento": etiqueta_data.get('url_rastreamento')
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao rastrear etiqueta: {e}")
        return jsonify({"erro": f"Erro ao rastrear: {str(e)}"}), 500

@labels_api_bp.route('/list', methods=['GET'])
def list_labels():
    """
    Lista todas as etiquetas (com filtros opcionais)
    """
    try:
        status = request.args.get('status')
        venda_id = request.args.get('venda_id', type=int)
        
        conn = g.db
        cur = conn.cursor()
        
        try:
            query = """
                SELECT 
                    e.*,
                    v.codigo_pedido, v.valor_total, v.status_pedido,
                    v.nome_recebedor, v.cidade_entrega, v.estado_entrega
                FROM etiquetas_frete e
                JOIN vendas v ON e.venda_id = v.id
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND e.status_etiqueta = %s"
                params.append(status)
            
            if venda_id:
                query += " AND e.venda_id = %s"
                params.append(venda_id)
            
            query += " ORDER BY e.criado_em DESC LIMIT 100"
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            columns = [desc[0] for desc in cur.description]
            labels = [dict(zip(columns, row)) for row in rows]
            
            return jsonify({
                "success": True,
                "labels": labels,
                "total": len(labels)
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Erro ao listar etiquetas: {e}")
            return jsonify({"erro": "Erro ao listar etiquetas"}), 500
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro na API de listagem: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@labels_api_bp.route('/order/<string:codigo_pedido>', methods=['GET'])
def get_label_by_order(codigo_pedido: str):
    """
    Busca etiqueta pelo código do pedido
    """
    try:
        etiqueta_data = get_label_from_db(codigo_pedido=codigo_pedido)
        
        if not etiqueta_data:
            return jsonify({
                "success": False,
                "mensagem": "Etiqueta não encontrada para este pedido"
            }), 404
        
        return jsonify({
            "success": True,
            "label": etiqueta_data
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar etiqueta: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

