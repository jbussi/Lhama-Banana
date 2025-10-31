from flask import render_template, session
from . import main_bp

@main_bp.route('/checkout')
def checkout_page():
    """
    Página de checkout do carrinho.
    Renderiza o template checkout.html do blueprint main.
    """
    # Verifica se o usuário está logado
    user_logged_in = 'user_id' in session
    user_email = session.get('email', '')
    user_name = session.get('username', '')
    
    # O Flask automaticamente procura em blueprints/main/templates/checkout.html
    # devido ao template_folder='templates' definido no blueprint
    return render_template('checkout.html', 
                         user_logged_in=user_logged_in,
                         user_email=user_email,
                         user_name=user_name)