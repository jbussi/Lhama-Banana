from . import api_bp
from flask import jsonify, request, g
from ..services import get_db, get_cart_owner_info, get_or_create_cart, login_required_and_load_user, execute_query_safely, execute_write_safely


@api_bp.route('/cart', methods=['GET'])
def view_cart():
    """Visualiza o conteúdo atual do carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    cart_items_list = []
    total_cart_value = 0.0

    try:
        # Obtém o ID do carrinho no DB
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: # Isso pode acontecer se get_or_create_cart falhar por algum motivo interno
            return jsonify({"erro": "Não foi possível identificar/criar o carrinho."}), 500

        # Buscar itens do carrinho usando execute_query_safely
        query = """
            SELECT
                ci.id AS cart_item_id, ci.quantidade, ci.preco_unitario_no_momento,
                p.id AS product_variation_id, p.codigo_sku,
                np.nome AS product_name, np.descricao AS product_description,
                e.nome AS estampa_nome, t.nome AS tamanho_nome,
                (SELECT ip.url FROM imagens_produto_produto_lnk ipl JOIN imagens_produto ip ON ipl.imagem_produto_id = ip.id WHERE ipl.produto_id = p.id ORDER BY COALESCE(ipl.imagem_produto_ord, ip.ordem, 0) ASC LIMIT 1) AS image_url
            FROM carrinho_itens ci
            JOIN produtos p ON ci.produto_id = p.id
            LEFT JOIN produtos_nome_produto_lnk pnp ON p.id = pnp.produto_id
            LEFT JOIN nome_produto np ON pnp.nome_produto_id = np.id
            LEFT JOIN produtos_estampa_lnk pe ON p.id = pe.produto_id
            LEFT JOIN estampa e ON pe.estampa_id = e.id
            LEFT JOIN produtos_tamanho_lnk pt ON p.id = pt.produto_id
            LEFT JOIN tamanho t ON pt.tamanho_id = t.id
            WHERE ci.carrinho_id = %s
            ORDER BY ci.id ASC;
        """
        items_db = execute_query_safely(query, (cart_id,), fetch_mode='all')
        if not items_db:
            items_db = []

        for item in items_db:
            item_total = item[1] * float(item[2])
            total_cart_value += item_total
            cart_items_list.append({
                'cart_item_id': item[0], 'quantity': item[1], 'price_at_time_of_add': float(item[2]),
                'product_variation_id': item[3], 'sku': item[4], 'product_name': item[5],
                'product_description': item[6], 'estampa_name': item[7], 'tamanho_name': item[8],
                'image_url': item[9] if item[9] else '/static/img/placeholder.jpg', 'item_total': item_total
            })

        return jsonify({"items": cart_items_list, "total_value": total_cart_value}), 200

    except Exception as e:
        print(f"Erro ao visualizar carrinho: {e}")
        return jsonify({"erro": "Erro interno ao visualizar carrinho."}), 500

@api_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Adiciona um item ao carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    data = request.get_json()
    product_variation_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    if not product_variation_id or not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"erro": "Dados inválidos: ID do produto e quantidade são obrigatórios e válidos."}), 400

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id:
            return jsonify({"erro": "Não foi possível obter ou criar carrinho."}), 500

        # Buscar informações do produto usando execute_query_safely
        product_info = execute_query_safely(
            "SELECT preco_venda, preco_promocional, estoque FROM produtos WHERE id = %s", 
            (product_variation_id,), 
            fetch_mode='one'
        )
        if not product_info:
            return jsonify({"erro": "Variação do produto não encontrada."}), 404
        # Usar preço promocional se existir, senão usar preço de venda
        preco_venda = product_info[0]
        preco_promocional = product_info[1]
        current_price = preco_promocional if preco_promocional else preco_venda
        current_stock = product_info[2]

        # Buscar item existente no carrinho
        cart_item = execute_query_safely(
            "SELECT id, quantidade FROM carrinho_itens WHERE carrinho_id = %s AND produto_id = %s", 
            (cart_id, product_variation_id), 
            fetch_mode='one'
        )

        if cart_item:
            # Item já existe no carrinho, somar quantidades
            new_quantity = cart_item[1] + quantity
            if new_quantity > current_stock:
                available = current_stock - cart_item[1]
                if available <= 0:
                    return jsonify({"erro": f"Você já possui {cart_item[1]} unidades no carrinho. Estoque total: {current_stock}."}), 400
                return jsonify({"erro": f"Adicionar mais itens excederia o estoque. Você já tem {cart_item[1]} no carrinho. Pode adicionar mais {available}."}), 400
            execute_write_safely(
                "UPDATE carrinho_itens SET quantidade = %s, adicionado_em = NOW() WHERE id = %s", 
                (new_quantity, cart_item[0]), 
                commit=True
            )
        else:
            # Novo item no carrinho
            if quantity > current_stock:
                 return jsonify({"erro": f"Quantidade solicitada ({quantity}) excede o estoque disponível ({current_stock})."}), 400
            execute_write_safely(
                "INSERT INTO carrinho_itens (carrinho_id, produto_id, quantidade, preco_unitario_no_momento) VALUES (%s, %s, %s, %s)",
                (cart_id, product_variation_id, quantity, current_price),
                commit=True
            )
        
        return jsonify({"mensagem": "Item adicionado ao carrinho com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao adicionar item ao carrinho: {e}")
        return jsonify({"erro": "Erro interno ao adicionar item ao carrinho."}), 500

@api_bp.route('/cart/update/<int:cart_item_id>', methods=['PUT'])
# @login_required_and_load_user
def update_cart_item_quantity(cart_item_id):
    """Atualiza a quantidade de um item específico no carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    data = request.get_json()
    new_quantity = data.get('quantity')
    if not isinstance(new_quantity, int) or new_quantity < 0:
        return jsonify({"erro": "Quantidade inválida."}), 400

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: return jsonify({"erro": "Carrinho não encontrado."}), 500

        item_info = execute_query_safely("""
            SELECT ci.produto_id, p.estoque
            FROM carrinho_itens ci
            JOIN produtos p ON ci.produto_id = p.id
            WHERE ci.id = %s AND ci.carrinho_id = %s
        """, (cart_item_id, cart_id), fetch_mode='one')
        if not item_info: return jsonify({"erro": "Item do carrinho não encontrado ou não pertence a este carrinho."}), 404

        product_variation_id, current_stock = item_info

        if new_quantity > current_stock:
            return jsonify({"erro": f"A quantidade solicitada ({new_quantity}) excede o estoque disponível ({current_stock})."}), 400

        if new_quantity == 0:
            execute_write_safely("DELETE FROM carrinho_itens WHERE id = %s", (cart_item_id,), commit=True)
        else:
            execute_write_safely(
                "UPDATE carrinho_itens SET quantidade = %s, adicionado_em = NOW() WHERE id = %s", 
                (new_quantity, cart_item_id), 
                commit=True
            )
        
        return jsonify({"mensagem": "Carrinho atualizado com sucesso!"}), 200
    except Exception as e:
        print(f"Erro ao atualizar item do carrinho: {e}")
        return jsonify({"erro": "Erro interno ao atualizar carrinho."}), 500

