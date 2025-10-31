from flask import Blueprint

main_bp = Blueprint("main", __name__, template_folder='templates', static_folder='static', static_url_path='/main_static')

from . import carrinho, checkout, contato, home, perfil, sobre_nos, order_confirmation