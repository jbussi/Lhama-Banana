from flask import render_template, redirect
from . import admin_bp
from .decorators import admin_required_email

@admin_bp.route('/', methods=['GET'])
@admin_required_email
def admin_index():
    """Página principal do admin - redireciona para Strapi após autenticação"""
    return redirect('http://localhost:1337/admin')
