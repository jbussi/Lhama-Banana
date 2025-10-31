from . import api_bp
from flask import jsonify
from ..services import get_db

@api_bp.route('/base_products', methods=['GET'])
def get_base_products():
    """Endpoint para listar produtos base (para a página da loja)."""
    base_products_list = []
    conn = get_db()  # Obtém a conexão do pool
    cur = conn.cursor()

    cur = conn.cursor()
    try:
        # A consulta agora inclui produtos fora de estoque
        # e conta variações em estoque para determinar a disponibilidade.
        query = """
            SELECT
                np.id AS nome_produto_id,
                np.nome AS nome_produto,
                np.descricao AS descricao_produto,
                c.nome AS categoria_nome,
                -- Subquery para selecionar a URL da imagem principal da primeira variação encontrada
                (SELECT ip.url FROM produtos p_var
                 JOIN imagens_produto ip ON p_var.id = ip.produto_id
                 WHERE p_var.nome_produto_id = np.id
                 ORDER BY ip.ordem ASC
                 LIMIT 1) AS imagem_representativa_url,
                -- Subquery para selecionar o menor preço de venda entre todas as variações (mesmo as sem estoque)
                (SELECT MIN(p_var.preco_venda) FROM produtos p_var WHERE p_var.nome_produto_id = np.id) AS preco_minimo,
                -- Conta quantas variações estão em estoque (estoque > 0) para determinar o status
                (SELECT COUNT(*) FROM produtos p_var WHERE p_var.nome_produto_id = np.id AND p_var.estoque > 0) AS variacoes_em_estoque_count
            FROM nome_produto np
            JOIN categorias c ON np.categoria_id = c.id
            ORDER BY np.id;
        """
        cur.execute(query)
        products_db = cur.fetchall()

        for prod in products_db:

            base_products_list.append({
                'id': prod[0],
                'nome': prod[1],
                'descricao': prod[2],
                'categoria': prod[3],
                'imagem_url': prod[4] if prod[4] else '/static/img/placeholder.jpg', # Placeholder se não houver imagem
                'preco_minimo': float(prod[5]) if prod[5] is not None else None, # Retorna None se não houver variações
                'estoque': prod[6] # unidades em estoque
            })

        return jsonify(base_products_list), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor ao carregar produtos base."}), 500
    finally:
        cur.close()
        conn.close()