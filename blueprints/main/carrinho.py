from flask import render_template, session
from . import main_bp

@main_bp.route('/carrinho')
@main_bp.route('/cart')
def carrinho():
    return render_template('carrinho.html', user=session.get('uid'))