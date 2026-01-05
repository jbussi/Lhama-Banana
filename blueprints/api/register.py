from . import api_bp
from flask import request, jsonify
from ..services.auth_service import verify_firebase_token, sync_user_from_firebase, log_auth_event

@api_bp.route('/register_user', methods=["POST"])
def register_api():
    """
    Endpoint de registro (mantido para compatibilidade).
    Redireciona para o novo endpoint /auth/register.
    """
    # Redirecionar para o novo endpoint
    from .auth import register
    return register()