import os
import sys
import requests
from blueprints.db import DB_config, get_db, init_db_pool, close_db_connection
from functools import wraps
from blueprints.services.user_service import get_user_by_firebase_uid, insert_new_user, update_user_profile_db, login_required_and_load_user, admin_required
from blueprints.services.cart_service import get_or_create_cart, get_cart_owner_info
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify, g
from flask_cors import CORS
import psycopg2.pool

from firebase_admin import auth, credentials, initialize_app

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app) 
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT' # Chave secreta para sessões



cred = credentials.Certificate("C:\\Users\\João Paulo Bussi\\Downloads\\LhamaBanana_visual_estatica_corrigida\\key.json")
initialize_app(cred)

# --- TOKEN PAGSEGURO (MUITO IMPORTANTE: USE VARIÁVEIS DE AMBIENTE EM PROD!) ---
# Para testes, você pode colocar aqui diretamente, mas REMOVA para produção.
PAGSEGURO_SANDBOX_API_TOKEN = os.environ.get('PAGSEGURO_SANDBOX_API_TOKEN', 'SEU_TOKEN_PAGSEGURO_AQUI')
PAGSEGURO_SANDBOX_CHECKOUT_URL = "https://sandbox.api.pagseguro.com/checkouts"

# URLs de retorno/notificação (ajuste para o seu domínio)
# Para notificações, em ambiente de desenvolvimento, você precisaria de algo como ngrok para expor seu localhost
PAGSEGURO_RETURN_URL = "http://localhost:80/pagseguro/return"
PAGSEGURO_REDIRECT_URL = "http://localhost:80/pagseguro/redirect" # Pode ser o mesmo do return_url
PAGSEGURO_NOTIFICATION_URL = "http://localhost:80/pagseguro/notification" # Deve ser um endpoint real para receber as notificações


@app.route('/loja')
def loja_page():
    """Rota da página da loja."""
    # O HTML da loja será carregado, e o JavaScript buscará os produtos via API
    return render_template('loja.html', user=session.get('uid'))

@app.route('/api/base_products', methods=['GET'])
def get_base_products():
    """Endpoint para listar produtos base (para a página da loja)."""
    base_products_list = []
    conn = get_db() # Obtém a conexão do pool
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
        print(f"Erro ao buscar produtos base: {e}")
        return jsonify({"erro": "Erro interno do servidor ao carregar produtos base."}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/perfil', methods=["GET"])
@login_required_and_load_user # Garante que o usuário está logado e g.user está populado
def perfil_page():
    return render_template('perfil.html')

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('uid', None) # Remove o ID do usuário da sessão
    return redirect(url_for('login_page'))



@app.route('/register', methods=["GET"])
def register_page():
        return render_template('register.html')


@app.route('/login', methods=["GET"])
def login_page():
    return render_template('login.html')


@app.route('/produto/<int:nome_produto_id>')
def produto_page(nome_produto_id):
    """Rota da página de detalhes do produto. O JavaScript buscará os detalhes."""
    # Este 'nome_produto_id' é o ID do produto base (da tabela nome_produto)
    # que o frontend JS usará para chamar a API.
    return render_template('produto.html', nome_produto_id=nome_produto_id, user=session.get('uid'))


@app.route('/checkout')
def checkout_page():
    conn = get_db()
    cur = conn.cursor()

    # Inicializa as variáveis para garantir que sempre existam
    cart_items = []
    cart_total_value = 0.0
    discount = 0.0 # Pode ser calculado depois
    final_total = 0.0 # Será atualizado com base nos outros

    error_response, user_db_id_for_cart, session_id_for_cart = get_cart_owner_info()
    if error_response:
        flash("Sua sessão expirou ou não há itens no carrinho. Por favor, adicione itens para prosseguir.", "warning")
        return redirect(url_for('loja_page'))

    cart_id = get_or_create_cart(user_db_id=user_db_id_for_cart, session_id=session_id_for_cart)
    if not cart_id:
        flash("Não foi possível carregar seu carrinho. Tente novamente mais tarde.", "danger")
        return redirect(url_for('loja_page'))

    try:
        cur.execute("""
            SELECT
                ci.id AS cart_item_id, ci.quantidade, ci.preco_unitario_no_momento,
                p.id AS product_variation_id, p.codigo_sku,
                np.nome AS product_name,
                e.nome AS estampa_name, t.nome AS tamanho_name,
                (SELECT ip.url FROM imagens_produto ip WHERE ip.produto_id = p.id ORDER BY ip.ordem ASC LIMIT 1) AS image_url
            FROM carrinho_itens ci
            JOIN produtos p ON ci.produto_id = p.id
            JOIN nome_produto np ON p.nome_produto_id = np.id
            JOIN estampa e ON p.estampa_id = e.id
            JOIN tamanho t ON p.tamanho_id = t.id
            WHERE ci.carrinho_id = %s
            ORDER BY ci.id ASC;
        """, (cart_id,))
        
        for row in cur.fetchall():
            item_total = row['quantidade'] * row['preco_unitario_no_momento']
            cart_items.append({
                'cart_item_id': row['cart_item_id'],
                'product_variation_id': row['product_variation_id'],
                'product_name': row['product_name'],
                'estampa_name': row['estampa_name'],
                'tamanho_name': row['tamanho_name'],
                'quantity': row['quantidade'],
                'price_at_time_of_add': row['preco_unitario_no_momento'],
                'item_total': item_total,
                'image_url': row['image_url']
            })
            cart_total_value += item_total

        # Após calcular o cart_total_value
        final_total = cart_total_value - discount # Atualiza final_total aqui

        if not cart_items:
            flash("Seu carrinho está vazio. Adicione itens antes de finalizar a compra.", "warning")
            return redirect(url_for('loja_page'))

    except Exception as e:
        print(f"Erro ao buscar itens do carrinho para checkout: {e}")
        flash("Ocorreu um erro ao carregar seu carrinho. Tente novamente mais tarde.", "danger")
        return redirect(url_for('loja_page'))
    finally:
        if cur: cur.close()

    user_addresses = []
#implementar lógica de endereços aqui
    
    return render_template(
        'checkout.html',
        cart_items=cart_items,
        cart_total_value=cart_total_value,
        user_addresses=user_addresses,
        discount=discount, # Passa a variável discount
        final_total=final_total, # Passa a variável final_total
        coupon_code="",
        user_email=g.user_db_data['email'] if g.user_db_data else None,
        user_name=g.user_db_data['nome'] if g.user_db_data and 'nome' in g.user_db_data else None
    )


if __name__ == '__main__':
    init_db_pool()
    app.run(host='0.0.0.0', port=80, debug=True)
