from flask import render_template, session, redirect, url_for
from . import main_bp

@main_bp.route('/')
@main_bp.route('/home')
def home():
    return render_template('home.html', user=session.get('uid'))

@main_bp.route('/loja')
def loja_page():
    return redirect(url_for('produtos.produtos_page'))