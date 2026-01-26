from flask import Blueprint, jsonify, request, g, current_app, session
from ..decorators import admin_required_email
from ...services.bling_transportadora_sync_service import sync_transportadoras_from_bling
from datetime import datetime, timedelta
from firebase_admin import auth
from ...services.user_service import get_user_by_firebase_uid

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')

@admin_api_bp.route('/dashboard/stats', methods=['GET'])
@admin_required_email
def dashboard_stats():
    """Retorna estatísticas do dashboard"""
    try:
        conn = g.db
        cur = conn.cursor()
        
        # Estatísticas gerais
        stats = {}
        
        # Total de vendas
        cur.execute("SELECT COUNT(*), COALESCE(SUM(valor_total), 0) FROM vendas")
        total_vendas, receita_total = cur.fetchone()
        stats['total_vendas'] = total_vendas
        stats['receita_total'] = float(receita_total)
        
        # Vendas do mês
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(valor_total), 0)
            FROM vendas
            WHERE DATE_TRUNC('month', data_venda) = DATE_TRUNC('month', CURRENT_DATE)
        """)
        vendas_mes, receita_mes = cur.fetchone()
        stats['vendas_mes'] = vendas_mes
        stats['receita_mes'] = float(receita_mes)
        
        # Pedidos pendentes
        cur.execute("""
            SELECT COUNT(*) FROM vendas 
            WHERE status_pedido IN ('pendente_pagamento', 'processando_envio')
        """)
        stats['pedidos_pendentes'] = cur.fetchone()[0]
        
        # Etiquetas pendentes
        cur.execute("""
            SELECT COUNT(*) FROM etiquetas_frete
            WHERE status_etiqueta IN ('pendente', 'criada')
        """)
        stats['etiquetas_pendentes'] = cur.fetchone()[0]
        
        # Produtos com estoque baixo (menor que 10)
        cur.execute("""
            SELECT COUNT(*) FROM produtos WHERE estoque < 10
        """)
        stats['estoque_baixo'] = cur.fetchone()[0]
        
        # Vendas dos últimos 30 dias (para gráfico)
        cur.execute("""
            SELECT 
                DATE(data_venda) as dia,
                COUNT(*) as quantidade,
                COALESCE(SUM(valor_total), 0) as receita
            FROM vendas
            WHERE data_venda >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(data_venda)
            ORDER BY dia ASC
        """)
        
        vendas_30_dias = []
        for row in cur.fetchall():
            vendas_30_dias.append({
                'dia': row[0].strftime('%Y-%m-%d'),
                'quantidade': row[1],
                'receita': float(row[2])
            })
        stats['vendas_30_dias'] = vendas_30_dias
        
        # Top 5 produtos mais vendidos
        cur.execute("""
            SELECT 
                iv.nome_produto_snapshot,
                SUM(iv.quantidade) as total_vendido,
                SUM(iv.subtotal) as receita_produto
            FROM itens_venda iv
            JOIN vendas v ON iv.venda_id = v.id
            WHERE v.status_pedido != 'cancelado_pelo_vendedor'
            GROUP BY iv.nome_produto_snapshot
            ORDER BY total_vendido DESC
            LIMIT 5
        """)
        
        top_produtos = []
        for row in cur.fetchall():
            top_produtos.append({
                'nome': row[0],
                'quantidade': row[1],
                'receita': float(row[2])
            })
        stats['top_produtos'] = top_produtos
        
        return jsonify({"success": True, "stats": stats}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({"erro": "Erro ao buscar estatísticas"}), 500
    finally:
        cur.close()

@admin_api_bp.route('/etiquetas/list', methods=['GET'])
@admin_required_email
def list_labels():
    """Lista todas as etiquetas"""
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        conn = g.db
        cur = conn.cursor()
        
        query = """
            SELECT 
                e.*,
                v.codigo_pedido, v.valor_total, v.status_pedido,
                v.nome_recebedor, v.cidade_entrega, v.estado_entrega,
                v.data_venda
            FROM etiquetas_frete e
            JOIN vendas v ON e.venda_id = v.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND e.status_etiqueta = %s"
            params.append(status)
        
        query += " ORDER BY e.criado_em DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        columns = [desc[0] for desc in cur.description]
        labels = []
        for row in rows:
            label_dict = dict(zip(columns, row))
            # Converter datas para strings
            for key in ['criado_em', 'atualizado_em', 'paga_em', 'impressa_em', 'data_venda']:
                if label_dict.get(key) and isinstance(label_dict[key], datetime):
                    label_dict[key] = label_dict[key].isoformat()
            labels.append(label_dict)
        
        return jsonify({"success": True, "labels": labels}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar etiquetas: {e}")
        return jsonify({"erro": "Erro ao listar etiquetas"}), 500
    finally:
        cur.close()

@admin_api_bp.route('/estoque/list', methods=['GET'])
@admin_required_email
def list_estoque():
    """Lista produtos com informações de estoque"""
    try:
        conn = g.db
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                p.id,
                p.codigo_sku,
                np.nome as nome_produto,
                e.nome as estampa,
                t.nome as tamanho,
                p.estoque,
                p.preco_venda,
                p.preco_custo,
                (p.estoque * p.preco_custo) as valor_estoque,
                CASE 
                    WHEN p.estoque = 0 THEN 'zerado'
                    WHEN p.estoque < 10 THEN 'baixo'
                    WHEN p.estoque < 50 THEN 'medio'
                    ELSE 'alto'
                END as status_estoque
            FROM produtos p
            JOIN nome_produto np ON p.nome_produto_id = np.id
            JOIN estampa e ON p.estampa_id = e.id
            JOIN tamanho t ON p.tamanho_id = t.id
            ORDER BY p.estoque ASC, np.nome ASC
        """)
        
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        
        produtos = [dict(zip(columns, row)) for row in rows]
        
        return jsonify({"success": True, "produtos": produtos}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar estoque: {e}")
        return jsonify({"erro": "Erro ao listar estoque"}), 500
    finally:
        cur.close()

@admin_api_bp.route('/estoque/update', methods=['POST'])
@admin_required_email
def update_estoque():
    """Atualiza estoque de um produto"""
    try:
        data = request.get_json()
        produto_id = data.get('produto_id')
        nova_quantidade = data.get('quantidade')
        
        if not produto_id or nova_quantidade is None:
            return jsonify({"erro": "produto_id e quantidade são obrigatórios"}), 400
        
        conn = g.db
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE produtos 
            SET estoque = %s, atualizado_em = NOW()
            WHERE id = %s
            RETURNING id, estoque
        """, (nova_quantidade, produto_id))
        
        result = cur.fetchone()
        if not result:
            return jsonify({"erro": "Produto não encontrado"}), 404
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "produto_id": result[0],
            "novo_estoque": result[1]
        }), 200
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao atualizar estoque: {e}")
        return jsonify({"erro": "Erro ao atualizar estoque"}), 500
    finally:
        cur.close()

