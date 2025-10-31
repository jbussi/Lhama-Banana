from . import auth_bp
from flask import session, redirect, url_for

@auth_bp.route('/logout')
def logout():
    session.pop('uid', None) # Remove o ID do usuário da sessão
    return redirect(url_for('auth.login_page'))