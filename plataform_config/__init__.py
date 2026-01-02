"""
Inicialização de Serviços da Plataforma
=========================================
Gerencia a inicialização do Firebase, banco de dados e outros serviços.
"""

import os
import sys
from pathlib import Path
import firebase_admin
from firebase_admin import credentials
from flask import Flask

from blueprints import init_db_pool
from blueprints.services.db import close_db_connection

_db_pool_instance = None
_firebase_initialized = False


def init_app(app: Flask):
    """
    Inicializa os serviços da plataforma para a aplicação Flask.
    
    Args:
        app (Flask): A instância da aplicação Flask.
    """
    global _db_pool_instance, _firebase_initialized

    print("\n--- Iniciando configuração do Pacote Services ---")

    # --- 1. Inicialização do Firebase Admin SDK ---
    if not _firebase_initialized:
        firebase_key_path = app.config.get('FIREBASE_ADMIN_SDK_PATH')
        
        if not firebase_key_path:
            print("⚠️  ATENÇÃO: 'FIREBASE_ADMIN_SDK_PATH' não configurado. Firebase Admin SDK não será inicializado.")
        else:
            # Verificar se é arquivo (não diretório)
            firebase_path = Path(firebase_key_path)
            
            if not firebase_path.exists():
                print(f"⚠️  ATENÇÃO: Arquivo de credenciais do Firebase não encontrado em: {firebase_key_path}")
                print("   Firebase Admin SDK não será inicializado.")
                # Em desenvolvimento, continuar sem Firebase
                if not app.config.get('DEBUG', False):
                    print("   Encerrando aplicação (Firebase é obrigatório em produção)")
                    sys.exit(1)
            elif firebase_path.is_dir():
                print(f"⚠️  ATENÇÃO: O caminho especificado é um diretório, não um arquivo: {firebase_key_path}")
                print("   Tentando localizar key.json na raiz do workspace...")
                # Tentar encontrar o arquivo na raiz (subindo dois níveis: /app -> Lhama-Banana -> raiz)
                # No Docker, /app é Lhama-Banana, então /app/.. seria a raiz
                root_key = Path('/app/../key.json').resolve()
                if root_key.exists() and root_key.is_file():
                    firebase_path = root_key
                    print(f"   ✅ Arquivo encontrado em: {firebase_path}")
                else:
                    print(f"   ❌ Arquivo key.json não encontrado na raiz do workspace")
                    if not app.config.get('DEBUG', False):
                        sys.exit(1)
                    return  # Em desenvolvimento, continuar sem Firebase
            
            # Se chegou aqui, temos um arquivo válido (ou encontramos na raiz)
            if firebase_path.exists() and firebase_path.is_file():
                try:
                    if not firebase_admin._apps:
                        cred = credentials.Certificate(str(firebase_path))
                        firebase_admin.initialize_app(cred)
                        print("✅ Firebase Admin SDK inicializado com sucesso!")
                        _firebase_initialized = True
                    else:
                        print("ℹ️  Firebase Admin SDK já está inicializado.")
                except Exception as e:
                    print(f"❌ ERRO FATAL: Falha ao inicializar Firebase Admin SDK: {e}")
                    # Em desenvolvimento, apenas avisar
                    if app.config.get('DEBUG', False):
                        print("   Continuando em modo de desenvolvimento sem Firebase...")
                    else:
                        print("   Encerrando aplicação (Firebase é obrigatório em produção)")
                        sys.exit(1)
            else:
                print(f"⚠️  Arquivo key.json não encontrado ou inválido em: {firebase_path}")
                if not app.config.get('DEBUG', False):
                    sys.exit(1)
    else:
        print("ℹ️  Firebase Admin SDK já está inicializado (pulando inicialização redundante).")

    # --- 2. Inicialização do Pool de Conexões de Banco de Dados ---
    db_config = app.config.get('DATABASE_CONFIG', {})
    
    if not db_config:
        print("⚠️  ATENÇÃO: 'DATABASE_CONFIG' não encontrado. Pool de conexões não será inicializado.")
    else:
        try:
            init_db_pool(db_config)
            print("✅ Pool de conexões DB inicializado com sucesso!")
            
            # Registrar teardown para fechar conexões automaticamente
            app.teardown_appcontext(close_db_connection)
            print("✅ Teardown de conexões DB registrado com sucesso!")
        except Exception as e:
            print(f"⚠️  ATENÇÃO: Falha ao inicializar Pool de Conexões DB: {e}")
            
            # Em desenvolvimento, não encerrar a aplicação se o banco não estiver disponível
            is_debug = app.config.get('DEBUG', False)
            if not is_debug:
                print("❌ ERRO FATAL: Banco de dados é obrigatório em produção")
                sys.exit(1)
            else:
                print("   Continuando em modo de desenvolvimento sem banco de dados...")
    
    print("--- Configuração do Pacote Services concluída ---\n")
