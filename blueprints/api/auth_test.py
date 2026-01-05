"""
Endpoint de teste para debug de autenticação
Apenas para desenvolvimento - remover em produção
"""

from . import api_bp
from flask import request, jsonify, current_app
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)


@api_bp.route('/auth/test-token', methods=['POST'])
def test_token():
    """
    Endpoint de teste para verificar se o token está sendo processado corretamente.
    APENAS PARA DESENVOLVIMENTO - REMOVER EM PRODUÇÃO
    """
    if current_app.config.get('ENV') == 'production':
        return jsonify({"erro": "Endpoint desabilitado em produção"}), 403
    
    data = request.get_json()
    id_token = data.get('id_token') if data else None
    
    result = {
        "token_recebido": bool(id_token),
        "token_length": len(id_token) if id_token else 0,
        "firebase_inicializado": False,
        "token_valido": False,
        "erro": None,
        "decoded_token": None
    }
    
    try:
        # Verificar se Firebase está inicializado
        import firebase_admin
        if firebase_admin._apps:
            result["firebase_inicializado"] = True
            app = firebase_admin.get_app()
            result["firebase_app_name"] = app.name
        else:
            result["erro"] = "Firebase Admin SDK não está inicializado"
            return jsonify(result), 500
        
        # Tentar verificar o token
        if id_token:
            try:
                decoded_token = auth.verify_id_token(id_token, check_revoked=False)
                result["token_valido"] = True
                result["decoded_token"] = {
                    "uid": decoded_token.get('uid'),
                    "email": decoded_token.get('email'),
                    "email_verified": decoded_token.get('email_verified'),
                    "name": decoded_token.get('name'),
                    "firebase": decoded_token.get('firebase', {}),
                    "auth_time": decoded_token.get('auth_time'),
                    "iat": decoded_token.get('iat'),
                    "exp": decoded_token.get('exp')
                }
            except auth.InvalidIdTokenError as e:
                result["erro"] = f"Token inválido: {str(e)}"
            except auth.ExpiredIdTokenError as e:
                result["erro"] = f"Token expirado: {str(e)}"
            except Exception as e:
                result["erro"] = f"Erro ao verificar token: {type(e).__name__}: {str(e)}"
        else:
            result["erro"] = "Token não fornecido"
    
    except Exception as e:
        result["erro"] = f"Erro geral: {type(e).__name__}: {str(e)}"
        logger.error(f"Erro no teste de token: {e}", exc_info=True)
    
    return jsonify(result), 200 if result["token_valido"] else 400


