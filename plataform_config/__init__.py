import os
import sys 
import firebase_admin
from firebase_admin import credentials 
from flask import g, Flask 

from blueprints import init_db_pool

_db_pool_instance = None
_firebase_initialized = False 

def init_app(app: Flask):
    """
    Inicializa o pacote de serviços para a aplicação Flask.
    Esta função deve ser chamada uma única vez durante a criação do app.

    Args:
        app (Flask): A instância da aplicação Flask.
    """
    global _db_pool_instance, _firebase_initialized

    print("\n--- Iniciando configuração do Pacote Services ---")

    # --- 1. Inicialização do Firebase Admin SDK ---
    if not _firebase_initialized:
        SERVICE_ACCOUNT_KEY_PATH = app.config.get('FIREBASE_ADMIN_SDK_PATH')
        if not SERVICE_ACCOUNT_KEY_PATH:
            print("ATENÇÃO: 'FIREBASE_ADMIN_SDK_PATH' não configurado em app.config. Firebase Admin SDK não será inicializado.")
        elif not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            print(f"ATENÇÃO: Arquivo de credenciais do Firebase Admin SDK não encontrado em: {SERVICE_ACCOUNT_KEY_PATH}. Firebase Admin SDK não será inicializado.")
        else:
            try:
                if not firebase_admin._apps:
                    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
                    firebase_admin.initialize_app(cred)
                    print("Firebase Admin SDK inicializado COM SUCESSO!")
                    _firebase_initialized = True
            except Exception as e:
                print(f"ERRO FATAL: Falha ao inicializar Firebase Admin SDK: {e}")
                sys.exit(1)
    else:
        print("Firebase Admin SDK já está inicializado (pulando inicialização redundante).")

    # --- 2. Inicialização do Pool de Conexões de Banco de Dados ---
    db_config = app.config.get('DATABASE_CONFIG', {}) 
    try:
        init_db_pool(db_config)
        print("Pool de conexões DB inicializado COM SUCESSO!")
    except Exception as e:
        print(f"ERRO FATAL: Falha ao inicializar Pool de Conexões DB: {e}")
        sys.exit(1) 