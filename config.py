import os

class Config:
    SECRET_KEY = "asdf#FGSgvasgf$5$WGT"
    
    FIREBASE_ADMIN_SDK_PATH = os.environ.get('FIREBASE_ADMIN_SDK_PATH', 'C:\\Users\\João Paulo Bussi\\Downloads\\LhamaBanana_visual_estatica_corrigida\\key.json')

    DATABASE_CONFIG = { # <--- Mude de DB_config para DATABASE_CONFIG
        "host": "localhost",
        "dbname": "sistema_usuarios",
        "user": "postgres",
        "password": "far111111"
    }

    PAGSEGURO_SANDBOX_API_TOKEN = os.environ.get('PAGSEGURO_SANDBOX_API_TOKEN', 'YOUR_PAGSEGURO_SANDBOX_TOKEN_IF_NOT_IN_CONFIG')
    PAGSEGURO_SANDBOX_CHECKOUT_URL = "https://sandbox.api.pagseguro.com/checkouts"
    PAGSEGURO_RETURN_URL = "http://localhost:80/pagseguro/return"
    PAGSEGURO_REDIRECT_URL = "http://localhost:80/pagseguro/redirect"
    PAGSEGURO_NOTIFICATION_URL = "http://localhost:80/pagseguro/notification"