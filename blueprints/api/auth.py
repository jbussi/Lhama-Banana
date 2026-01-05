"""
Endpoints de Autenticação Expandidos
====================================
Endpoints para login Google, verificação de email, recuperação de senha, etc.
"""

from . import api_bp
from flask import request, jsonify, session, g, current_app
from firebase_admin import auth
from ..services.auth_service import (
    verify_firebase_token,
    sync_user_from_firebase,
    check_admin_access,
    require_email_verified,
    log_auth_event,
    get_email_verification_link,
    get_password_reset_link,
    generate_mfa_secret,
    verify_totp_code,
    enable_mfa_for_user,
    disable_mfa_for_user,
    is_mfa_enabled,
    get_mfa_status
)
from flask import session
from ..services.user_service import get_user_by_firebase_uid
import logging
import traceback

logger = logging.getLogger(__name__)


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Login via email/senha ou Google.
    O frontend já autenticou no Firebase, apenas validamos o token.
    """
    data = request.get_json()
    if not data:
        current_app.logger.warning("Requisição sem dados JSON")
        return jsonify({"erro": "Dados não recebidos"}), 400
    
    id_token = data.get('id_token')
    
    if not id_token:
        current_app.logger.warning("Token não fornecido na requisição")
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    # Verificar token Firebase
    try:
        # Verificar se Firebase Admin está inicializado
        try:
            import firebase_admin
            if not firebase_admin._apps:
                current_app.logger.error("Firebase Admin SDK não está inicializado")
                return jsonify({"erro": "Serviço de autenticação não disponível. Contate o administrador."}), 503
            # Verificar se podemos acessar o app
            firebase_admin.get_app()
        except Exception as fb_init_error:
            current_app.logger.error(f"Firebase Admin SDK não está inicializado: {fb_init_error}")
            return jsonify({"erro": "Serviço de autenticação não disponível. Contate o administrador."}), 503
        
        # Verificar token com retry
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            # Log mais detalhado para debug
            current_app.logger.warning(f"Token inválido ou não pôde ser verificado. Token length: {len(id_token) if id_token else 0}")
            if id_token:
                current_app.logger.warning(f"Primeiros 50 chars do token: {id_token[:50]}...")
                current_app.logger.warning(f"Últimos 50 chars do token: ...{id_token[-50:]}")
            log_auth_event('login', 'unknown', False, "Token inválido ou não verificado")
            return jsonify({"erro": "Token inválido ou expirado. Tente fazer login novamente."}), 401
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar token: {e}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        log_auth_event('login', 'unknown', False, f"Erro na verificação: {str(e)}")
        return jsonify({"erro": "Erro ao processar autenticação. Tente novamente."}), 500
    
    uid = decoded_token['uid']
    email_verified = decoded_token.get('email_verified', False)
    
    # Sincronizar usuário com banco local
    user_data, is_new_user = sync_user_from_firebase(decoded_token)
    
    if not user_data:
        log_auth_event('login', uid, False, "Erro ao sincronizar usuário")
        return jsonify({"erro": "Erro ao processar login"}), 500
    
    # Verificar se email está verificado (obrigatório para admin)
    is_admin = check_admin_access(user_data)
    if is_admin and not email_verified:
        log_auth_event('login', uid, False, "Admin sem email verificado")
        return jsonify({
            "erro": "Email não verificado",
            "email_verificado": False,
            "requer_verificacao": True
        }), 403
    
    # Verificar se 2FA está habilitado (apenas para admins)
    mfa_required = False
    mfa_enabled = is_mfa_enabled(user_data)
    logger.info(f"[LOGIN] Admin: {is_admin}, MFA Enabled: {mfa_enabled}, User Data MFA: {user_data.get('mfa_enabled')}, Has Secret: {bool(user_data.get('mfa_secret'))}")
    
    if is_admin and mfa_enabled:
        mfa_required = True
        # Não marcar como verificado ainda - precisa verificar código 2FA
        session['uid'] = uid
        session['mfa_verified'] = False
        session['mfa_verified_uid'] = None
        
        ip_address = request.remote_addr
        log_auth_event('login', uid, True, f"Login iniciado - 2FA necessário para {user_data.get('email')}", ip_address)
        
        return jsonify({
            "mensagem": "Login iniciado. Verificação 2FA necessária.",
            "requer_mfa": True,
            "usuario": {
                "uid": uid,
                "email": user_data.get('email'),
                "nome": user_data.get('nome'),
                "email_verificado": email_verified,
                "role": user_data.get('role', 'user')
            }
        }), 200
    
    # Login bem-sucedido (sem 2FA ou não é admin)
    session['uid'] = uid
    if is_admin:
        session['mfa_verified'] = True  # Admin sem 2FA habilitado
        session['mfa_verified_uid'] = uid
    else:
        session['mfa_verified'] = False  # Usuário comum não precisa
        session['mfa_verified_uid'] = None
    
    ip_address = request.remote_addr
    log_auth_event('login', uid, True, f"Email: {user_data.get('email')}", ip_address)
    
    return jsonify({
        "mensagem": "Login efetuado com sucesso",
        "requer_mfa": False,
        "usuario": {
            "uid": uid,
            "email": user_data.get('email'),
            "nome": user_data.get('nome'),
            "email_verificado": email_verified,
            "role": user_data.get('role', 'user')
        }
    }), 200


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """
    Registro de novo usuário.
    O frontend já criou a conta no Firebase, apenas sincronizamos com o banco.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    username = data.get('username')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    if not username:
        return jsonify({"erro": "Nome de usuário é obrigatório"}), 400
    
    # Verificar token Firebase
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido ou expirado"}), 401
    
    uid = decoded_token['uid']
    email_verified = decoded_token.get('email_verified', False)
    
    # Verificar se usuário já existe
    existing_user = get_user_by_firebase_uid(uid)
    if existing_user:
        return jsonify({"erro": "Usuário já cadastrado"}), 400
    
    # Sincronizar usuário (criar no banco)
    user_data, is_new_user = sync_user_from_firebase(decoded_token)
    
    if not user_data or not is_new_user:
        log_auth_event('register', uid, False, "Erro ao criar usuário")
        return jsonify({"erro": "Erro ao criar conta"}), 500
    
    # Atualizar nome se fornecido
    if username and username != user_data.get('nome'):
        from ..services.user_service import update_user_profile_db
        update_user_profile_db(user_data['id'], {'nome': username})
        user_data['nome'] = username
    
    ip_address = request.remote_addr
    log_auth_event('register', uid, True, f"Email: {user_data.get('email')}", ip_address)
    
    # Notificar administradores sobre novo usuário
    from ..services.email_service import send_new_user_notification
    send_new_user_notification(user_data.get('email'), user_data.get('nome'))
    
    return jsonify({
        "mensagem": "Conta criada com sucesso",
        "usuario": {
            "uid": uid,
            "email": user_data.get('email'),
            "nome": user_data.get('nome'),
            "email_verificado": email_verified
        },
        "requer_verificacao": not email_verified
    }), 200


