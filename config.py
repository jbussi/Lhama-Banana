"""
Configurações do Sistema LhamaBanana
====================================

Este arquivo contém todas as configurações do sistema.
As configurações podem ser sobrescritas via variáveis de ambiente no arquivo .env

Ambientes suportados:
- development: Desenvolvimento locala
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
        'https://efractory-burdenless-kathlene.ngrok-free.dev/api/webhook/pagbank' if ENV == 'development' else
        'https://efractory-burdenless-kathlene.ngrok-free.dev/api/webhook/pagbank'
    )
    # Token secreto para validação de webhooks (recomendado usar token diferente do API_TOKEN)
    # Se não configurado, usará PAGBANK_API_TOKEN como fallback
    PAGBANK_WEBHOOK_SECRET = os.environ.get('PAGBANK_WEBHOOK_SECRET', '')
    
    # ============================================
    # BLING - ERP FISCAL E OPERACIONAL
    # ============================================
    BLING_CLIENT_ID = os.environ.get('BLING_CLIENT_ID', '')
    BLING_CLIENT_SECRET = os.environ.get('BLING_CLIENT_SECRET', '')
    BLING_REDIRECT_URI = os.environ.get('BLING_REDIRECT_URI', '')
    # URL base para webhooks e callbacks (usado com ngrok em desenvolvimento)
    NGROK_URL = os.environ.get('NGROK_URL', 'https://efractory-burdenless-kathlene.ngrok-free.dev')
    # URL do webhook do Bling (para receber notificações de estoque, produtos, etc.)
    BLING_WEBHOOK_URL = os.environ.get('BLING_WEBHOOK_URL', f'{NGROK_URL}/api/webhook/bling')
    
    # Estado da loja (emitente) para cálculo de CFOP
    # Use a UF do estado onde sua loja está registrada (ex: 'SP', 'RJ', 'MG')
    BLING_EMITENTE_ESTADO = os.environ.get('BLING_EMITENTE_ESTADO', 'SP')
    
    # Bling - Financeiro
    BLING_CATEGORIA_VENDAS_ID = os.environ.get('BLING_CATEGORIA_VENDAS_ID', '') # ID da categoria de vendas no Bling
    BLING_VENDEDOR_ID = os.environ.get('BLING_VENDEDOR_ID', '') # ID do vendedor padrão no Bling
    BASE_URL = os.environ.get('BASE_URL', NGROK_URL if ENV == 'development' else 'https://lhama-banana.com.br')
    # URL base para webhooks e callbacks (usado com ngrok em desenvolvimento)
    NGROK_URL = os.environ.get('NGROK_URL', 'https://efractory-burdenless-kathlene.ngrok-free.dev')
    BASE_URL = os.environ.get('BASE_URL', NGROK_URL if ENV == 'development' else 'https://lhama-banana.com.br')
    
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
    
    # ============================================
    # METABASE - ANALYTICS E DASHBOARDS
    # ============================================
    METABASE_URL = os.environ.get('METABASE_URL', 'http://metabase:3000')
    METABASE_ENABLED = os.environ.get('METABASE_ENABLED', 'true').lower() == 'true'
    
    # ============================================
    # EMAIL - SERVIÇO DE EMAILS CUSTOMIZADOS
    # ============================================
    # Configurações SMTP para envio de emails administrativos
    # Nota: Para emails de autenticação (verificação, reset), use o Firebase
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    EMAIL_FROM = os.environ.get('EMAIL_FROM', '')
    
    # ============================================
    # MFA - MULTI-FACTOR AUTHENTICATION
    # ============================================
    # Nome do emissor para códigos TOTP (aparece no app autenticador)
    MFA_ISSUER_NAME = os.environ.get('MFA_ISSUER_NAME', 'LhamaBanana')


class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    ENV = 'production'


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
