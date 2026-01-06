from . import api_bp
from flask import jsonify, request
from ..services import get_db

@api_bp.route('/store/filters', methods=['GET'])
def get_store_filters():
    """Endpoint para obter filtros disponíveis na loja (tamanhos, estampas, categorias)."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        filters = {
            'categorias': [],
            'tamanhos': [],
            'estampas': [],
            'precos': [
                {'label': 'Até R$ 50', 'min': 0, 'max': 50},
                {'label': 'R$ 50 - R$ 100', 'min': 50, 'max': 100},
                {'label': 'R$ 100 - R$ 200', 'min': 100, 'max': 200},
                {'label': 'Acima de R$ 200', 'min': 200, 'max': None}
            ]
        }
        
        # Buscar categorias ativas
        cur.execute("""
            SELECT DISTINCT c.id, c.nome
            FROM categorias c
            JOIN nome_produto np ON c.id = np.categoria_id
            WHERE c.ativo = TRUE
            ORDER BY c.nome
        """)
        categorias = cur.fetchall()
        filters['categorias'] = [{'id': cat[0], 'nome': cat[1]} for cat in categorias]
        
        # Buscar tamanhos disponíveis (apenas os que têm produtos em estoque)
        cur.execute("""
            SELECT DISTINCT t.id, t.nome
            FROM tamanho t
            JOIN produtos p ON t.id = p.tamanho_id
            WHERE t.ativo = TRUE AND p.estoque > 0
            ORDER BY t.ordem_exibicao, t.nome
        """)
        tamanhos = cur.fetchall()
        filters['tamanhos'] = [{'id': tam[0], 'nome': tam[1]} for tam in tamanhos]
        
        # Buscar estampas disponíveis (apenas as que têm produtos em estoque)
        cur.execute("""
            SELECT DISTINCT e.id, e.nome, e.imagem_url
            FROM estampa e
            JOIN produtos p ON e.id = p.estampa_id
            WHERE e.ativo = TRUE AND p.estoque > 0
            ORDER BY e.ordem_exibicao, e.nome
        """)
        estampas = cur.fetchall()
        filters['estampas'] = [{'id': est[0], 'nome': est[1], 'imagem_url': est[2]} for est in estampas]
        
        return jsonify(filters), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro ao carregar filtros."}), 500
    finally:
        cur.close()

@api_bp.route('/base_products', methods=['GET'])
def get_base_products():
    """Endpoint para listar produtos base (para a página da loja) com suporte a filtros."""
    base_products_list = []
    conn = get_db()
    cur = conn.cursor()

    try:
        # Obter parâmetros de filtro da query string
        categoria_ids = request.args.getlist('categoria_id', type=int)
        tamanho_ids = request.args.getlist('tamanho_id', type=int)
        estampa_ids = request.args.getlist('estampa_id', type=int)
        preco_min = request.args.get('preco_min', type=float)
        preco_max = request.args.get('preco_max', type=float)
        
        # Construir query base
        query = """
            SELECT DISTINCT
                np.id AS nome_produto_id,
                np.nome AS nome_produto,
                np.descricao AS descricao_produto,
                c.nome AS categoria_nome,
                c.id AS categoria_id,
                (SELECT ip.url FROM produtos p_var
                 JOIN imagens_produto ip ON p_var.id = ip.produto_id
                 WHERE p_var.nome_produto_id = np.id
                 ORDER BY ip.ordem ASC
                 LIMIT 1) AS imagem_representativa_url,
                (SELECT MIN(p_var.preco_venda) FROM produtos p_var WHERE p_var.nome_produto_id = np.id) AS preco_minimo,
                (SELECT COUNT(*) FROM produtos p_var WHERE p_var.nome_produto_id = np.id AND p_var.estoque > 0) AS variacoes_em_estoque_count
            FROM nome_produto np
            JOIN categorias c ON np.categoria_id = c.id
            WHERE np.ativo = TRUE
        """
        
        params = []
        conditions = []
        
        # Aplicar filtros
        if categoria_ids:
            conditions.append(f"c.id = ANY(%s)")
            params.append(categoria_ids)
        
        # Construir condições para filtros de variações (produtos)
        variation_conditions = []
        variation_params = []
        
        if tamanho_ids:
            variation_conditions.append("p.tamanho_id = ANY(%s)")
            variation_params.append(tamanho_ids)
        
        if estampa_ids:
            variation_conditions.append("p.estampa_id = ANY(%s)")
            variation_params.append(estampa_ids)
        
        if preco_min is not None:
            variation_conditions.append("p.preco_venda >= %s")
            variation_params.append(preco_min)
        
        if preco_max is not None:
            variation_conditions.append("p.preco_venda <= %s")
            variation_params.append(preco_max)
        
        # Se houver filtros de variação, adicionar subquery
        if variation_conditions:
            # Garantir que há produtos em estoque
            variation_conditions.append("p.estoque > 0")
            
            # Construir a subquery com placeholders
            subquery = "EXISTS (SELECT 1 FROM produtos p WHERE p.nome_produto_id = np.id AND " + \
                      " AND ".join(variation_conditions) + ")"
            conditions.append(subquery)
            params.extend(variation_params)
        else:
            # Se não houver filtros de variação, ainda mostrar apenas produtos com estoque
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM produtos p
                    WHERE p.nome_produto_id = np.id
                    AND p.estoque > 0
                )
            """)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY np.nome"
        
        cur.execute(query, params)
        products_db = cur.fetchall()

        for prod in products_db:
            base_products_list.append({
                'id': prod[0],
                'nome': prod[1],
                'descricao': prod[2],
                'categoria': prod[3],
                'categoria_id': prod[4],
                'imagem_url': prod[5] if prod[5] else '/static/img/placeholder.jpg',
                'preco_minimo': float(prod[6]) if prod[6] is not None else None,
                'estoque': prod[7]
            })

        return jsonify(base_products_list), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor ao carregar produtos base."}), 500
    finally:
        cur.close()