from flask import render_template, g, current_app
from . import admin_bp
from .decorators import admin_required_email

@admin_bp.route('/')
@admin_required_email
def dashboard():
    """Dashboard principal com analytics e insights"""
    user_data = g.user if hasattr(g, 'user') else (g.user_db_data if hasattr(g, 'user_db_data') else {})
    return render_template('admin/dashboard.html', 
                         user=user_data)

@admin_bp.route('/etiquetas')
@admin_required_email
def etiquetas():
    """Gerenciamento de etiquetas de frete"""
    user_data = g.user if hasattr(g, 'user') else (g.user_db_data if hasattr(g, 'user_db_data') else {})
    return render_template('admin/etiquetas.html',
                         user=user_data)

@admin_bp.route('/estoque')
@admin_required_email
def estoque():
    """Gerenciamento de estoque"""
    user_data = g.user if hasattr(g, 'user') else (g.user_db_data if hasattr(g, 'user_db_data') else {})
    return render_template('admin/estoque.html',
                         user=user_data)

@admin_bp.route('/produtos')
@admin_required_email
def produtos():
    """Gerenciamento de produtos"""
    user_data = g.user if hasattr(g, 'user') else (g.user_db_data if hasattr(g, 'user_db_data') else {})
    return render_template('admin/produtos.html',
                         user=user_data)

@admin_bp.route('/vendas')
@admin_required_email
def vendas():
    """Análise de vendas e relatórios"""
    user_data = g.user if hasattr(g, 'user') else (g.user_db_data if hasattr(g, 'user_db_data') else {})
    return render_template('admin/vendas.html',
                         user=user_data)

@admin_bp.route('/pedidos')
@admin_required_email
def pedidos():
    """Gerenciamento de pedidos"""
    user_data = g.user if hasattr(g, 'user') else (g.user_db_data if hasattr(g, 'user_db_data') else {})
    return render_template('admin/pedidos.html',
                         user=user_data)

