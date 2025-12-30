from flask import Blueprint

main_bp = Blueprint(
    "main",
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/main'  # Alterado para um caminho mais previsível
)

from . import carrinho, checkout, contato, home, perfil, sobre_nos, order_confirmation, payment_routes