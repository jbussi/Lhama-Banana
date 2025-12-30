import os
import sys
import time
from blueprints import auth_bp, produtos_bp, api_bp, main_bp, checkout_api_bp, shipping_api_bp
from blueprints.api.labels import labels_api_bp
from blueprints.api.orders import orders_api_bp
from blueprints.api.webhook import webhook_api_bp
from blueprints.admin import admin_bp
from blueprints.admin.api import admin_api_bp
from flask import Flask
from config import Config
from plataform_config import init_app
from flask_cors import CORS

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Forçar modo de desenvolvimento
    os.environ['FLASK_DEBUG'] = '1'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DEV_MODE'] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    # Desabilitar cache completamente em desenvolvimento
    is_dev = True
    
    # Configurações para desenvolvimento
    if is_dev:
        app.config.update(
            # Desabilitar cache
            SEND_FILE_MAX_AGE_DEFAULT=0,
            TEMPLATES_AUTO_RELOAD=True,
            DEBUG=True,
            # Outras configurações úteis para desenvolvimento
            EXPLAIN_TEMPLATE_LOADING=True,
            JSONIFY_PRETTYPRINT_REGULAR=True,
            JSON_SORT_KEYS=False
        )
        
        # Desabilitar cache do Jinja2
        app.jinja_env.cache = {}
    
    # Sempre usar Config (configurações podem ser sobrescritas por variáveis de ambiente)
    app.config.from_object(Config)
    
    if is_dev:
        print("🔧 Modo de desenvolvimento ativado")
    else:
        print("🏭 Modo de produção ativado")
    
    init_app(app)
    
    # Função para forçar recarregamento dos arquivos estáticos
    @app.after_request
    def add_header(response):
        # Prevenir cache em desenvolvimento
        if is_dev:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            # Adicionar timestamp para forçar recarregamento
            if response.content_type.startswith(('text/javascript', 'text/css')):
                response.direct_passthrough = False
                content = response.get_data(as_text=True)
                if not content.strip().endswith(';'):
                    content += ';'
                content += f"\n/* Timestamp: {int(time.time())} */\n"
                response.set_data(content)
        return response


    
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp, url_prefix="/produtos")
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(checkout_api_bp)
    app.register_blueprint(shipping_api_bp, url_prefix='/api/shipping')
    app.register_blueprint(labels_api_bp)
    app.register_blueprint(orders_api_bp)
    app.register_blueprint(webhook_api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_api_bp)

    return app

app = create_app()

if __name__ == '__main__':
    # Usar porta 5000 em desenvolvimento, porta 80 em produção
    port = 5000 if app.config.get('DEBUG', False) else 80
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))