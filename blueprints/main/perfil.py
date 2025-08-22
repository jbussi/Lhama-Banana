from flask import session, render_template
from . import main_bp
from ..services import login_required_and_load_user

@main_bp.route('/perfil', methods=["GET"])
@login_required_and_load_user # Garante que o usuário está logado e g.user está populado
def perfil_page():
    return render_template('perfil.html')