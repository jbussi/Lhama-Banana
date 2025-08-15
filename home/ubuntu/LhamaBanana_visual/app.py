import os
import sys
from functools import wraps
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify, g
from flask_cors import CORS
import psycopg2.pool

from firebase_admin import auth, credentials, initialize_app

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app) 
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT' # Chave secreta para sessões

DB_config = {
    "host":"localhost",
    "dbname":"sistema_usuarios",
    "user":"postgres",
    "password":"far111111"
}
connection_pool = None

def init_db_pool():
    """Inicializa o pool de conexões do banco de dados. Chamado uma vez."""
    global connection_pool
    try:
        # ThreadedConnectionPool é ideal para Flask (multi-thread)
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,  # Número mínimo de conexões ociosas no pool
            maxconn=20, # Número máximo de conexões que podem ser abertas no pool
            **DB_config
        )
        print("Database connection pool initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize database connection pool: {e}")
        # Se o pool não pode ser inicializado, a aplicação não pode funcionar.
        # Poderíamos considerar um exit(1) aqui em produção.


def get_db():
    """Obtém uma conexão do pool e a armazena em g (contexto da requisição)."""
    if 'db' not in g:
        try:
            g.db = connection_pool.getconn()
            # print("Connection obtained from pool.") # Para depuração
        except Exception as e:
            # Caso o pool não consiga fornecer uma conexão (ex: pool esgotado, DB offline)
            print(f"ERROR: Could not get connection from pool: {e}")
            raise # Re-lança a exceção para que o Flask a capture e retorne um erro 500
    return g.db

@app.teardown_appcontext
def close_db_connection(exception):
    """Retorna a conexão ao pool no final da requisição."""
    db = g.pop('db', None) # Tenta pegar a conexão do g e remove-a
    if db is not None:
        if db.closed: # Verifica se a conexão já está fechada por algum erro
            print("WARNING: Attempted to return a closed connection to the pool.")
        else:
            connection_pool.putconn(db) # Retorna a conexão para o pool
            # print("Connection returned to pool.") # Para depuração


cred = credentials.Certificate("C:\\Users\\João Paulo Bussi\\Downloads\\LhamaBanana_visual_estatica_corrigida\\key.json")
initialize_app(cred)

def get_user_by_firebase_uid(firebase_uid):
    """Busca os dados principais de um usuário pelo seu Firebase UID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, firebase_uid, nome, email, cpf, data_nascimento, criado_em, telefone
        FROM usuarios WHERE firebase_uid = %s
    """, (firebase_uid,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        # Retorna um dicionário para facilitar o acesso por nome da coluna
        # Adapte os índices conforme a ordem das colunas no seu SELECT
        return {
            'id': user_data[0],
            'firebase_uid': user_data[1],
            'nome': user_data[2],
            'email': user_data[3],
            'cpf': user_data[4],
            'data_nascimento': str(user_data[5]) if user_data[5] else None,
            'criado_em': str(user_data[6]),
            'telefone': user_data[7],
        }
    return None

def insert_new_user(firebase_uid, nome, email):
    """Insere um novo usuário na tabela 'usuarios'."""
    conn = get_db() # Obtém a conexão do pool
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (firebase_uid, nome, email) VALUES (%s, %s, %s) RETURNING id",
            (firebase_uid, nome, email)
        )
        new_user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return new_user_id
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao inserir novo usuário: {e}")
        return None

def update_user_profile_db(user_id, data):
    """Atualiza os dados de perfil de um usuário."""
    conn = get_db() # Obtém a conexão do pool
    cur = conn.cursor()
    try:
        cur = conn.cursor()
        # Construa a query dinamicamente para atualizar apenas campos presentes em 'data'
        updates = []
        params = []
        
        if 'nome' in data:
            updates.append("nome = %s")
            params.append(data['nome'])
        if 'email' in data: # Cuidado ao permitir atualização de email que é também UID no Firebase
            updates.append("email = %s")
            params.append(data['email'])
        if 'cpf' in data:
            updates.append("cpf = %s")
            params.append(data['cpf'])
        if 'data_nascimento' in data:
            updates.append("data_nascimento = %s")
            # Converta string para date object se necessário, ex: datetime.date.fromisoformat(data['data_nascimento'])
            params.append(data['data_nascimento']) 
        if 'telefone' in data:
            updates.append("telefone = %s")
            params.append(data['telefone'])

        if not updates: # Nenhuma atualização para fazer
            cur.close()
            return True

        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
        params.append(user_id)
        
        cur.execute(query, tuple(params))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao atualizar perfil do usuário {user_id}: {e}")
        return False

