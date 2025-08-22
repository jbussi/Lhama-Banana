import os
import sys
from blueprints import auth_bp, produtos_bp, api_bp, main_bp
from flask import Flask
from config import Config
from plataform_config import init_app

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    app.config.from_object(Config)
    
    init_app(app)
    
    app.register_blueprint(main_bp)
    app.register_blueprint(produtos_bp, url_prefix="/produtos")
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)