@admin_api_bp.route('/vendas/analytics', methods=['GET'])
@admin_required_email
def vendas_analytics():
    """Análise detalhada de vendas"""
    try:
        periodo = request.args.get('periodo', '30')  # dias
        conn = g.db
        cur = conn.cursor()
        
        analytics = {}
        
        # Vendas por período
        cur.execute(f"""
            SELECT 
                DATE_TRUNC('day', data_venda) as dia,
                COUNT(*) as quantidade,
                COALESCE(SUM(valor_total), 0) as receita,
                COALESCE(AVG(valor_total), 0) as ticket_medio
            FROM vendas
            WHERE data_venda >= CURRENT_DATE - INTERVAL '{periodo} days'
            AND status_pedido != 'cancelado_pelo_vendedor'
            GROUP BY DATE_TRUNC('day', data_venda)
            ORDER BY dia ASC
        """)
        
        vendas_por_dia = []
        for row in cur.fetchall():
            vendas_por_dia.append({
                'dia': row[0].strftime('%Y-%m-%d'),
                'quantidade': row[1],
                'receita': float(row[2]),
                'ticket_medio': float(row[3])
            })
        analytics['vendas_por_dia'] = vendas_por_dia
        
        # Vendas por status
        cur.execute("""
            SELECT 
                status_pedido,
                COUNT(*) as quantidade,
                COALESCE(SUM(valor_total), 0) as receita
            FROM vendas
            GROUP BY status_pedido
        """)
        
        vendas_por_status = []
        for row in cur.fetchall():
            vendas_por_status.append({
                'status': row[0],
                'quantidade': row[1],
                'receita': float(row[2])
            })
        analytics['vendas_por_status'] = vendas_por_status
        
        # Método de pagamento mais usado
        cur.execute("""
            SELECT 
                forma_pagamento_tipo,
                COUNT(*) as quantidade,
                COALESCE(SUM(valor_pago), 0) as total
            FROM pagamentos
            WHERE status_pagamento = 'PAID'
            GROUP BY forma_pagamento_tipo
            ORDER BY quantidade DESC
        """)
        
        pagamentos = []
        for row in cur.fetchall():
            pagamentos.append({
                'metodo': row[0],
                'quantidade': row[1],
                'total': float(row[2])
            })
        analytics['pagamentos'] = pagamentos
        
        return jsonify({"success": True, "analytics": analytics}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar analytics: {e}")
        return jsonify({"erro": "Erro ao buscar analytics"}), 500
    finally:
        cur.close()

@admin_api_bp.route('/pedidos/list', methods=['GET'])
@admin_required_email
def list_pedidos():
    """Lista todos os pedidos"""
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        conn = g.db
        cur = conn.cursor()
        
        query = """
            SELECT 
                v.*,
                COUNT(iv.id) as total_itens,
                STRING_AGG(iv.nome_produto_snapshot, ', ') as produtos
            FROM vendas v
            LEFT JOIN itens_venda iv ON v.id = iv.venda_id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND v.status_pedido = %s"
            params.append(status)
        
        query += """
            GROUP BY v.id
            ORDER BY v.data_venda DESC
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        columns = [desc[0] for desc in cur.description]
        pedidos = []
        for row in rows:
            pedido_dict = dict(zip(columns, row))
            # Converter datas
            for key in ['data_venda', 'criado_em', 'atualizado_em']:
                if pedido_dict.get(key) and isinstance(pedido_dict[key], datetime):
                    pedido_dict[key] = pedido_dict[key].isoformat()
            pedidos.append(pedido_dict)
        
        return jsonify({"success": True, "pedidos": pedidos}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar pedidos: {e}")
        return jsonify({"erro": "Erro ao listar pedidos"}), 500
    finally:
        cur.close()

@admin_api_bp.route('/pedidos/update-status', methods=['POST'])
@admin_required_email
def update_pedido_status():
    """Atualiza status de um pedido (usado pelo admin)"""
    try:
        data = request.get_json()
        venda_id = data.get('venda_id')
        novo_status = data.get('status')
        
        if not venda_id or not novo_status:
            return jsonify({"erro": "venda_id e status são obrigatórios"}), 400
        
        # Validar status permitidos
        status_permitidos = [
            'pendente', 'pendente_pagamento', 'processando_envio', 
            'enviado', 'entregue', 'cancelado_pelo_cliente', 
            'cancelado_pelo_vendedor', 'devolvido', 'reembolsado'
        ]
        
        if novo_status not in status_permitidos:
            return jsonify({"erro": f"Status inválido. Permited: {', '.join(status_permitidos)}"}), 400
        
        conn = g.db
        cur = conn.cursor()
        
        # Buscar status atual
        cur.execute("""
            SELECT status_pedido FROM vendas WHERE id = %s
        """, (venda_id,))
        
        resultado = cur.fetchone()
        if not resultado:
            return jsonify({"erro": "Pedido não encontrado"}), 404
        
        status_atual = resultado[0]
        
        # Atualizar status
        cur.execute("""
            UPDATE vendas
            SET status_pedido = %s,
                atualizado_em = NOW()
            WHERE id = %s
            RETURNING id, codigo_pedido, status_pedido
        """, (novo_status, venda_id))
        
        resultado_atualizado = cur.fetchone()
        conn.commit()
        
        # Sincronizar status da tabela orders
        try:
            from ...services.order_service import sync_order_status_from_venda
            sync_order_status_from_venda(venda_id)
        except Exception as sync_error:
            current_app.logger.warning(f"Erro ao sincronizar status do order: {sync_error}")
        
        # Gerenciar estoque conforme mudança de status
        try:
            from ...services.bling_stock_service import handle_order_status_change
            stock_result = handle_order_status_change(venda_id, status_atual, novo_status)
            if stock_result.get('success'):
                current_app.logger.info(f"✅ Estoque gerenciado após mudança de status (venda {venda_id})")
            else:
                current_app.logger.warning(f"⚠️ Falha ao gerenciar estoque (venda {venda_id}): {stock_result.get('error')}")
        except Exception as stock_error:
            current_app.logger.error(f"❌ Erro ao gerenciar estoque (venda {venda_id}): {stock_error}")
            # Não falhar a atualização de status por erro no estoque
        
        # REMOVIDO: Criação automática de etiqueta quando status muda para processando_envio
        # A etiqueta só será criada após aprovação do SEFAZ (no webhook de NFC-e)
        
        return jsonify({
            "success": True,
            "venda_id": resultado_atualizado[0],
            "codigo_pedido": resultado_atualizado[1],
            "status_anterior": status_atual,
            "status_novo": resultado_atualizado[2]
        }), 200
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao atualizar status do pedido: {e}")
        return jsonify({"erro": "Erro ao atualizar status do pedido"}), 500
    finally:
        cur.close()

@admin_api_bp.route('/transportadoras/sync', methods=['POST'])
@admin_required_email
def sync_transportadoras():
    """Sincroniza transportadoras do Bling com banco de dados local (sempre manual)"""
    try:
        # Sempre forçar sincronização (sincronização é manual)
        current_app.logger.info("🔄 Iniciando sincronização manual de transportadoras do Bling...")
        
        result = sync_transportadoras_from_bling(force_refresh=True)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Transportadoras sincronizadas com sucesso",
                "total_encontradas": result['total_encontradas'],
                "total_salvas": result['total_salvas'],
                "total_atualizadas": result['total_atualizadas'],
                "errors": result['errors']
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Erro ao sincronizar transportadoras",
                "errors": result['errors']
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar transportadoras: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"Erro ao sincronizar transportadoras: {str(e)}"
        }), 500