def login_required_and_load_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get('uid')
        if not uid:
            return redirect(url_for('login_page')) # Sua rota de login HTML

        user_data = get_user_by_firebase_uid(uid) # Usa a função auxiliar
        if not user_data:
            session.pop('uid', None) # Limpa sessão se usuário não existe no DB
            return redirect(url_for('login_page'))

        g.user = user_data # g.user agora é um dicionário com os dados principais

        # Busca dados relacionados e os adiciona a g.user
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador que verifica se o usuário tem permissão de administrador.
    Assume que `login_required_and_load_user` já foi aplicado e `g.user_db_data` está preenchido.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # g.user_db_data já deve estar preenchido por login_required_and_load_user
        if not hasattr(g, 'user_db_data') or g.user_db_data.get('role') != 'admin':
            flash("Acesso negado: Você não possui permissões de administrador.")
            # Você pode escolher redirecionar para uma página de acesso negado
            # ou simplesmente retornar um 404 (para não dar dicas sobre a existência da página)
            return redirect(url_for('home')) # Redireciona para a home
            # from flask import abort
            # abort(404) # Se quiser um 404 para esconder a página

        return f(*args, **kwargs)
    return decorated_function

def get_or_create_cart(user_uid=None, session_id=None):
    """
    Obtém o carrinho de um usuário logado ou de uma sessão anônima.
    Cria um novo carrinho se não existir.
    Retorna o ID do carrinho no DB.
    """
    conn = get_db()
    cur = conn.cursor()
    carrinho_id = None

    try:
        if user_uid:
            cur.execute("SELECT id FROM carrinhos WHERE usuario_uid = %s", (user_uid,))
            result = cur.fetchone()
            if result:
                carrinho_id = result[0]
            else:
                cur.execute("INSERT INTO carrinhos (usuario_uid) VALUES (%s) RETURNING id", (user_uid,))
                carrinho_id = cur.fetchone()[0]
                conn.commit()
        elif session_id:
            cur.execute("SELECT id FROM carrinhos WHERE session_id = %s", (session_id,))
            result = cur.fetchone()
            if result:
                carrinho_id = result[0]
            else:
                cur.execute("INSERT INTO carrinhos (session_id) VALUES (%s) RETURNING id", (session_id,))
                carrinho_id = cur.fetchone()[0]
                conn.commit()
        else:
            # Isso não deve acontecer se get_cart_owner_info for bem-sucedido
            raise ValueError("user_id ou session_id deve ser fornecido para get_or_create_cart.")

    except Exception as e:
        conn.rollback() # Garante rollback em caso de erro na criação/busca
        print(f"Erro ao obter/criar carrinho: {e}")
        raise # Re-lança a exceção para que o endpoint a capture
    finally:
        if cur: cur.close()
    return carrinho_id

def get_cart_owner_info():
    """
    Determina o identificador do carrinho para a requisição atual.
    Prioriza usuário logado sobre sessão anônima.
    Retorna (erro_response, user_id, session_id). Se erro_response não for None, use-o.
    """
    user_uid = None
    session_id_from_header = request.headers.get('X-Session-ID') # Frontend envia este header

    # 1. Verifica se o usuário está logado
    if hasattr(g, 'user_db_data') and g.user_db_data and g.user_db_data.get('uid'):
        user_uid = g.user_db_data['id']
        # Se logado, o session_id anônimo é ignorado para as operações de cart
        # (será usado apenas na mesclagem, se aplicável)
        return None, user_uid, None
    
    # 2. Se não está logado, tenta usar o session_id do header
    if session_id_from_header:
        return None, None, session_id_from_header
    
    # 3. Se nem logado nem session_id, é um erro
    return jsonify({"erro": "Autenticação necessária ou ID de sessão anônima ausente."}), None, None

# Rotas para visualização estática
@app.route('/')
def home():
    return render_template('home.html', user=session.get('uid'))

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

@app.route('/sobre-nos')
def sobre_nos():
    return render_template('sobre_nos.html', user=session.get('uid'))

@app.route('/contato')
def contato():
    return render_template('contato.html', user=session.get('username'))

@app.route('/perfil', methods=["GET"])
@login_required_and_load_user # Garante que o usuário está logado e g.user está populado
def perfil_page():
    return render_template('perfil.html')

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('uid', None) # Remove o ID do usuário da sessão
    return redirect(url_for('login_page'))

# Rota API para obter os dados do perfil do usuário logado (GET JSON)
@app.route('/api/user_data', methods=["GET"])
@login_required_and_load_user # Garante que o usuário está logado e g.user está populado
def get_user_profile_data_api():
    # g.user já está populado pelo decorator com todos os dados (principais, endereços, vendas)
    return jsonify(g.user)

