from functools import wraps
from flask import g, abort, current_app, session, request
from ..services.user_service import get_user_by_firebase_uid
from ..services.auth_service import check_admin_access, require_email_verified, verify_firebase_token, is_mfa_enabled

def admin_required_email(f):
    """
    Decorador que verifica se o usuário está logado, se o email está na lista de admins,
    e se o email está verificado (obrigatório para administradores).
    Retorna 404 para emails não autorizados ou não logados (para não revelar existência da área admin).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se o usuário está logado (sem redirecionar para login)
        uid = session.get('uid')
        if not uid:
            # Retorna 404 ao invés de redirect para não revelar área admin
            current_app.logger.warning("[Admin] Usuário não logado - retornando 404")
            abort(404)
        
        # Buscar dados do usuário
        user_data = get_user_by_firebase_uid(uid)
        if not user_data:
            # Limpa sessão se usuário não existe no DB e retorna 404
            session.pop('uid', None)
            current_app.logger.warning("[Admin] Usuário não encontrado no DB - retornando 404")
            abort(404)
        
        # Armazenar em g.user
        g.user = user_data
        g.user_db_data = user_data
        
        # Verificar permissões de admin
        is_admin = check_admin_access(user_data)
        if not is_admin:
            user_email = user_data.get('email', '').lower()
            current_app.logger.warning(f"[Admin] Acesso negado - Email: {user_email}, Role: {user_data.get('role', 'user')}")
            abort(404)
        
        # Verificar se email está verificado (obrigatório para admin)
        email_verified, error_msg = require_email_verified(user_data)
        if not email_verified:
            current_app.logger.warning(f"[Admin] Email não verificado - Email: {user_data.get('email')}")
            # Retorna 403 com mensagem clara sobre necessidade de verificação
            abort(403, description="Email não verificado. Verifique seu email antes de acessar a área administrativa.")
        
        # Verificar 2FA se estiver habilitado
        if is_mfa_enabled(user_data):
            mfa_verified = session.get('mfa_verified', False)
            mfa_verified_uid = session.get('mfa_verified_uid')
            
            # Verificar se 2FA foi verificado para este usuário específico
            if not mfa_verified or mfa_verified_uid != uid:
                current_app.logger.warning(f"[Admin] 2FA não verificado - Email: {user_data.get('email')}, UID: {uid}")
                abort(403, description="Verificação em duas etapas (2FA) é obrigatória. Por favor, verifique seu código 2FA.")
        
        return f(*args, **kwargs)
    
    return decorated_function

def admin_role_required(f):
    """
    Decorador que verifica apenas se o usuário tem role 'admin' no banco.
    Usado para endpoints internos que já verificaram email.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se o usuário está logado (sem redirecionar para login)
        uid = session.get('uid')
        if not uid:
            abort(404)
        
        # Buscar dados do usuário
        user_data = get_user_by_firebase_uid(uid)
        if not user_data:
            session.pop('uid', None)
            abort(404)
        
        # Armazenar em g.user
        g.user = user_data
        g.user_db_data = user_data
        
        # Verificar role
        if user_data.get('role') != 'admin':
            abort(404)
        
        return f(*args, **kwargs)
    
    return decorated_function

