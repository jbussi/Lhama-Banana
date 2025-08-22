from flask import render_template, session
from . import produtos_bp

@produtos_bp.route('/')
def produtos_page():
    return render_template('loja.html')

@produtos_bp.route('/<int:nome_produto_id>')
def produto_page(nome_produto_id):
    return render_template('produto.html', nome_produto_id=nome_produto_id, user=session.get('uid'))