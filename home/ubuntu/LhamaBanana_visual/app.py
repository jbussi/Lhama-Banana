import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, session, redirect, url_for, flash, request

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT' # Chave secreta para sessões

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
    return render_template('home.html', user=session.get('username'))

@app.route('/loja')
def loja():
    return render_template('loja.html', products=produtos, user=session.get('username'))

@app.route('/sobre-nos')
def sobre_nos():
    return render_template('sobre_nos.html', user=session.get('username'))

@app.route('/contato')
def contato():
    return render_template('contato.html', user=session.get('username'))

@app.route('/perfil')
def perfil():
    # Simulação de perfil - apenas visual
    return render_template('perfil.html', user="Visitante (Demo)", user_data={"username": "Visitante", "email": "demo@exemplo.com"})

# Rota para testar o CSS
@app.route('/test_css')
def test_css():
    return app.send_static_file('css/profile.css')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

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