@api_bp.route('/auth/verify-email-status', methods=['POST'])
def verify_email_status():
    """
    Verifica o status de verificação de email do usuário.
    Útil para revalidar após o usuário verificar o email.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    email_verified = decoded_token.get('email_verified', False)
    
    # Sincronizar status com banco
    user_data, _ = sync_user_from_firebase(decoded_token)
    
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    return jsonify({
        "email_verificado": email_verified,
        "usuario": {
            "uid": uid,
            "email": user_data.get('email'),
            "email_verificado": email_verified
        }
    }), 200


@api_bp.route('/auth/resend-verification', methods=['POST'])
def resend_verification():
    """
    Endpoint para reenviar email de verificação.
    O Firebase envia o email automaticamente quando o cliente chama sendEmailVerification().
    Este endpoint apenas valida o token e retorna sucesso.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    email = decoded_token.get('email')
    email_verified = decoded_token.get('email_verified', False)
    
    # Se já está verificado, não precisa reenviar
    if email_verified:
        return jsonify({
            "mensagem": "Email já está verificado",
            "email_verificado": True
        }), 200
    
    # Sincronizar com banco
    user_data, _ = sync_user_from_firebase(decoded_token)
    
    logger.info(f"Solicitação de reenvio de verificação para UID: {uid}, Email: {email}")
    
    # O Firebase envia o email automaticamente quando o cliente chama sendEmailVerification()
    # Este endpoint apenas confirma que a solicitação foi recebida
    return jsonify({
        "mensagem": "Email de verificação será enviado. Verifique sua caixa de entrada.",
        "email": email,
        "instrucoes": "O email será enviado automaticamente pelo Firebase. Verifique também a pasta de spam."
    }), 200


