from . import api_bp
from flask import jsonify, request, current_app
from ..services import get_db, execute_query_safely

@api_bp.route('/store/filters', methods=['GET'])
def get_store_filters():
    """Endpoint para obter filtros disponíveis na loja (tamanhos, estampas, categorias)."""
    try:
        conn = get_db()
        if not conn:
            return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
        
        # Garantir rollback antes de começar
        try:
            conn.rollback()
        except Exception:
            # Se rollback falhar, tentar obter nova conexão
            conn = get_db()
        
        filters = {
            'categorias': [],
            'tamanhos': [],
            'estampas': [],
            'tecidos': [],
            'sexos': [
                {'value': 'm', 'label': 'Masculino'},
                {'value': 'f', 'label': 'Feminino'},
                {'value': 'u', 'label': 'Unissex'}
            ],
            'precos': [
                {'label': 'Até R$ 50', 'min': 0, 'max': 50},
                {'label': 'R$ 50 - R$ 100', 'min': 50, 'max': 100},
                {'label': 'R$ 100 - R$ 200', 'min': 100, 'max': 200},
                {'label': 'Acima de R$ 200', 'min': 200, 'max': None}
            ]
        }
        
        # Buscar categorias ativas (que têm produtos)
        try:
            categorias = execute_query_safely("""
                SELECT DISTINCT c.id, c.nome
                FROM categorias c
                JOIN nome_produto_categoria_lnk npc ON c.id = npc.categoria_id
                JOIN nome_produto np ON npc.nome_produto_id = np.id
                JOIN produtos_nome_produto_lnk pnp ON np.id = pnp.nome_produto_id
                JOIN produtos p ON pnp.produto_id = p.id
                WHERE c.ativo = TRUE AND np.ativo = TRUE AND p.ativo = TRUE
                ORDER BY c.nome
            """, fetch_mode='all')
            filters['categorias'] = [{'id': cat[0], 'nome': cat[1]} for cat in categorias] if categorias else []
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar categorias: {e}", exc_info=True)
            filters['categorias'] = []
        
        # Buscar tamanhos disponíveis (apenas os que têm produtos em estoque)
        try:
            tamanhos = execute_query_safely("""
                SELECT DISTINCT t.id, t.nome, COALESCE(t.ordem_exibicao, 999) as ordem
                FROM tamanho t
                JOIN produtos_tamanho_lnk pt ON t.id = pt.tamanho_id
                JOIN produtos p ON pt.produto_id = p.id
                WHERE t.ativo = TRUE AND p.ativo = TRUE
                ORDER BY ordem, t.nome
            """, fetch_mode='all')
            filters['tamanhos'] = [{'id': tam[0], 'nome': tam[1]} for tam in tamanhos] if tamanhos else []
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar tamanhos: {e}", exc_info=True)
            filters['tamanhos'] = []
        
        # Verificar se a tabela tecidos existe
        tecidos_table_exists = False
        try:
            result = execute_query_safely("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'tecidos'
                )
            """, fetch_mode='one')
            if result:
                tecidos_table_exists = result[0]
        except Exception as e:
            current_app.logger.warning(f"Erro ao verificar existência da tabela tecidos: {e}")
            tecidos_table_exists = False
        
        # Buscar estampas disponíveis (apenas as que têm produtos em estoque)
        try:
            if tecidos_table_exists:
                # Verificar se existe tabela de relacionamento estampa_tecido_lnk
                tecido_lnk_exists = False
                try:
                    result = execute_query_safely("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'estampa_tecido_lnk'
                        )
                    """, fetch_mode='one')
                    tecido_lnk_exists = result[0] if result else False
                except Exception:
                    tecido_lnk_exists = False
                
                try:
                    if tecido_lnk_exists:
                        # Usar tabela de relacionamento estampa_tecido_lnk
                        estampas = execute_query_safely("""
                            SELECT DISTINCT e.id, e.nome, e.imagem_url, t.id as tecido_id, t.nome as tecido_nome, e.sexo, COALESCE(e.ordem_exibicao, 999) as ordem
                            FROM estampa e
                            JOIN produtos_estampa_lnk pe ON e.id = pe.estampa_id
                            JOIN produtos p ON pe.produto_id = p.id
                            LEFT JOIN estampa_tecido_lnk etl ON e.id = etl.estampa_id
                            LEFT JOIN tecidos t ON etl.tecido_id = t.id
                            WHERE e.ativo = TRUE AND p.ativo = TRUE
                            ORDER BY ordem, e.nome
                        """, fetch_mode='all')
                    else:
                        # Sem tabela de link, buscar estampas sem tecido
                        estampas = execute_query_safely("""
                            SELECT DISTINCT e.id, e.nome, e.imagem_url, NULL as tecido_id, NULL as tecido_nome, e.sexo, COALESCE(e.ordem_exibicao, 999) as ordem
                            FROM estampa e
                            JOIN produtos_estampa_lnk pe ON e.id = pe.estampa_id
                            JOIN produtos p ON pe.produto_id = p.id
                            WHERE e.ativo = TRUE AND p.ativo = TRUE
                            ORDER BY ordem, e.nome
                        """, fetch_mode='all')
                    filters['estampas'] = [{
                        'id': est[0], 
                        'nome': est[1], 
                        'imagem_url': est[2] if est[2] else '/static/img/placeholder.jpg', 
                        'tecido_id': est[3] if est[3] else None,
                        'tecido': est[4] if est[4] else None, 
                        'sexo': est[5] if est[5] else 'u'
                    } for est in estampas] if estampas else []
                except Exception as e:
                    current_app.logger.error(f"Erro ao buscar estampas: {e}")
                    filters['estampas'] = []
                
                # Buscar tecidos únicos disponíveis
                # Primeiro tenta buscar tecidos associados a produtos, depois todos os tecidos ativos
                try:
                    result = execute_query_safely("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'estampa_tecido_lnk'
                        )
                    """, fetch_mode='one')
                    tecido_lnk_exists = result[0] if result else False
                    
                    # Primeiro tentar buscar tecidos associados a produtos
                    tecidos = []
                    if tecido_lnk_exists:
                        # Buscar tecidos da tabela de relacionamento
                        tecidos = execute_query_safely("""
                            SELECT DISTINCT t.id, t.nome
                            FROM tecidos t
                            WHERE t.ativo = TRUE
                            AND EXISTS (
                                SELECT 1 FROM estampa_tecido_lnk etl
                                JOIN estampa e ON etl.estampa_id = e.id
                                JOIN produtos_estampa_lnk pe ON e.id = pe.estampa_id
                                JOIN produtos p ON pe.produto_id = p.id
                                WHERE etl.tecido_id = t.id
                                AND e.ativo = TRUE AND p.ativo = TRUE
                            )
                            ORDER BY t.nome
                        """, fetch_mode='all')
                    
                    # Se não encontrou tecidos associados a produtos, buscar todos os tecidos ativos
                    if not tecidos or len(tecidos) == 0:
                        tecidos = execute_query_safely("""
                            SELECT id, nome
                            FROM tecidos
                            WHERE ativo = TRUE
                            ORDER BY nome
                        """, fetch_mode='all')
                    
                    # Quando a tabela tecidos existe, usar o ID como value para filtragem
                    filters['tecidos'] = [{'id': tec[0], 'value': str(tec[0]), 'label': tec[1]} for tec in tecidos if tec and len(tec) >= 2 and tec[1]] if tecidos else []
                except Exception as e:
                    current_app.logger.error(f"Erro ao buscar tecidos: {e}")
                    filters['tecidos'] = []
            else:
                # Fallback: usar campo tecido VARCHAR se a tabela não existir
                try:
                    estampas = execute_query_safely("""
                        SELECT DISTINCT e.id, e.nome, e.imagem_url, e.tecido, e.sexo, COALESCE(e.ordem_exibicao, 999) as ordem
                        FROM estampa e
                        JOIN produtos_estampa_lnk pe ON e.id = pe.estampa_id
                        JOIN produtos p ON pe.produto_id = p.id
                        WHERE e.ativo = TRUE AND p.ativo = TRUE
                        ORDER BY ordem, e.nome
                    """, fetch_mode='all')
                    filters['estampas'] = [{
                        'id': est[0], 
                        'nome': est[1], 
                        'imagem_url': est[2] if est[2] else '/static/img/placeholder.jpg', 
                        'tecido_id': None,
                        'tecido': est[3] if est[3] else None, 
                        'sexo': est[4] if est[4] else 'u'
                    } for est in estampas] if estampas else []
                except Exception as e:
                    current_app.logger.error(f"Erro ao buscar estampas (fallback): {e}")
                    filters['estampas'] = []
                
                # Buscar tecidos únicos (campo VARCHAR)
                try:
                    tecidos = execute_query_safely("""
                        SELECT DISTINCT e.tecido
                        FROM estampa e
                        JOIN produtos_estampa_lnk pe ON e.id = pe.estampa_id
                        JOIN produtos p ON pe.produto_id = p.id
                        WHERE e.ativo = TRUE AND p.ativo = TRUE AND e.tecido IS NOT NULL AND e.tecido != ''
                        ORDER BY e.tecido
                    """, fetch_mode='all')
                    filters['tecidos'] = [{'id': None, 'value': tec[0], 'label': tec[0]} for tec in tecidos if tec[0]] if tecidos else []
                except Exception as e:
                    current_app.logger.error(f"Erro ao buscar tecidos (VARCHAR): {e}")
                    filters['tecidos'] = []
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar estampas: {e}", exc_info=True)
            filters['estampas'] = []
            filters['tecidos'] = []
        
        return jsonify(filters), 200
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        try:
            current_app.logger.error(f"Erro ao carregar filtros: {error_msg}")
        except:
            print(f"Erro ao carregar filtros: {error_msg}")
        return jsonify({"erro": f"Erro ao carregar filtros: {error_msg}"}), 500
    finally:
        pass

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
        tecidos = request.args.getlist('tecido', type=str)
        sexos = request.args.getlist('sexo', type=str)
        preco_min = request.args.get('preco_min', type=float)
        preco_max = request.args.get('preco_max', type=float)
        
        # Construir query base
        # Usa LEFT JOIN para permitir produtos sem categoria (categoria_id NULL ou categoria deletada)
        query = """
            SELECT DISTINCT
                np.id AS nome_produto_id,
                np.nome AS nome_produto,
                np.descricao AS descricao_produto,
                COALESCE(c.nome, 'Sem categoria') AS categoria_nome,
                c.id AS categoria_id,
                (SELECT ip.url FROM produtos p_var
                 JOIN produtos_nome_produto_lnk pnp_var ON p_var.id = pnp_var.produto_id
                 JOIN imagens_produto_produto_lnk ipl ON p_var.id = ipl.produto_id
                 JOIN imagens_produto ip ON ipl.imagem_produto_id = ip.id
                 WHERE pnp_var.nome_produto_id = np.id
                 ORDER BY COALESCE(ipl.imagem_produto_ord, ip.ordem, 0) ASC
                 LIMIT 1) AS imagem_representativa_url,
                (SELECT MIN(COALESCE(p_var.preco_promocional, p_var.preco_venda)) FROM produtos p_var JOIN produtos_nome_produto_lnk pnp_var ON p_var.id = pnp_var.produto_id WHERE pnp_var.nome_produto_id = np.id AND p_var.ativo = TRUE) AS preco_minimo,
                (SELECT MIN(p_var.preco_venda) FROM produtos p_var JOIN produtos_nome_produto_lnk pnp_var ON p_var.id = pnp_var.produto_id WHERE pnp_var.nome_produto_id = np.id AND p_var.ativo = TRUE) AS preco_minimo_original,
                (SELECT COUNT(*) FROM produtos p_var JOIN produtos_nome_produto_lnk pnp_var ON p_var.id = pnp_var.produto_id WHERE pnp_var.nome_produto_id = np.id AND p_var.ativo = TRUE) AS variacoes_em_estoque_count
            FROM nome_produto np
            LEFT JOIN nome_produto_categoria_lnk npc ON np.id = npc.nome_produto_id
            LEFT JOIN categorias c ON npc.categoria_id = c.id
            WHERE np.ativo = TRUE
        """
        
        params = []
        conditions = []
        
        # Aplicar filtros
        if categoria_ids:
            conditions.append(f"c.id = ANY(%s)")
            params.append(categoria_ids)
        
        # Verificar se tabela tecidos existe (uma vez, antes dos filtros)
        # Reutilizar a verificação já feita em get_store_filters se possível
        # Mas como estamos em uma função diferente, vamos verificar novamente
        tecidos_table_exists = False
        try:
            cur_tec_check = conn.cursor()
            try:
                cur_tec_check.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'tecidos'
                    )
                """)
                result = cur_tec_check.fetchone()
                if result:
                    tecidos_table_exists = result[0]
            finally:
                cur_tec_check.close()
        except Exception as e:
            current_app.logger.warning(f"Erro ao verificar existência da tabela tecidos: {e}")
            tecidos_table_exists = False
        
        # Construir condições para filtros de variações (produtos)
        variation_conditions = []
        variation_params = []
        
        if tamanho_ids:
            variation_conditions.append("EXISTS (SELECT 1 FROM produtos_tamanho_lnk pt WHERE pt.produto_id = p.id AND pt.tamanho_id = ANY(%s))")
            variation_params.append(tamanho_ids)
        
        if estampa_ids:
            variation_conditions.append("EXISTS (SELECT 1 FROM produtos_estampa_lnk pe WHERE pe.produto_id = p.id AND pe.estampa_id = ANY(%s))")
            variation_params.append(estampa_ids)
        
        # Filtros de tecido e sexo (via estampa)
        if tecidos:
            if tecidos_table_exists:
                # Usar tecido_id se a tabela existir
                # Converter strings para inteiros se necessário
                tecido_ids = []
                tecido_nomes = []
                
                for t in tecidos:
                    try:
                        if isinstance(t, str):
                            # Tentar converter para int
                            if t.isdigit():
                                tecido_ids.append(int(t))
                            else:
                                # Se não for dígito, guardar para buscar pelo nome depois
                                tecido_nomes.append(t)
                        elif isinstance(t, int):
                            tecido_ids.append(t)
                    except Exception as e:
                        current_app.logger.warning(f"Erro ao processar filtro de tecido {t}: {e}")
                        continue
                
                # Buscar IDs dos tecidos por nome se necessário
                if tecido_nomes:
                    cur_tec_ids = conn.cursor()
                    try:
                        placeholders_nomes = ','.join(['%s'] * len(tecido_nomes))
                        cur_tec_ids.execute(f"SELECT id FROM tecidos WHERE nome IN ({placeholders_nomes}) AND ativo = TRUE", tecido_nomes)
                        ids_por_nome = [row[0] for row in cur_tec_ids.fetchall()]
                        tecido_ids.extend(ids_por_nome)
                    finally:
                        cur_tec_ids.close()
                
                # Remover duplicatas
                tecido_ids = list(set(tecido_ids))
                
                if tecido_ids:
                    # Usar IN ao invés de ANY para melhor compatibilidade
                    placeholders = ','.join(['%s'] * len(tecido_ids))
                    variation_conditions.append(f"EXISTS (SELECT 1 FROM produtos_estampa_lnk pe JOIN estampa e ON pe.estampa_id = e.id JOIN estampa_tecido_lnk etl ON e.id = etl.estampa_id WHERE pe.produto_id = p.id AND etl.tecido_id IN ({placeholders}))")
                    variation_params.extend(tecido_ids)
            else:
                # Fallback: usar campo tecido VARCHAR (se existir)
                # Verificar se a coluna tecido existe
                try:
                    cur_tec_col = conn.cursor()
                    try:
                        cur_tec_col.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_name = 'estampa' 
                                AND column_name = 'tecido'
                            )
                        """)
                        result = cur_tec_col.fetchone()
                        tecido_column_exists = result[0] if result else False
                        if tecido_column_exists:
                            variation_conditions.append("EXISTS (SELECT 1 FROM produtos_estampa_lnk pe JOIN estampa e ON pe.estampa_id = e.id WHERE pe.produto_id = p.id AND e.tecido = ANY(%s))")
                            variation_params.append(tecidos)
                    finally:
                        cur_tec_col.close()
                except:
                    # Se não conseguir verificar, simplesmente ignorar o filtro de tecido
                    pass
        
        if sexos:
            variation_conditions.append("EXISTS (SELECT 1 FROM produtos_estampa_lnk pe JOIN estampa e ON pe.estampa_id = e.id WHERE pe.produto_id = p.id AND e.sexo = ANY(%s))")
            variation_params.append(sexos)
        
        if preco_min is not None:
            # Filtrar pelo menor preço (promocional ou venda)
            variation_conditions.append("COALESCE(p.preco_promocional, p.preco_venda) >= %s")
            variation_params.append(preco_min)
        
        if preco_max is not None:
            # Filtrar pelo menor preço (promocional ou venda)
            variation_conditions.append("COALESCE(p.preco_promocional, p.preco_venda) <= %s")
            variation_params.append(preco_max)
        
        # Se houver filtros de variação, adicionar subquery
        if variation_conditions:
            # Garantir que há produtos ativos
            variation_conditions.append("p.ativo = TRUE")
            
            # Construir a subquery com placeholders
            subquery = "EXISTS (SELECT 1 FROM produtos p JOIN produtos_nome_produto_lnk pnp ON p.id = pnp.produto_id WHERE pnp.nome_produto_id = np.id AND " + \
                      " AND ".join(variation_conditions) + ")"
            conditions.append(subquery)
            params.extend(variation_params)
        else:
            # Se não houver filtros de variação, mostrar produtos ativos
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM produtos p
                    JOIN produtos_nome_produto_lnk pnp ON p.id = pnp.produto_id
                    WHERE pnp.nome_produto_id = np.id
                    AND p.ativo = TRUE
                )
            """)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY np.nome"
        
        cur.execute(query, params)
        products_db = cur.fetchall()

        for prod in products_db:
            preco_minimo = float(prod[6]) if prod[6] is not None else None
            preco_minimo_original = float(prod[7]) if prod[7] is not None else None
            variacoes_em_estoque = prod[8] if prod[8] is not None else 0
            
            # Verificar se tem promoção (preço mínimo é menor que original)
            tem_promocao = preco_minimo is not None and preco_minimo_original is not None and preco_minimo < preco_minimo_original
            preco_original_para_exibir = preco_minimo_original if preco_minimo_original else preco_minimo
            
            base_products_list.append({
                'id': prod[0],
                'nome': prod[1],
                'descricao': prod[2],
                'categoria': prod[3] if prod[3] else 'Sem categoria',
                'categoria_id': prod[4] if prod[4] else None,
                'imagem_url': prod[5] if prod[5] else '/static/img/placeholder.jpg',
                'preco_minimo': preco_minimo,
                'preco_minimo_original': preco_original_para_exibir,
                'tem_promocao': tem_promocao,
                'estoque': variacoes_em_estoque
            })

        return jsonify(base_products_list), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor ao carregar produtos base."}), 500
    finally:
        if cur:
            cur.close()