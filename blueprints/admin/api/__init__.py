from .routes import admin_api_bp

# Importar e registrar endpoints de cadastros base
from . import cadastros_base# Registrar blueprint de cadastros dentro do admin_api
admin_api_bp.register_blueprint(cadastros_base.cadastros_base_bp)