@api_bp.route('/auth/password-reset', methods=['POST'])
def password_reset():
    """
    Endpoint para solicitar recuperação de senha (esqueci minha senha).
    O Firebase envia o email automaticamente quando o cliente chama sendPasswordResetEmail().
    Este endpoint apenas valida e retorna sucesso.
    """
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"erro": "Email é obrigatório"}), 400
    
    logger.info(f"Solicitação de recuperação de senha para: {email}")
    
    # O Firebase envia o email automaticamente quando o cliente chama sendPasswordResetEmail()
    # Este endpoint apenas confirma que a solicitação foi recebida
    return jsonify({
        "mensagem": "Email de recuperação de senha será enviado. Verifique sua caixa de entrada.",
        "email": email,
        "instrucoes": "O email será enviado automaticamente pelo Firebase. Verifique também a pasta de spam."
    }), 200


@api_bp.route('/auth/change-password', methods=['POST'])
def change_password():
    """
    Endpoint para alteração de senha (usuário logado).
    Requer senha atual e nova senha.
    O Firebase faz a alteração, este endpoint apenas valida e sincroniza.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    if not current_password or not new_password:
        return jsonify({"erro": "Senha atual e nova senha são obrigatórias"}), 400
    
    if len(new_password) < 6:
        return jsonify({"erro": "A nova senha deve ter pelo menos 6 caracteres"}), 400
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    email = decoded_token.get('email')
    
    # Buscar dados do usuário
    user_data = get_user_by_firebase_uid(uid)
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    # Nota: A alteração de senha é feita no Firebase pelo cliente usando updatePassword()
    # Este endpoint apenas valida o token e registra o evento
    logger.info(f"Solicitação de alteração de senha para UID: {uid}, Email: {email}")
    log_auth_event('change_password', uid, True, f"Alteração de senha solicitada para: {email}", request.remote_addr)
    
    return jsonify({
        "mensagem": "Alteração de senha processada com sucesso",
        "instrucoes": "A senha foi alterada no Firebase. Use updatePassword() no cliente para confirmar."
    }), 200


@api_bp.route('/auth/check-admin', methods=['POST'])
def check_admin():
    """
    Verifica se o usuário tem permissões de administrador.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    email_verified = decoded_token.get('email_verified', False)
    
    # Buscar dados do usuário
    user_data = get_user_by_firebase_uid(uid)
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    # Verificar acesso admin
    is_admin = check_admin_access(user_data)
    
    # Verificar email verificado (obrigatório para admin)
    if is_admin and not email_verified:
        return jsonify({
            "is_admin": False,
            "requer_verificacao": True,
            "erro": "Email não verificado. Administradores devem verificar o email."
        }), 403
    
    return jsonify({
        "is_admin": is_admin,
        "email_verificado": email_verified,
        "usuario": {
            "uid": uid,
            "email": user_data.get('email'),
            "role": user_data.get('role', 'user')
        }
    }), 200


