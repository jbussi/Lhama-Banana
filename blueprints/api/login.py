from . import api_bp
from flask import request, jsonify, session
from ..services.auth_service import verify_firebase_token, sync_user_from_firebase, check_admin_access, log_auth_event

@api_bp.route('/login_user', methods=["POST"])
def login_api():
    """
    Endpoint de login (mantido para compatibilidade).
    Redireciona para o novo endpoint /auth/login.
    """
    # Redirecionar para o novo endpoint
    from .auth import login
    return login()