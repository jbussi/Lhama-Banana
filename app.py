import os
import sys
from blueprints import auth_bp, produtos_bp, api_bp, main_bp, checkout_api_bp, shipping_api_bp
from blueprints.api.labels import labels_api_bp
from blueprints.admin import admin_bp
from blueprints.admin.api import admin_api_bp
from flask import Flask
from config import Config
from config_dev import ConfigDev
from plataform_config import init_app
from flask_cors import CORS

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Usar configuração de desenvolvimento se DEBUG estiver definido
    is_dev = (os.environ.get('FLASK_DEBUG') == '1' or 
              os.environ.get('FLASK_ENV') == 'development' or
              os.environ.get('DEV_MODE') == '1')
    
    if is_dev:
        app.config.from_object(ConfigDev)
        print("🔧 Modo de desenvolvimento ativado")
    else:
        app.config.from_object(Config)
        print("🏭 Modo de produção ativado")
    
    init_app(app)


    
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp, url_prefix="/produtos")
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(checkout_api_bp)
    app.register_blueprint(shipping_api_bp, url_prefix='/api/shipping')
    app.register_blueprint(labels_api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_api_bp)

    return app

app = create_app()

if __name__ == '__main__':
    # Usar porta 5000 em desenvolvimento, porta 80 em produção
    port = 5000 if app.config.get('DEBUG', False) else 80
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))