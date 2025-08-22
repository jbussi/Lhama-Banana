from flask import render_template, session
from . import main_bp

@main_bp.route('/sobre-nos')
@main_bp.route('/sobre')
def sobre_nos():
    return render_template('sobre_nos.html', user=session.get('uid'))