import os

class ConfigDev:
    """Configuração para desenvolvimento - sem dependências externas"""
    SECRET_KEY = "dev-key-for-testing"
    
    # Firebase - usar arquivo local
    FIREBASE_ADMIN_SDK_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'key.json')
    
    # Banco de dados - configuração de desenvolvimento
    DATABASE_CONFIG = {
        "host": "localhost",
        "dbname": "sistema_usuarios",
        "user": "postgres",
        "password": "far111111"
    }
    
    # PagSeguro - sandbox
    PAGSEGURO_SANDBOX_API_TOKEN = os.environ.get('PAGSEGURO_SANDBOX_API_TOKEN', '56db144e-54ab-4905-8c11-bcfbf040bee26ce79b14494f86bb8fe5af87bc0b53a0c020-c1fc-4a64-908a-dcd73ff498bc')
    PAGSEGURO_SANDBOX_CHECKOUT_URL = "https://sandbox.api.pagseguro.com/checkouts"
    PAGSEGURO_RETURN_URL = "http://localhost:80/pagseguro/return"
    PAGSEGURO_REDIRECT_URL = "http://localhost:80/pagseguro/redirect"
    PAGSEGURO_NOTIFICATION_URL = "http://localhost:80/pagseguro/notification"
    
    # Configurações de desenvolvimento
    DEBUG = True
    TESTING = False