@api_bp.route('/cart/remove/<int:cart_item_id>', methods=['DELETE'])
# @login_required_and_load_user
def remove_from_cart(cart_item_id):
    """Remove um item específico do carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: return jsonify({"erro": "Carrinho não encontrado."}), 500

        rowcount = execute_write_safely(
            "DELETE FROM carrinho_itens WHERE id = %s AND carrinho_id = %s", 
            (cart_item_id, cart_id), 
            commit=True
        )
        if not rowcount or rowcount == 0:
            return jsonify({"erro": "Item do carrinho não encontrado ou não pertence a este carrinho."}), 404
        return jsonify({"mensagem": "Item removido do carrinho com sucesso!"}), 200
    except Exception as e:
        print(f"Erro ao remover item do carrinho: {e}")
        return jsonify({"erro": "Erro interno ao remover item do carrinho."}), 500

@api_bp.route('/cart/clear', methods=['DELETE'])
# @login_required_and_load_user
def clear_cart():
    """Limpa todos os itens do carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: return jsonify({"mensagem": "Carrinho já está vazio ou não encontrado."}), 200

        execute_write_safely("DELETE FROM carrinho_itens WHERE carrinho_id = %s", (cart_id,), commit=True)
        return jsonify({"mensagem": "Carrinho limpo com sucesso!"}), 200
    except Exception as e:
        print(f"Erro ao limpar carrinho: {e}")
        return jsonify({"erro": "Erro interno ao limpar carrinho."}), 500

# --- Endpoint para Mesclar Carrinhos (Chamado no login) ---
@api_bp.route('/cart/merge', methods=['POST'])
@login_required_and_load_user # APENAS PARA USUÁRIOS LOGADOS
def merge_carts():
    """Mescla um carrinho anônimo com o carrinho do usuário logado."""
    user_id = g.user_db_data['id']
    data = request.get_json()
    anonymous_session_id = data.get('anonymous_session_id')

    if not anonymous_session_id:
        return jsonify({"erro": "ID de sessão anônima ausente."}), 400

    try:
        # Obter o ID do carrinho anônimo
        anon_cart_id_res = execute_query_safely(
            "SELECT id FROM carrinhos WHERE session_id = %s", 
            (anonymous_session_id,), 
            fetch_mode='one'
        )
        
        if not anon_cart_id_res:
            return jsonify({"mensagem": "Nenhum carrinho anônimo para mesclar."}), 200 # Nada a fazer

        anon_cart_id = anon_cart_id_res[0]

        # Obter o ID do carrinho do usuário logado (cria se não existir)
        user_cart_id = get_or_create_cart(user_id=user_id) # Reutiliza a lógica para obter/criar

        # Mover itens do carrinho anônimo para o carrinho do usuário
        # Lógica para lidar com itens duplicados: somar quantidades (ON CONFLICT)
        execute_write_safely("""
            INSERT INTO carrinho_itens (carrinho_id, produto_id, quantidade, preco_unitario_no_momento, adicionado_em)
            SELECT %s, produto_id, quantidade, preco_unitario_no_momento, adicionado_em
            FROM carrinho_itens
            WHERE carrinho_id = %s
            ON CONFLICT (carrinho_id, produto_id) DO UPDATE SET
                quantidade = carrinho_itens.quantidade + EXCLUDED.quantidade,
                adicionado_em = NOW();
        """, (user_cart_id, anon_cart_id), commit=True)
        
        # Deletar o carrinho anônimo após a mesclagem
        execute_write_safely("DELETE FROM carrinhos WHERE id = %s", (anon_cart_id,), commit=True)

        return jsonify({"mensagem": "Carrinhos mesclados com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao mesclar carrinhos: {e}")
        return jsonify({"erro": "Erro interno ao mesclar carrinhos."}), 500