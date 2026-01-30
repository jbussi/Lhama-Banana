from . import api_bp
from flask import jsonify, current_app
from ..services import get_db, execute_query_safely
import traceback

@api_bp.route('/base_products/<int:nome_produto_id>', methods=['GET'])
def get_product_details(nome_produto_id):
    """Endpoint para obter detalhes de um produto base específico (para a página de detalhes do produto)."""
    try:
        # 1. Busca os detalhes do produto base (nome_produto)
        # Usa LEFT JOIN para permitir produtos sem categoria (categoria_id NULL ou categoria deletada)
        base_product_data = execute_query_safely("""
            SELECT np.id, np.nome, np.descricao, COALESCE(c.nome, 'Sem categoria') AS categoria_nome
            FROM nome_produto np
            LEFT JOIN nome_produto_categoria_lnk npc ON np.id = npc.nome_produto_id
            LEFT JOIN categorias c ON npc.categoria_id = c.id
            WHERE np.id = %s;
        """, (nome_produto_id,), fetch_mode='one')

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
        variations_data = execute_query_safely("""
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
                ARRAY_AGG(JSON_BUILD_OBJECT('id', ip.id, 'url', ip.url, 'ordem', COALESCE(ipl.imagem_produto_ord, ip.ordem, 0), 'descricao', ip.descricao, 'is_thumbnail', ip.is_thumbnail) ORDER BY COALESCE(ipl.imagem_produto_ord, ip.ordem, 0)) FILTER (WHERE ip.id IS NOT NULL) AS images_json
            FROM produtos p
            LEFT JOIN produtos_estampa_lnk pe ON p.id = pe.produto_id
            LEFT JOIN estampa e ON pe.estampa_id = e.id
            LEFT JOIN produtos_tamanho_lnk pt ON p.id = pt.produto_id
            LEFT JOIN tamanho t ON pt.tamanho_id = t.id
            LEFT JOIN imagens_produto_produto_lnk ipl ON p.id = ipl.produto_id -- LEFT JOIN para incluir variações sem imagem
            LEFT JOIN imagens_produto ip ON ipl.imagem_produto_id = ip.id
            LEFT JOIN produtos_nome_produto_lnk pnp ON p.id = pnp.produto_id
            WHERE pnp.nome_produto_id = %s
            GROUP BY p.id, e.id, t.id, p.preco_venda, p.preco_promocional, p.estoque, p.codigo_sku -- Agrupa por variação para que ARRAY_AGG funcione
            ORDER BY estampa_nome, tamanho_nome; -- Ordena para consistência
        """, (nome_produto_id,), fetch_mode='all')
        if not variations_data:
            variations_data = []

        # 3. Formata os dados das variações
        # Índices da tupla: 0=variation_id, 1=estampa_id, 2=estampa_nome, 3=estampa_imagem_url,
        #                  4=tamanho_id, 5=tamanho_nome, 6=preco_venda, 7=preco_promocional,
        #                  8=estoque, 9=codigo_sku, 10=images_json
        for var in variations_data:
            # Pega as imagens agregadas (índice 10 da tupla)
            # var[10] é um array PostgreSQL que pode ser None ou um array vazio
            images = []
            if var[10] is not None:
                # Se for um array PostgreSQL, converter para lista Python
                if isinstance(var[10], list):
                    images = var[10]
                elif isinstance(var[10], (tuple, set)):
                    images = list(var[10])
                else:
                    # Se for um tipo desconhecido, tentar converter
                    try:
                        images = list(var[10]) if var[10] else []
                    except:
                        images = []
            
            preco_venda = float(var[6]) if var[6] is not None else 0.0
            preco_promocional = float(var[7]) if var[7] is not None else None
            
            # Preço final: usa promocional se existir, senão usa venda
            preco_final = preco_promocional if preco_promocional else preco_venda
            tem_promocao = preco_promocional is not None and preco_promocional < preco_venda
            
            product_details['variations'].append({
                'id': var[0], # ID da variação específica de 'produtos'
                'estampa': {'id': var[1], 'nome': var[2], 'imagem_url': var[3]},
                'tamanho': {'id': var[4], 'nome': var[5]},
                'preco': preco_final,
                'preco_original': preco_venda,
                'preco_promocional': preco_promocional,
                'tem_promocao': tem_promocao,
                'estoque': var[8] if var[8] is not None else 0,
                'sku': var[9] if var[9] is not None else '',
                'images': images # Array de URLs de todas as imagens para esta variação
            })
        
        # Retorna os detalhes completos do produto base e suas variações
        return jsonify(product_details), 200

    except Exception as e:
        # Log detalhado do erro para debug
        error_msg = str(e)
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Error fetching product details for nome_produto_id {nome_produto_id}: {error_msg}")
        current_app.logger.error(f"Traceback: {error_trace}")
        print(f"Error fetching product details: {e}")
        print(traceback.format_exc())
        return jsonify({
            "erro": "Erro interno do servidor ao carregar detalhes do produto.",
            "detalhes": error_msg if current_app.config.get('DEBUG') else None
        }), 500