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

from blueprints.services.db import init_db_pool, close_db_connection

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
        # PRIMEIRA OPÇÃO: Base64 (recomendado)
        firebase_base64 = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        
        if firebase_base64:
            try:
                import base64
                import json
                print(f"🔧 Inicializando Firebase via Base64 ({len(firebase_base64)} caracteres)...")
                
                # Decodifica Base64
                json_bytes = base64.b64decode(firebase_base64)
                json_str = json_bytes.decode('utf-8')
                
                # Carrega JSON
                cred_dict = json.loads(json_str)
                
                # Inicializa Firebase
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                
                print("✅ Firebase Admin SDK inicializado com sucesso via Base64!")
                _firebase_initialized = True
                
            except base64.binascii.Error as e:
                print(f"❌ ERRO: Base64 inválido: {e}")
            except json.JSONDecodeError as e:
                print(f"❌ ERRO: JSON inválido após decodificar Base64: {e}")
            except Exception as e:
                print(f"❌ ERRO: Falha ao inicializar Firebase com Base64: {e}")
        
        else:
            print("⚠️ AVISO: Nenhuma configuração do Firebase encontrada.")
            print("   Configurações verificadas: FIREBASE_JSON_BASE64, FIREBASE_SERVICE_ACCOUNT_JSON")
            print("   Firebase Admin SDK não será inicializado. Defina FIREBASE_SERVICE_ACCOUNT_JSON no .env para autenticação.")
            # Não encerrar o processo: permite subir o container para testes e configurar .env depois
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