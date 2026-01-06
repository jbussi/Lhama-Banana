from . import api_bp
from flask import jsonify, request, g
from ..services import get_db, get_cart_owner_info, get_or_create_cart, login_required_and_load_user


@api_bp.route('/cart', methods=['GET'])
def view_cart():
    """Visualiza o conteúdo atual do carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    conn = get_db()
    cur = conn.cursor()
    cart_items_list = []
    total_cart_value = 0.0

    try:
        # Obtém o ID do carrinho no DB
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: # Isso pode acontecer se get_or_create_cart falhar por algum motivo interno
            return jsonify({"erro": "Não foi possível identificar/criar o carrinho."}), 500

        # ... (restante da sua consulta SELECT e processamento para listar itens do carrinho) ...
        # (O código que já te dei para esta rota está bom, apenas se certifique de que usa `cart_id`)
        query = """
            SELECT
                ci.id AS cart_item_id, ci.quantidade, ci.preco_unitario_no_momento,
                p.id AS product_variation_id, p.codigo_sku,
                np.nome AS product_name, np.descricao AS product_description,
                e.nome AS estampa_nome, t.nome AS tamanho_nome,
                (SELECT ip.url FROM imagens_produto ip WHERE ip.produto_id = p.id ORDER BY ip.ordem ASC LIMIT 1) AS image_url
            FROM carrinho_itens ci
            JOIN produtos p ON ci.produto_id = p.id
            JOIN nome_produto np ON p.nome_produto_id = np.id
            JOIN estampa e ON p.estampa_id = e.id
            JOIN tamanho t ON p.tamanho_id = t.id
            WHERE ci.carrinho_id = %s
            ORDER BY ci.id ASC;
        """
        cur.execute(query, (cart_id,))
        items_db = cur.fetchall()

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
    finally:
        if cur: cur.close()

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

    conn = get_db()
    cur = conn.cursor()

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id:
            return jsonify({"erro": "Não foi possível obter ou criar carrinho."}), 500

        # ... (restante da lógica de verificação de estoque, inserção/atualização do item no carrinho) ...
        cur.execute("SELECT preco_venda, estoque FROM produtos WHERE id = %s", (product_variation_id,))
        product_info = cur.fetchone()
        if not product_info:
            return jsonify({"erro": "Variação do produto não encontrada."}), 404
        current_price = product_info[0]
        current_stock = product_info[1]

        cur.execute("SELECT id, quantidade FROM carrinho_itens WHERE carrinho_id = %s AND produto_id = %s", (cart_id, product_variation_id))
        cart_item = cur.fetchone()

        if cart_item:
            # Item já existe no carrinho, somar quantidades
            new_quantity = cart_item[1] + quantity
            if new_quantity > current_stock:
                available = current_stock - cart_item[1]
                if available <= 0:
                    return jsonify({"erro": f"Você já possui {cart_item[1]} unidades no carrinho. Estoque total: {current_stock}."}), 400
                return jsonify({"erro": f"Adicionar mais itens excederia o estoque. Você já tem {cart_item[1]} no carrinho. Pode adicionar mais {available}."}), 400
            cur.execute("UPDATE carrinho_itens SET quantidade = %s, adicionado_em = NOW() WHERE id = %s", (new_quantity, cart_item[0]))
        else:
            # Novo item no carrinho
            if quantity > current_stock:
                 return jsonify({"erro": f"Quantidade solicitada ({quantity}) excede o estoque disponível ({current_stock})."}), 400
            cur.execute("INSERT INTO carrinho_itens (carrinho_id, produto_id, quantidade, preco_unitario_no_momento) VALUES (%s, %s, %s, %s)",
                        (cart_id, product_variation_id, quantity, current_price))
        
        conn.commit()
        return jsonify({"mensagem": "Item adicionado ao carrinho com sucesso!"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Erro ao adicionar item ao carrinho: {e}")
        return jsonify({"erro": "Erro interno ao adicionar item ao carrinho."}), 500
    finally:
        if cur: cur.close()

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

    conn = get_db()
    cur = conn.cursor()

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: return jsonify({"erro": "Carrinho não encontrado."}), 500

        cur.execute("""
            SELECT ci.produto_id, p.estoque
            FROM carrinho_itens ci
            JOIN produtos p ON ci.produto_id = p.id
            WHERE ci.id = %s AND ci.carrinho_id = %s
        """, (cart_item_id, cart_id))
        item_info = cur.fetchone()
        if not item_info: return jsonify({"erro": "Item do carrinho não encontrado ou não pertence a este carrinho."}), 404

        product_variation_id, current_stock = item_info

        if new_quantity > current_stock:
            return jsonify({"erro": f"A quantidade solicitada ({new_quantity}) excede o estoque disponível ({current_stock})."}), 400

        if new_quantity == 0:
            cur.execute("DELETE FROM carrinho_itens WHERE id = %s", (cart_item_id,))
        else:
            cur.execute("UPDATE carrinho_itens SET quantidade = %s, adicionado_em = NOW() WHERE id = %s", (new_quantity, cart_item_id))
        
        conn.commit()
        return jsonify({"mensagem": "Carrinho atualizado com sucesso!"}), 200
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar item do carrinho: {e}")
        return jsonify({"erro": "Erro interno ao atualizar carrinho."}), 500
    finally:
        if cur: cur.close()

@api_bp.route('/cart/remove/<int:cart_item_id>', methods=['DELETE'])
# @login_required_and_load_user
def remove_from_cart(cart_item_id):
    """Remove um item específico do carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    conn = get_db()
    cur = conn.cursor()

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: return jsonify({"erro": "Carrinho não encontrado."}), 500

        cur.execute("DELETE FROM carrinho_itens WHERE id = %s AND carrinho_id = %s", (cart_item_id, cart_id))
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({"erro": "Item do carrinho não encontrado ou não pertence a este carrinho."}), 404
        conn.commit()
        return jsonify({"mensagem": "Item removido do carrinho com sucesso!"}), 200
    except Exception as e:
        conn.rollback()
        print(f"Erro ao remover item do carrinho: {e}")
        return jsonify({"erro": "Erro interno ao remover item do carrinho."}), 500
    finally:
        if cur: cur.close()