@app.route('/api/user_data', methods=["PUT"]) # ou POST, mas PUT é mais semântico para atualização
def update_user_profile_api():
    data = request.get_json()
    id_token = request.headers.get("Authorization").split("Bearer ")[1] # Pega o token do header

    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401

    try:
        decoded_token = auth.verify_id_token(id_token)
        firebase_uid = decoded_token['uid']
        
        # Busque o usuário pelo firebase_uid para obter o id interno do seu DB
        user_in_db = get_user_by_firebase_uid(firebase_uid)
        if not user_in_db:
            return jsonify({"erro": "Usuário não encontrado em seu sistema."}), 404
        
        user_id_db = user_in_db['id']

        # Limpa dados que não devem ser atualizados via essa rota ou que são gerados pelo Firebase
        data_to_update = {k: v for k, v in data.items() if k in ['nome', 'email', 'cpf', 'data_nascimento', 'telefone']}
        
        if update_user_profile_db(user_id_db, data_to_update):
            return jsonify({"mensagem": "Perfil atualizado com sucesso"}), 200
        else:
            return jsonify({"erro": "Falha ao atualizar perfil no banco de dados"}), 500
    except auth.InvalidIdTokenError:
        return jsonify({"erro": "Token inválido ou expirado"}), 401
    except Exception as e:
        print(f"Erro ao atualizar perfil: {e}")
        return jsonify({"erro": "Erro interno do servidor"}), 500

@app.route('/register', methods=["GET"])
def register_page():
        return render_template('register.html')


@app.route('/api/register_user', methods=["POST"])
def register_api():
    # método POST:
    data = request.get_json()
    id_token = data.get("id_token")  # Token JWT enviado pelo frontend
    username = data.get("username")

    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401

    try:
        # Verifica e decodifica o token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token['email']
        # Agora insere no banco com o uid validado
        conn = get_db() # Obtém a conexão do pool
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (firebase_uid, nome, email) VALUES (%s, %s, %s)",
            (uid, username, email)
        )
        conn.commit()
        cur.close()

        return jsonify({"mensagem": "Conta criada com sucesso"}), 200

    except auth.InvalidIdTokenError:
        return jsonify({"erro": "Token inválido"}), 401
    except auth.ExpiredIdTokenError:
        return jsonify({"erro": "Token expirado"}), 401
    except Exception as e:
        print(f"Erro ao salvar usuário no banco: {e}")
        return jsonify({"erro": "Erro interno ao salvar usuário"}), 500

@app.route('/login', methods=["GET"])
def login_page():
    return render_template('login.html')


@app.route('/api/login_user', methods=["POST"])
def login_api():
        # método POST:
    data = request.get_json()
    id_token = data.get("id_token") # pode ser None se não enviado
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401


    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']        
        conn = get_db() # Obtém a conexão do pool
        cur = conn.cursor()
        # Buscar dados do usuário
        cur.execute("""
            SELECT id, nome, email, cpf, data_nascimento, criado_em, telefone
            FROM usuarios WHERE firebase_uid = %s
        """, (uid,))
        user = cur.fetchone()

        if user is None:
            cur.close()
            return jsonify({"erro": "Usuário não encontrado em seu sistema. Por favor, registre-se."}), 404

        cur.close()

        session['uid'] = uid
        return jsonify({"mensagem": "Login efetuado com sucesso"}), 200
    except Exception as e:
        print("Erro ao consultar usuário:", e)
        return jsonify({"erro": "Erro interno do servidor ao efetuar login"}), 500

@app.route('/produto/<int:nome_produto_id>')
def produto_page(nome_produto_id):
    """Rota da página de detalhes do produto. O JavaScript buscará os detalhes."""
    # Este 'nome_produto_id' é o ID do produto base (da tabela nome_produto)
    # que o frontend JS usará para chamar a API.
    return render_template('produto.html', nome_produto_id=nome_produto_id, user=session.get('uid'))