@admin_api_bp.route('/validate-strapi-access', methods=['POST'])
def validate_strapi_access():
    """
    Valida se o usuário pode acessar o Strapi.
    Verifica autenticação Firebase, role admin e MFA.
    Este endpoint é chamado pelo plugin flask-auth do Strapi.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token não fornecido'}), 401
    
    token = auth_header.split(' ')[1]
    
    try:
        # Verificar token Firebase
        decoded_token = auth.verify_id_token(token, check_revoked=False)
        uid = decoded_token['uid']
        
        # Buscar dados do usuário
        user_data = get_user_by_firebase_uid(uid)
        if not user_data:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Verificar role admin
        if user_data.get('role') != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Verificar MFA (assumir que foi verificado no login)
        # TODO: Implementar verificação real de MFA
        # Por enquanto, verificar se o usuário tem MFA habilitado
        mfa_verified = request.json.get('mfa_verified', False) if request.is_json else False
        
        # Se MFA for obrigatório, verificar
        # Por enquanto, apenas verificar se é admin
        if not mfa_verified:
            current_app.logger.warning(f"Tentativa de acesso ao Strapi sem MFA verificado: {uid}")
            # Em produção, descomentar para exigir MFA:
            # return jsonify({'error': 'MFA não verificado'}), 403
        
        # Retornar dados do usuário para o Strapi
        return jsonify({
            'uid': uid,
            'email': user_data.get('email'),
            'role': user_data.get('role'),
            'nome': user_data.get('nome'),
            'id': user_data.get('id'),
        }), 200
        
    except auth.InvalidIdTokenError:
        return jsonify({'error': 'Token inválido'}), 401
    except auth.ExpiredIdTokenError:
        return jsonify({'error': 'Token expirado'}), 401
    except Exception as e:
        current_app.logger.error(f"Erro ao validar acesso Strapi: {e}")
        return jsonify({'error': 'Erro ao validar autenticação'}), 500

