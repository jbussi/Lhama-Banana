import os
import sys
from functools import wraps
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, session, redirect, url_for, flash, request, jsonify, g
from flask_cors import CORS
import psycopg2

from firebase_admin import auth, credentials, initialize_app

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app) 
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT' # Chave secreta para sessões
conn = psycopg2.connect(
    host="localhost",
    dbname="sistema_usuarios",
    user="postgres",
    password="far111111"
)
cred = credentials.Certificate("C:\\Users\\João Paulo Bussi\\Downloads\\LhamaBanana_visual_estatica_corrigida\\key.json")
initialize_app(cred)

def get_user_by_firebase_uid(firebase_uid):
    """Busca os dados principais de um usuário pelo seu Firebase UID."""
    if conn is None: return None # Ou levante um erro se o DB não estiver conectado
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
    if conn is None: return None
    try:
        cur = conn.cursor()
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
    if conn is None: return False
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

# Dados estáticos para simulação
produtos = [
    {
        "id": 1,
        "name": "Pijama Lhamitas Felizes",
        "price": 79.90,
        "image": "img/pijama_exemplo1.jpg",
        "category": "infantil",
        "description": "Pijama infantil com estampa de lhamas felizes, super confortável e divertido."
    },
    {
        "id": 2,
        "name": "Conjunto Bananinhas",
        "price": 149.90,
        "image": "img/pijama_exemplo2.jpg",
        "category": "mae-filha",
        "description": "Conjunto mãe e filha com estampa de bananas, perfeito para momentos especiais."
    },
    {
        "id": 3,
        "name": "Pijama Adulto Sonho Leve",
        "price": 99.90,
        "image": "img/pijama_exemplo3.jpg",
        "category": "adulto",
        "description": "Pijama adulto com tecido leve e macio, ideal para noites tranquilas."
    },
    {
        "id": 4,
        "name": "Pijama Unicórnio Mágico",
        "price": 85.00,
        "image": "img/pijama_exemplo4.jpg",
        "category": "infantil",
        "description": "Pijama infantil com estampa de unicórnios, para sonhos mágicos e coloridos."
    }
]

# Rotas para visualização estática
@app.route('/')
def home():
    return render_template('home.html', user=session.get('uid'))

@app.route('/loja')
def loja():
    return render_template('loja.html', products=produtos, user=session.get('uid'))

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

@app.route('/produto/<int:id>')
def produto(id):
    # Busca o produto pelo ID
    produto_encontrado = next((p for p in produtos if p['id'] == id), None)
    if not produto_encontrado:
        # Se não encontrar o produto, redireciona para a loja
        return redirect(url_for('loja'))
    
    # Dados de exemplo para o produto
    produto_detalhado = {
        **produto_encontrado,
        'description': produto_encontrado.get('description', 'Este é um produto incrível com estampa de lhama, feito com materiais de alta qualidade e muito conforto. Perfeito para quem ama estilo e conforto.'),
        'category': produto_encontrado.get('category', 'Infantil'),
        'codigo': f'PROD{id:04d}',
        'colors': ['Azul', 'Vermelho', 'Verde'],
        'sizes': ['P', 'M', 'G', 'GG'],
        'reviews': [
            {'user': 'Cliente Satisfeito', 'rating': 5, 'comment': 'Adorei o produto!', 'date': '10/07/2024'},
            {'user': 'Comprador Feliz', 'rating': 4, 'comment': 'Muito bom, recomendo!', 'date': '09/07/2024'}
        ],
        'images': [
            produto_encontrado['image'],
            'img/produto1_2.jpg',
            'img/produto1_3.jpg'
        ],
        'old_price': produto_encontrado.get('old_price', float(produto_encontrado['price']) * 1.2),  # 20% mais caro como preço antigo
        'discount': 20,  # 20% de desconto
        'stock': 50,  # Quantidade em estoque
        'tags': ['lhamas', 'infantil', 'conforto'],
        'material': 'Algodão 100%',
        'cor': 'Varia conforme o modelo',
        'tamanho': 'P, M, G, GG',
        'peso': '200g',
        'composicao': '95% Algodão, 5% Elastano',
        'instrucoes': 'Lavar na máquina com água fria, não usar alvejante, secar à sombra'
    }
    return render_template('produto.html', produto=produto_detalhado)

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

@app.route('/checkout')
def checkout():
    # Simulação de checkout com dados estáticos
    cart_items = [
        {"product": produtos[0], "quantity": 1, "item_total": 79.90},
        {"product": produtos[1], "quantity": 1, "item_total": 149.90}
    ]
    order_total = 229.80
    discount = 20.00
    final_total = order_total - discount
    
    # Endereços de exemplo
    user_addresses = [
        {"id": 1, "nickname": "Casa", "street": "Rua das Bananeiras", "number": "123", "city": "Cidade Feliz"}
    ]
    
    return render_template('checkout.html', 
                          cart_items=cart_items, 
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
    app.run(host='0.0.0.0', port=80, debug=True)