@app.route('/api/base_products/<int:nome_produto_id>', methods=['GET'])
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
                p.estoque,
                p.codigo_sku,
                -- Agrega as imagens de CADA VARIAÇÃO em um array JSON (Recurso do PostgreSQL)
                ARRAY_AGG(JSON_BUILD_OBJECT('id', ip.id, 'url', ip.url, 'ordem', ip.ordem, 'descricao', ip.descricao, 'is_thumbnail', ip.is_thumbnail) ORDER BY ip.ordem) FILTER (WHERE ip.id IS NOT NULL) AS images_json
            FROM produtos p
            JOIN estampa e ON p.estampa_id = e.id
            JOIN tamanho t ON p.tamanho_id = t.id
            LEFT JOIN imagens_produto ip ON p.id = ip.produto_id -- LEFT JOIN para incluir variações sem imagem
            WHERE p.nome_produto_id = %s
            GROUP BY p.id, e.id, t.id, p.preco_venda, p.estoque, p.codigo_sku -- Agrupa por variação para que ARRAY_AGG funcione
            ORDER BY estampa_nome, tamanho_nome; -- Ordena para consistência
        """, (nome_produto_id,))
        variations_data = cur.fetchall()

        # 3. Formata os dados das variações
        for var in variations_data:
            # Pega as imagens agregadas (o elemento var[9] da tupla)
            images = var[9] if var[9] and var[9][0] is not None else []
            product_details['variations'].append({
                'id': var[0], # ID da variação específica de 'produtos'
                'estampa': {'id': var[1], 'nome': var[2], 'imagem_url': var[3]},
                'tamanho': {'id': var[4], 'nome': var[5]},
                'preco': float(var[6]),
                'estoque': var[7],
                'sku': var[8],
                'images': images # Array de URLs de todas as imagens para esta variação
            })
        
        # Retorna os detalhes completos do produto base e suas variações
        return jsonify(product_details), 200

    except Exception as e:
        print(f"Error fetching product details: {e}")
        return jsonify({"erro": "Erro interno do servidor ao carregar detalhes do produto."}), 500
    finally:
        if cur: cur.close() # Fecha o cursor, a conexão é retornada ao pool pelo teardown

@app.route('/carrinho')
def carrinho():
    # Simulação de carrinho com produtos estáticos
    cart_items = [
        {
            "id": 1,
            "name": "Pijama Lhamitas Felizes",
            "price": 79.90,
            "quantity": 1,
            "image": "img/pijama_exemplo1.jpg",
            "item_total": 79.90
        },
        {
            "id": 2,
            "name": "Conjunto Bananinhas",
            "price": 149.90,
            "quantity": 1,
            "image": "img/pijama_exemplo2.jpg",
            "item_total": 149.90
        }
    ]
    total_price = sum(item["item_total"] for item in cart_items)
    return render_template('carrinho.html', cart_items=cart_items, total_price=total_price, user="Visitante (Demo)")

@app.route('/api/cart', methods=['GET'])
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
            ORDER BY ci.adicionado_em;
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

@app.route('/api/cart/add', methods=['POST'])
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
            new_quantity = cart_item[1] + quantity
            if new_quantity > current_stock:
                return jsonify({"erro": f"Adicionar mais itens excederia o estoque. Máximo disponível: {current_stock}."}), 400
            cur.execute("UPDATE carrinho_itens SET quantidade = %s, adicionado_em = NOW() WHERE id = %s", (new_quantity, cart_item[0]))
        else:
            if quantity > current_stock: # Verifica estoque para o primeiro item também
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

@app.route('/api/cart/update/<int:cart_item_id>', methods=['PUT'])
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

@app.route('/api/cart/remove/<int:cart_item_id>', methods=['DELETE'])
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

@app.route('/api/cart/clear', methods=['DELETE'])
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
@app.route('/api/cart/merge', methods=['POST'])
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


@app.route('/checkout')
def checkout():
    # Simulação de checkout com dados estáticos

    order_total = 229.80
    discount = 20.00
    final_total = order_total - discount
    
    # Endereços de exemplo
    user_addresses = [
        {"id": 1, "nickname": "Casa", "street": "Rua das Bananeiras", "number": "123", "city": "Cidade Feliz"}
    ]
    
    return render_template('checkout.html', 
                          order_total=order_total,
                          discount=discount, 
                          final_total=final_total,
                          user_addresses=user_addresses,
                          coupon_code="DEMO20",
                          user="Visitante (Demo)")

@app.route('/order_confirmation')
def order_confirmation():
    # Simulação de dados de pedido
    order_details = {
        "order_number": "ORD123456",
        "date": "15/07/2025",
        "total": 229.80,
        "discount": 20.00,
        "final_total": 209.80,
        "shipping_address": "Rua das Bananeiras, 123 - Cidade Feliz",
        "payment_method": "Cartão de Crédito",
        "status": "Pedido Confirmado"
    }
    return render_template('order_confirmation.html', order_details=order_details, user="Visitante (Demo)")

@app.route('/admin')
def admin():
    # Simulação de painel administrativo com dados estáticos
    insights = {
        "total_users": 42,
        "total_products": 15,
        "total_orders": 28,
        "total_revenue": 3450.75,
        "recent_orders": [
            {"id": 1001, "user": {"username": "maria_silva"}, "user_id": 1, "created_at": "2025-05-14 10:30:00", "total_amount": 229.80, "status": "Entregue"},
            {"id": 1002, "user": {"username": "joao_santos"}, "user_id": 2, "created_at": "2025-05-14 14:45:00", "total_amount": 159.90, "status": "Processando"},
            {"id": 1003, "user": {"username": "ana_costa"}, "user_id": 3, "created_at": "2025-05-15 09:15:00", "total_amount": 85.00, "status": "Pendente"}
        ]
    }
    return render_template('admin/dashboard.html', insights=insights, user="Admin (Demo)")

if __name__ == '__main__':
    init_db_pool()
    app.run(host='0.0.0.0', port=80, debug=True)