@api_bp.route('/cart/clear', methods=['DELETE'])
# @login_required_and_load_user
def clear_cart():
    """Limpa todos os itens do carrinho."""
    error_response, user_id, session_id = get_cart_owner_info()
    if error_response: return error_response

    conn = get_db()
    cur = conn.cursor()

    try:
        cart_id = get_or_create_cart(user_id=user_id, session_id=session_id)
        if not cart_id: return jsonify({"mensagem": "Carrinho já está vazio ou não encontrado."}), 200

        cur.execute("DELETE FROM carrinho_itens WHERE carrinho_id = %s", (cart_id,))
        conn.commit()
        return jsonify({"mensagem": "Carrinho limpo com sucesso!"}), 200
    except Exception as e:
        conn.rollback()
        print(f"Erro ao limpar carrinho: {e}")
        return jsonify({"erro": "Erro interno ao limpar carrinho."}), 500
    finally:
        if cur: cur.close()

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

    conn = get_db()
    cur = conn.cursor()
    try:
        # Obter o ID do carrinho anônimo
        cur.execute("SELECT id FROM carrinhos WHERE session_id = %s", (anonymous_session_id,))
        anon_cart_id_res = cur.fetchone()
        
        if not anon_cart_id_res:
            return jsonify({"mensagem": "Nenhum carrinho anônimo para mesclar."}), 200 # Nada a fazer

        anon_cart_id = anon_cart_id_res[0]

        # Obter o ID do carrinho do usuário logado (cria se não existir)
        user_cart_id = get_or_create_cart(user_id=user_id) # Reutiliza a lógica para obter/criar

        # Mover itens do carrinho anônimo para o carrinho do usuário
        # Lógica para lidar com itens duplicados: somar quantidades (ON CONFLICT)
        cur.execute("""
            INSERT INTO carrinho_itens (carrinho_id, produto_id, quantidade, preco_unitario_no_momento, adicionado_em)
            SELECT %s, produto_id, quantidade, preco_unitario_no_momento, adicionado_em
            FROM carrinho_itens
            WHERE carrinho_id = %s
            ON CONFLICT (carrinho_id, produto_id) DO UPDATE SET
                quantidade = carrinho_itens.quantidade + EXCLUDED.quantidade,
                adicionado_em = NOW();
        """, (user_cart_id, anon_cart_id))
        
        # Deletar o carrinho anônimo após a mesclagem
        cur.execute("DELETE FROM carrinhos WHERE id = %s", (anon_cart_id,))

        conn.commit()
        return jsonify({"mensagem": "Carrinhos mesclados com sucesso!"}), 200

    except Exception as e:
        conn.rollback()
        print(f"Erro ao mesclar carrinhos: {e}")
        return jsonify({"erro": "Erro interno ao mesclar carrinhos."}), 500
    finally:
        if cur: cur.close()