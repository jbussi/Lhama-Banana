#!/usr/bin/env python3
"""
Testa busca da situação ID 6 do Bling
"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_api_service import get_valid_access_token, make_bling_api_request
from blueprints.services.bling_situacao_service import get_bling_situacao_by_id

app = Flask(__name__)
app.config.from_object('config.Config')

init_db_pool(app.config['DATABASE_CONFIG'])

with app.app_context():
    print("Testando situação ID 6...")
    
    try:
        token = get_valid_access_token()
        print(f"Token: {token[:20]}...")
        
        # Buscar situação ID 6
        print("\nBuscando situação ID 6...")
        situacao = get_bling_situacao_by_id(6)
        
        if situacao:
            print(f"✅ Encontrada: {situacao}")
        else:
            print("❌ Não encontrada")
            
            # Tentar requisição direta
            print("\nTentando requisição direta...")
            response = make_bling_api_request('GET', '/situacoes/6')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
