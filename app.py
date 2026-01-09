"""
Aplicação Flask - LhamaBanana E-commerce
=========================================
"""

import os
import sys
import time
from blueprints import auth_bp, produtos_bp, api_bp, main_bp, checkout_api_bp, shipping_api_bp
from blueprints.api.labels import labels_api_bp
from blueprints.api.webhook import webhook_api_bp
from blueprints.api.pagbank import pagbank_api_bp
from blueprints.api.bling import bling_bp
from blueprints.admin import admin_bp
from blueprints.admin.api import admin_api_bp
from flask import Flask, render_template, jsonify
from config import CurrentConfig
from plataform_config import init_app
from flask_cors import CORS

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def create_app(config_class=None):
    """
    Factory function para criar a aplicação Flask.
    
    Args:
        config_class: Classe de configuração (opcional, usa CurrentConfig por padrão)
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Carregar configurações
    config_to_use = config_class or CurrentConfig
    app.config.from_object(config_to_use)
    
    # Determinar ambiente
    env = app.config.get('ENV', 'development')
    is_dev = env == 'development'
    is_prod = env == 'production'
    
    # Configurações específicas por ambiente
    if is_dev:
        app.config.update(
            SEND_FILE_MAX_AGE_DEFAULT=0,
            TEMPLATES_AUTO_RELOAD=True,
            DEBUG=True,
            EXPLAIN_TEMPLATE_LOADING=True,
            JSONIFY_PRETTYPRINT_REGULAR=True,
            JSON_SORT_KEYS=False
        )
        app.jinja_env.cache = {}
        print("🔧 Modo de desenvolvimento ativado")
    elif is_prod:
        app.config.update(
            SEND_FILE_MAX_AGE_DEFAULT=31536000,  # 1 ano
            TEMPLATES_AUTO_RELOAD=False,
            DEBUG=False
        )
        print("🏭 Modo de produção ativado")
    else:
        print(f"🧪 Modo {env} ativado")
    
    # Inicializar serviços (Firebase, DB, etc)
    init_app(app)
    
    # Configurar CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*" if is_dev else app.config.get('ALLOWED_ORIGINS', []),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Middleware para cache em desenvolvimento
    @app.after_request
    def add_header(response):
        if is_dev:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            # Adicionar timestamp para forçar recarregamento de assets
            if response.content_type and response.content_type.startswith(('text/javascript', 'text/css')):
                response.direct_passthrough = False
                content = response.get_data(as_text=True)
                if not content.strip().endswith(';'):
                    content += ';'
                content += f"\n/* Timestamp: {int(time.time())} */\n"
                response.set_data(content)
        return response
    
    # Registrar blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp, url_prefix="/produtos")
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(checkout_api_bp)
    app.register_blueprint(shipping_api_bp, url_prefix='/api/shipping')
    app.register_blueprint(pagbank_api_bp)
    app.register_blueprint(labels_api_bp)
    app.register_blueprint(webhook_api_bp)
    app.register_blueprint(bling_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_api_bp)
    
    # Handler para erro 404
    @app.errorhandler(404)
    def not_found_error(error):
        # Se for uma requisição de API, retornar JSON
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({"erro": "Endpoint não encontrado", "path": request.path}), 404
        return render_template('404.html'), 404
    
    # Handler para erro 403 (Forbidden) - redireciona para 404
    @app.errorhandler(403)
    def forbidden_error(error):
        # Se for uma requisição de API, retornar JSON
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({"erro": "Acesso negado", "path": request.path}), 403
        return render_template('404.html'), 404
    
    # Handler para erro 500 (Internal Server Error) - retornar JSON para APIs
    @app.errorhandler(500)
    def internal_error(error):
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({"erro": "Erro interno do servidor"}), 500
        return render_template('500.html') if hasattr(app, 'template_folder') else "Erro interno do servidor", 500
    
    return app


app = create_app()


if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = app.config.get('DEBUG', False)
    app.run(host='0.0.0.0', port=port, debug=debug)
