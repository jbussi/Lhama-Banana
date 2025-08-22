from .main import main_bp
from .api import api_bp
from .produtos import produtos_bp
from .auth import auth_bp
from .services import get_db, close_db_connection, init_db_pool
# importa a blueprint com todas as rotas