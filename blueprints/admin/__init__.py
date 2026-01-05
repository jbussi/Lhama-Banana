from flask import Blueprint

admin_bp = Blueprint('admin', __name__, 
                     template_folder='templates',
                     static_folder='static',
                     url_prefix='/admin')

# Importar proxy do Strapi (todas as rotas vão para o Strapi)
try:
    from . import strapi_proxy
except ImportError:
    pass

# Importar proxy do Metabase (rotas /analytics/* vão para o Metabase)
try:
    from . import metabase_proxy
except ImportError:
    pass

