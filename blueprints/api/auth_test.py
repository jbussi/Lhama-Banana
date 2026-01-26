"""
Endpoint de teste para debug de autenticação
Apenas para desenvolvimento - remover em produção
"""

from . import api_bp
from flask import request, jsonify, current_app
from firebase_admin import auth
import logging
import time
import datetime
import base64
import json

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


@api_bp.route('/auth/diagnose-clock', methods=['GET', 'POST'])
def diagnose_clock():
    """
    Diagnóstico completo de relógio e token.
    Compara tempo do servidor com NTP e analisa token se fornecido.
    """
    if current_app.config.get('ENV') == 'production':
        return jsonify({"erro": "Endpoint desabilitado em produção"}), 403
    
    result = {
        "server_time": {
            "unix_timestamp": int(time.time()),
            "iso_format": datetime.datetime.now().isoformat(),
            "readable": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        "ntp_sync": None,
        "token_analysis": None,
        "clock_skew_detected": False
    }
    
    # Tentar verificar sincronização NTP
    try:
        import ntplib
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org', version=3, timeout=5)
        ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
        server_time = datetime.datetime.now()
        time_diff = abs((ntp_time - server_time).total_seconds())
        
        result["ntp_sync"] = {
            "synced": time_diff < 5,  # Considera sincronizado se diferença < 5s
            "time_diff_seconds": round(time_diff, 2),
            "ntp_time": ntp_time.isoformat(),
            "server_time": server_time.isoformat(),
            "message": "Sincronizado" if time_diff < 5 else f"Desincronizado ({time_diff:.2f}s)"
        }
    except ImportError:
        result["ntp_sync"] = {
            "synced": None,
            "error": "ntplib não instalado",
            "message": "Instale com: pip install ntplib"
        }
    except Exception as e:
        result["ntp_sync"] = {
            "synced": None,
            "error": str(e),
            "message": "Não foi possível verificar NTP"
        }
    
    # Se recebeu token, analisar
    if request.method == 'POST':
        data = request.get_json()
        id_token = data.get('id_token') if data else None
        
        if id_token:
            try:
                # Decodificar token sem verificar (para ver os claims)
                # JWT tem 3 partes separadas por ponto
                parts = id_token.split('.')
                if len(parts) >= 2:
                    # Decodificar payload (segunda parte)
                    payload = parts[1]
                    # Adicionar padding se necessário
                    padding = 4 - len(payload) % 4
                    if padding != 4:
                        payload += '=' * padding
                    
                    decoded_payload = json.loads(base64.urlsafe_b64decode(payload))
                    
                    # Extrair timestamps
                    iat = decoded_payload.get('iat')  # Issued at
                    exp = decoded_payload.get('exp')  # Expiration
                    nbf = decoded_payload.get('nbf')  # Not before
                    auth_time = decoded_payload.get('auth_time')
                    
                    server_now = int(time.time())
                    
                    # Calcular diferenças
                    if iat:
                        iat_diff = server_now - iat
                        result["clock_skew_detected"] = abs(iat_diff) > 5
                    
                    token_info = {
                        "iat": {
                            "timestamp": iat,
                            "readable": datetime.datetime.fromtimestamp(iat).isoformat() if iat else None,
                            "diff_from_server": server_now - iat if iat else None
                        },
                        "nbf": {
                            "timestamp": nbf,
                            "readable": datetime.datetime.fromtimestamp(nbf).isoformat() if nbf else None,
                            "diff_from_server": server_now - nbf if nbf else None
                        },
                        "exp": {
                            "timestamp": exp,
                            "readable": datetime.datetime.fromtimestamp(exp).isoformat() if exp else None,
                            "seconds_until_expiry": exp - server_now if exp else None,
                            "is_expired": exp < server_now if exp else None
                        },
                        "auth_time": {
                            "timestamp": auth_time,
                            "readable": datetime.datetime.fromtimestamp(auth_time).isoformat() if auth_time else None
                        },
                        "server_now": {
                            "timestamp": server_now,
                            "readable": datetime.datetime.fromtimestamp(server_now).isoformat()
                        },
                        "token_validity_seconds": exp - iat if (exp and iat) else None,
                        "is_valid_now": (nbf or iat) <= server_now < exp if (exp and (nbf or iat)) else None
                    }
                    
                    result["token_analysis"] = token_info
                    
                    # Verificar se token é válido
                    if iat and server_now < iat:
                        result["clock_skew_detected"] = True
                        result["error"] = f"Token emitido no futuro! Diferença: {iat - server_now}s"
                    elif nbf and server_now < nbf:
                        result["clock_skew_detected"] = True
                        result["error"] = f"Token ainda não é válido (nbf)! Diferença: {nbf - server_now}s"
                    elif exp and server_now >= exp:
                        result["error"] = "Token expirado"
                    
            except Exception as e:
                result["token_analysis"] = {
                    "error": f"Erro ao decodificar token: {str(e)}"
                }
    
    return jsonify(result), 200