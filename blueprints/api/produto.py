from . import api_bp
from flask import jsonify
from ..services import get_db

@api_bp.route('/base_products/<int:nome_produto_id>', methods=['GET'])
def get_product_details(nome_produto_id):
    """Endpoint para obter detalhes de um produto base específico (para a página de detalhes do produto)."""
    conn = get_db() # Obtém uma conexão do pool
    cur = conn.cursor()
    try:
        # 1. Busca os detalhes do produto base (nome_produto)
        cur.execute("""
            SELECT np.id, np.nome, np.descricao, c.nome AS categoria_nome
            FROM nome_produto np
            JOIN categorias c ON np.categoria_id = c.id
            WHERE np.id = %s;
        """, (nome_produto_id,))
        base_product_data = cur.fetchone()

        if not base_product_data:
            # Se o produto base não for encontrado, retorna 404
            return jsonify({"erro": "Produto não encontrado."}), 404

        product_details = {
            'id': base_product_data[0],
            'nome': base_product_data[1],
            'descricao': base_product_data[2],
            'categoria': base_product_data[3],
            'variations': [] # Aqui serão adicionadas todas as variações
        }

        # 2. Busca TODAS as variações (tabela 'produtos') associadas a este nome_produto_id
        # Inclui estampa, tamanho, preço, estoque, SKU e TODAS as imagens por variação.
        cur.execute("""
            SELECT
                p.id AS variation_id,
                e.id AS estampa_id,
                e.nome AS estampa_nome,
                e.imagem_url AS estampa_imagem_url, -- Imagem da estampa em si
                t.id AS tamanho_id,
                t.nome AS tamanho_nome,
                p.preco_venda,
                p.preco_promocional,
                p.estoque,
                p.codigo_sku,
                -- Agrega as imagens de CADA VARIAÇÃO em um array JSON (Recurso do PostgreSQL)
                ARRAY_AGG(JSON_BUILD_OBJECT('id', ip.id, 'url', ip.url, 'ordem', ip.ordem, 'descricao', ip.descricao, 'is_thumbnail', ip.is_thumbnail) ORDER BY ip.ordem) FILTER (WHERE ip.id IS NOT NULL) AS images_json
            FROM produtos p
            JOIN estampa e ON p.estampa_id = e.id
            JOIN tamanho t ON p.tamanho_id = t.id
            LEFT JOIN imagens_produto ip ON p.id = ip.produto_id -- LEFT JOIN para incluir variações sem imagem
            WHERE p.nome_produto_id = %s
            GROUP BY p.id, e.id, t.id, p.preco_venda, p.preco_promocional, p.estoque, p.codigo_sku -- Agrupa por variação para que ARRAY_AGG funcione
            ORDER BY estampa_nome, tamanho_nome; -- Ordena para consistência
        """, (nome_produto_id,))
        variations_data = cur.fetchall()

        # 3. Formata os dados das variações
        for var in variations_data:
            # Pega as imagens agregadas (o elemento var[10] da tupla)
            images = var[10] if var[10] and var[10][0] is not None else []
            preco_venda = float(var[6])
            preco_promocional = float(var[7]) if var[7] is not None else None
            
            # Determina o preço final (promocional se existir, senão preço de venda)
            preco_final = preco_promocional if preco_promocional is not None else preco_venda
            
            product_details['variations'].append({
                'id': var[0], # ID da variação específica de 'produtos'
                'estampa': {'id': var[1], 'nome': var[2], 'imagem_url': var[3]},
                'tamanho': {'id': var[4], 'nome': var[5]},
                'preco': preco_final,
                'preco_original': preco_venda,
                'preco_promocional': preco_promocional,
                'tem_promocao': preco_promocional is not None,
                'estoque': var[8],
                'sku': var[9],
                'images': images # Array de URLs de todas as imagens para esta variação
            })
        
        # Retorna os detalhes completos do produto base e suas variações
        return jsonify(product_details), 200

    except Exception as e:
        print(f"Error fetching product details: {e}")
        return jsonify({"erro": "Erro interno do servidor ao carregar detalhes do produto."}), 500
    finally:
        if cur: cur.close() # Fecha o cursor, a conexão é retornada ao pool pelo teardown