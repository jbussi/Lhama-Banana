from functools import wraps
from flask import g, abort, current_app, session
from ..services.user_service import get_user_by_firebase_uid

def admin_required_email(f):
    """
    Decorador que verifica se o usuário está logado E se o email está na lista de admins.
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
        user_role = user_data.get('role', 'user')
        user_email = user_data.get('email', '').lower()
        
        # Lista de emails autorizados (configurável)
        admin_emails = current_app.config.get('ADMIN_EMAILS', [])
        
        # Log para debug (remover em produção se necessário)
        current_app.logger.info(f"[Admin] Verificando acesso - Email: {user_email}, Role: {user_role}, Admin emails: {admin_emails}")
        
        # Verificar se o email está na lista de admins OU se tem role admin no banco
        is_admin_email = user_email in [email.lower() for email in admin_emails] if admin_emails else False
        is_admin_role = user_role == 'admin'
        
        if not (is_admin_email or is_admin_role):
            current_app.logger.warning(f"[Admin] Acesso negado - Email: {user_email}, Role: {user_role}, Admin emails configurados: {admin_emails}")
            # Retorna 404 ao invés de 403 para não revelar existência da área admin
            abort(404)
        
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