# =====================================================
# MULTI-FACTOR AUTHENTICATION (2FA) - ENDPOINTS
# =====================================================

@api_bp.route('/auth/mfa/setup', methods=['POST'])
def mfa_setup():
    """
    Gera secret e QR code para configurar 2FA.
    Apenas para administradores.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    email_verified = decoded_token.get('email_verified', False)
    
    # Sincronizar usuário com banco local (importante para atualizar email_verificado)
    user_data, _ = sync_user_from_firebase(decoded_token)
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado ou erro ao sincronizar"}), 404
    
    # Verificar se é admin
    if not check_admin_access(user_data):
        return jsonify({"erro": "Apenas administradores podem habilitar 2FA"}), 403
    
    # Verificar se email está verificado (usar dados do token Firebase como fonte de verdade)
    # Para usuários do Google OAuth, o email sempre vem verificado
    if not email_verified:
        # Se não estiver verificado no token, verificar no banco também
        is_verified, error_msg = require_email_verified(user_data)
        if not is_verified:
            return jsonify({"erro": error_msg}), 403
    
    # Verificar se 2FA já está habilitado
    if is_mfa_enabled(user_data):
        return jsonify({"erro": "2FA já está habilitado. Desabilite primeiro para reconfigurar."}), 400
    
    # Gerar secret e QR code
    try:
        secret, qr_code_base64 = generate_mfa_secret(user_data.get('email'), user_data.get('id'))
        
        # Salvar secret temporariamente (não habilitar ainda - precisa verificar código primeiro)
        # Por enquanto, retornamos o secret para o frontend validar
        # O frontend deve chamar /auth/mfa/enable após verificar o código
        
        return jsonify({
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_base64}",
            "manual_entry_key": secret,
            "instrucoes": "Escaneie o QR code com um app autenticador (Google Authenticator, Authy, etc.) ou digite a chave manualmente."
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar secret 2FA: {e}")
        return jsonify({"erro": "Erro ao gerar configuração 2FA"}), 500


@api_bp.route('/auth/mfa/enable', methods=['POST'])
def mfa_enable():
    """
    Habilita 2FA após verificar o código.
    Apenas para administradores.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    secret = data.get('secret')
    code = data.get('code')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    if not secret or not code:
        return jsonify({"erro": "Secret e código são obrigatórios"}), 400
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    email_verified = decoded_token.get('email_verified', False)
    
    # Sincronizar usuário com banco local
    user_data, _ = sync_user_from_firebase(decoded_token)
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado ou erro ao sincronizar"}), 404
    
    # Verificar se é admin
    if not check_admin_access(user_data):
        return jsonify({"erro": "Apenas administradores podem habilitar 2FA"}), 403
    
    # Verificar se email está verificado
    if not email_verified:
        is_verified, error_msg = require_email_verified(user_data)
        if not is_verified:
            return jsonify({"erro": error_msg}), 403
    
    # Verificar código TOTP
    if not verify_totp_code(secret, code):
        log_auth_event('mfa_enable', uid, False, "Código 2FA inválido", request.remote_addr)
        return jsonify({"erro": "Código inválido. Verifique o código de 6 dígitos do seu app autenticador."}), 400
    
    # Habilitar 2FA
    if enable_mfa_for_user(user_data.get('id'), secret):
        log_auth_event('mfa_enable', uid, True, f"2FA habilitado para {user_data.get('email')}", request.remote_addr)
        return jsonify({
            "mensagem": "2FA habilitado com sucesso!",
            "mfa_enabled": True
        }), 200
    else:
        return jsonify({"erro": "Erro ao habilitar 2FA"}), 500


