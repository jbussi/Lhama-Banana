"""
Configurações do Sistema LhamaBanana
====================================

Este arquivo contém todas as configurações do sistema.
Altere os valores conforme necessário para seu ambiente.

Para produção, use variáveis de ambiente para sobrescrever valores sensíveis.
"""

import os

class Config:
    """Configurações principais do sistema"""
    
    # ============================================
    # SEGURANÇA
    # ============================================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    
    # ============================================
    # FIREBASE (Autenticação)
    # ============================================
    FIREBASE_ADMIN_SDK_PATH = os.environ.get(
        'FIREBASE_ADMIN_SDK_PATH', 
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'key.json')
    )
    
    # ============================================
    # BANCO DE DADOS
    # ============================================
    DATABASE_CONFIG = {
        "host": os.environ.get('DB_HOST', 'localhost'),
        "dbname": os.environ.get('DB_NAME', 'sistema_usuarios'),
        "user": os.environ.get('DB_USER', 'postgres'),
        "password": os.environ.get('DB_PASSWORD', 'far111111')
    }
    
    # ============================================
    # PAGBANK - GATEWAY DE PAGAMENTO
    # ============================================
    
    # Token de autenticação (obtido no painel do desenvolvedor PagBank)
    PAGBANK_API_TOKEN = os.environ.get(
        'PAGBANK_API_TOKEN', 
        '56db144e-54ab-4905-8c11-bcfbf040bee26ce79b14494f86bb8fe5af87bc0b53a0c020-c1fc-4a64-908a-dcd73ff498bc'
    )
    
    # URLs da API PagBank
    PAGBANK_SANDBOX_API_URL = "https://sandbox.api.pagseguro.com/orders"
    PAGBANK_PRODUCTION_API_URL = "https://api.pagseguro.com/orders"
    
    # Ambiente: 'sandbox' (desenvolvimento) ou 'production' (produção)
    PAGBANK_ENVIRONMENT = os.environ.get('PAGBANK_ENVIRONMENT', 'sandbox')
    
    # URL do Webhook - onde o PagBank enviará notificações de atualização de status
    # ⚠️ IMPORTANTE: Em produção, use HTTPS e URL pública acessível
    # Configure esta URL no painel do PagBank → Configurações → Webhooks
    PAGBANK_NOTIFICATION_URL = os.environ.get(
        'PAGBANK_NOTIFICATION_URL', 
        'https://efractory-burdenless-kathlene.ngrok-free.dev/api/webhook/pagbank'
    )
    
    # Modo de simulação: se True, não chama a API real do PagBank
    # Útil para desenvolvimento/testes sem token válido
    PAGBANK_SIMULATION_MODE = os.environ.get('PAGBANK_SIMULATION_MODE', 'true').lower() == 'false'
    
    # ============================================
    # MELHOR ENVIO - CÁLCULO DE FRETE
    # ============================================
    
    # Token da API Melhor Envio
    # Obter em: https://melhorenvio.com.br/app/cadastrar → Configurações > API Token
    MELHOR_ENVIO_TOKEN = os.environ.get(
        'MELHOR_ENVIO_TOKEN', 
        'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNjQxNGUzODUxODExYjE1MzQ1Y2I2ZGI1NzhkNmFiMTVmYjQyZTZlMGM5Zjk5YTI3ZDEyNmJjN2Q5YjA2MTI2MjZjYTRmZmIwYTVlMjczMjMiLCJpYXQiOjE3NjE5MzAwMDguMzQ5MTk3LCJuYmYiOjE3NjE5MzAwMDguMzQ5MzE5LCJleHAiOjE3OTM0NjYwMDguMzMyODA0LCJzdWIiOiJhYjJiYTIxZi1hNmJhLTQ1NjQtOWQzNS01YjI0YWVhNDU3NmEiLCJzY29wZXMiOlsiY2FydC1yZWFkIiwiY2FydC13cml0ZSIsImNvbXBhbmllcy1yZWFkIiwiY29tcGFuaWVzLXdyaXRlIiwiY291cG9ucy1yZWFkIiwiY291cG9ucy13cml0ZSIsIm5vdGlmaWNhdGlvbnMtcmVhZCIsIm9yZGVycy1yZWFkIiwicHJvZHVjdHMtcmVhZCIsInByb2R1Y3RzLWRlc3Ryb3kiLCJwcm9kdWN0cy13cml0ZSIsInB1cmNoYXNlcy1yZWFkIiwic2hpcHBpbmctY2FsY3VsYXRlIiwic2hpcHBpbmctY2FuY2VsIiwic2hpcHBpbmctY2hlY2tvdXQiLCJzaGlwcGluZy1jb21wYW5pZXMiLCJzaGlwcGluZy1nZW5lcmF0ZSIsInNoaXBwaW5nLXByZXZpZXciLCJzaGlwcGluZy1wcmludCIsInNoaXBwaW5nLXNoYXJlIiwic2hpcHBpbmctdHJhY2tpbmciLCJlY29tbWVyY2Utc2hpcHBpbmciLCJ0cmFuc2FjdGlvbnMtcmVhZCIsInVzZXJzLXJlYWQiLCJ1c2Vycy13cml0ZSIsIndlYmhvb2tzLXJlYWQiLCJ3ZWJob29rcy13cml0ZSIsIndlYmhvb2tzLWRlbGV0ZSIsInRkZWFsZXItd2ViaG9vayJdfQ.oeqekXWh-Z0T7thY23rCMLHrBbWWWUyx8miUMUEq8Kl3a3XG_dtfGNzmdvu-8mXgie6p7MBwsemCbvASZ_9mcVIZiMncPCkZIKN7H_5YJ3TTafsxilP9fpR6YzOYlJzV1FrjQrX-0j0BexVcd3AMeT51ozQ1elCxpYrKBaIPTpwtL1ctx9x0rNMiWlWaRMoWP0q3ZF2Z4NAFJd2yXBh0bomUfvsrk0eJDbKZg_Y29hXiunx-iJpYzWDEAVLCCnrBNnxeGeQmRBwTXLffzthxS-bot-XtLnR1jAukyE6XgtVaMOqhBYuhGjf8A7rIoHinjRlbh0_ABmx2Wcn8kgQyXUmY0HteURxUVqTgQcMwMjw6Xa6KkvVdbZDxhsDcdc_lAvLKVXKSh9DUOQySAWp9LZ3Xghk_wJCM5a0WzDs5tP2NiUpMl3OO2dXGJJJwNi_dI8mgdMd2bBA54m1I7FuqqrIkJFaQNZhAkloDEFxR2NK_ukyfxe43MzBi-_GG-JFi-A1NhIN8_QfwbK6WQvlJLUoFA4tk8PnEhOImm8dJoHUOR2GcT5Q1UOpV66sOYs1cKjA3TrDu17Kvuz7qOAzpvkwlGQ-dT4PpA5ng8YWSOXVUroE84sogIBvq4XfI6Izu1kOCRSG-qAVFaHtxAQMFUjeHOoLsaZOxhy93DTdpE-4'
    )
    
    # CEP de origem para cálculo de frete (formato: XXXXX-XXX)
    MELHOR_ENVIO_CEP_ORIGEM = os.environ.get('MELHOR_ENVIO_CEP_ORIGEM', '13219-052')
    
    # ============================================
    # ADMINISTRAÇÃO
    # ============================================
    
    # Lista de emails autorizados a acessar o painel administrativo
    # Configure via variável de ambiente: ADMIN_EMAILS=email1@exemplo.com,email2@exemplo.com
    _admin_emails_env = os.environ.get('ADMIN_EMAILS', '')
    ADMIN_EMAILS = (
        [email.strip() for email in _admin_emails_env.split(',') if email.strip()] 
        if _admin_emails_env 
        else ['joao.paulo.bussi1@gmail.com']
    )
