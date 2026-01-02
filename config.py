"""
Configurações do Sistema LhamaBanana
====================================

Este arquivo contém todas as configurações do sistema.
As configurações podem ser sobrescritas via variáveis de ambiente no arquivo .env

Ambientes suportados:
- development: Desenvolvimento local
- production: Produção
- testing: Testes
"""

import os
from pathlib import Path

# Determinar ambiente atual
ENV = os.environ.get('ENV', os.environ.get('FLASK_ENV', 'development')).lower()

class Config:
    """Configurações base do sistema"""
    
    # ============================================
    # AMBIENTE
    # ============================================
    ENV = ENV
    DEBUG = ENV == 'development'
    TESTING = ENV == 'testing'
    
    # ============================================
    # SEGURANÇA
    # ============================================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    
    # ============================================
    # FIREBASE (Autenticação)
    # ============================================
    # Caminho do arquivo de credenciais do Firebase
    # No Docker: /app/key.json
    # Local: ../key.json (raiz do workspace)
    def _get_default_firebase_path():
        """Detecta automaticamente o caminho do key.json"""
        # Verificar se já está definido via env
        env_path = os.environ.get('FIREBASE_ADMIN_SDK_PATH')
        if env_path:
            return env_path
        
        # Tentar /app/key.json (Docker)
        docker_path = Path('/app/key.json')
        if docker_path.exists() and docker_path.is_file():
            return str(docker_path)
        
        # Tentar ../key.json (raiz do workspace)
        root_key = Path(__file__).parent.parent / 'key.json'
        if root_key.exists() and root_key.is_file():
            return str(root_key)
        
        # Fallback
        return '/app/key.json'
    
    FIREBASE_ADMIN_SDK_PATH = os.environ.get('FIREBASE_ADMIN_SDK_PATH', _get_default_firebase_path())
    
    # ============================================
    # BANCO DE DADOS
    # ============================================
    DATABASE_CONFIG = {
        "host": os.environ.get('DB_HOST', 'postgres' if ENV != 'development' else 'localhost'),
        "dbname": os.environ.get('DB_NAME', 'sistema_usuarios'),
        "user": os.environ.get('DB_USER', 'postgres'),
        "password": os.environ.get('DB_PASSWORD', 'far111111'),
        "port": os.environ.get('DB_PORT', '5432')
    }
    
    # ============================================
    # PAGBANK - GATEWAY DE PAGAMENTO
    # ============================================
    PAGBANK_API_TOKEN = os.environ.get('PAGBANK_API_TOKEN', '')
    PAGBANK_SANDBOX_API_URL = "https://sandbox.api.pagseguro.com/orders"
    PAGBANK_PRODUCTION_API_URL = "https://api.pagseguro.com/orders"
    PAGBANK_ENVIRONMENT = os.environ.get('PAGBANK_ENVIRONMENT', 'sandbox')
    PAGBANK_NOTIFICATION_URL = os.environ.get(
        'PAGBANK_NOTIFICATION_URL',
        'http://localhost:5000/api/webhook/pagbank' if ENV == 'development' else
        'https://seudominio.com/api/webhook/pagbank'
    )
    # Modo de simulação: se True, não chama a API real do PagBank
    PAGBANK_SIMULATION_MODE = os.environ.get('PAGBANK_SIMULATION_MODE', 'true').lower() == 'true'
    
    # ============================================
    # MELHOR ENVIO - CÁLCULO DE FRETE
    # ============================================
    MELHOR_ENVIO_TOKEN = os.environ.get('MELHOR_ENVIO_TOKEN', '')
    MELHOR_ENVIO_CEP_ORIGEM = os.environ.get('MELHOR_ENVIO_CEP_ORIGEM', '13219-052')
    
    # ============================================
    # ADMINISTRAÇÃO
    # ============================================
    _admin_emails_env = os.environ.get('ADMIN_EMAILS', '')
    ADMIN_EMAILS = (
        [email.strip() for email in _admin_emails_env.split(',') if email.strip()] 
        if _admin_emails_env 
        else ['joao.paulo.bussi1@gmail.com']
    )
    
    # ============================================
    # STRAPI - INTERFACE DE ADMINISTRAÇÃO
    # ============================================
    STRAPI_URL = os.environ.get('STRAPI_URL', 'http://strapi:1337')
    STRAPI_ENABLED = os.environ.get('STRAPI_ENABLED', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    ENV = 'production'
    PAGBANK_SIMULATION_MODE = False


class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    DEBUG = True
    ENV = 'testing'
    DATABASE_CONFIG = {
        "host": os.environ.get('DB_HOST', 'localhost'),
        "dbname": os.environ.get('DB_NAME', 'sistema_usuarios_test'),
        "user": os.environ.get('DB_USER', 'postgres'),
        "password": os.environ.get('DB_PASSWORD', 'far111111'),
        "port": os.environ.get('DB_PORT', '5432')
    }


# Mapeamento de ambientes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Configuração atual baseada no ambiente
CurrentConfig = config.get(ENV, config['default'])