@api_bp.route('/auth/mfa/verify', methods=['POST'])
def mfa_verify():
    """
    Verifica código 2FA durante o login.
    Usado quando admin com 2FA habilitado faz login.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    code = data.get('code')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    if not code:
        return jsonify({"erro": "Código 2FA é obrigatório"}), 400
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    
    # Buscar dados do usuário
    user_data = get_user_by_firebase_uid(uid)
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    # Verificar se 2FA está habilitado
    if not is_mfa_enabled(user_data):
        return jsonify({"erro": "2FA não está habilitado para este usuário"}), 400
    
    # Verificar código TOTP
    mfa_secret = user_data.get('mfa_secret')
    if not mfa_secret:
        return jsonify({"erro": "Secret 2FA não encontrado"}), 500
    
    if verify_totp_code(mfa_secret, code):
        # Marcar 2FA como verificado na sessão
        session['mfa_verified'] = True
        session['mfa_verified_uid'] = uid
        session['uid'] = uid  # Garantir que uid está na sessão
        
        log_auth_event('mfa_verify', uid, True, f"2FA verificado para {user_data.get('email')}", request.remote_addr)
        return jsonify({
            "mensagem": "Código 2FA verificado com sucesso",
            "mfa_verified": True,
            "login_completo": True
        }), 200
    else:
        log_auth_event('mfa_verify', uid, False, f"2FA falhou para {user_data.get('email')}", request.remote_addr)
        return jsonify({"erro": "Código 2FA inválido"}), 400


@api_bp.route('/auth/mfa/disable', methods=['POST'])
def mfa_disable():
    """
    Desabilita 2FA.
    Apenas para administradores.
    Requer código 2FA para confirmar.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    code = data.get('code')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    if not code:
        return jsonify({"erro": "Código 2FA é obrigatório para desabilitar"}), 400
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    email_verified = decoded_token.get('email_verified', False)
    
    # Sincronizar usuário com banco local
    user_data, _ = sync_user_from_firebase(decoded_token)
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado ou erro ao sincronizar"}), 404
    
    # Verificar se é admin
    if not check_admin_access(user_data):
        return jsonify({"erro": "Apenas administradores podem desabilitar 2FA"}), 403
    
    # Verificar se email está verificado
    if not email_verified:
        is_verified, error_msg = require_email_verified(user_data)
        if not is_verified:
            return jsonify({"erro": error_msg}), 403
    
    # Verificar se 2FA está habilitado
    if not is_mfa_enabled(user_data):
        return jsonify({"erro": "2FA não está habilitado"}), 400
    
    # Verificar código TOTP antes de desabilitar
    mfa_secret = user_data.get('mfa_secret')
    if not verify_totp_code(mfa_secret, code):
        log_auth_event('mfa_disable', uid, False, "Código 2FA inválido ao tentar desabilitar", request.remote_addr)
        return jsonify({"erro": "Código 2FA inválido"}), 400
    
    # Desabilitar 2FA
    if disable_mfa_for_user(user_data.get('id')):
        log_auth_event('mfa_disable', uid, True, f"2FA desabilitado para {user_data.get('email')}", request.remote_addr)
        return jsonify({
            "mensagem": "2FA desabilitado com sucesso",
            "mfa_enabled": False
        }), 200
    else:
        return jsonify({"erro": "Erro ao desabilitar 2FA"}), 500


@api_bp.route('/auth/mfa/status', methods=['POST'])
def mfa_status():
    """
    Retorna o status de 2FA do usuário.
    """
    data = request.get_json()
    id_token = data.get('id_token')
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    # Verificar token
    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"erro": "Token inválido"}), 401
    
    uid = decoded_token['uid']
    
    # Buscar dados do usuário
    user_data = get_user_by_firebase_uid(uid)
    if not user_data:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    
    mfa_status = get_mfa_status(user_data)
    
    return jsonify({
        "mfa_enabled": mfa_status['enabled'],
        "has_secret": mfa_status['has_secret'],
        "is_admin": check_admin_access(user_data)
    }), 200

