from flask import Blueprint

api_bp = Blueprint("api", __name__)

from . import carrinho, login, loja, perfil, produto, register, checkout, orders, webhook