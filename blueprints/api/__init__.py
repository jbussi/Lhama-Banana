from flask import Blueprint

api_bp = Blueprint("api", __name__)

from . import carrinho, login, loja, perfil, produto, register, checkout, orders, webhook, auth

# Importar módulo de teste apenas em desenvolvimento
import os
if os.environ.get('FLASK_ENV', 'development') == 'development':
    from . import auth_test