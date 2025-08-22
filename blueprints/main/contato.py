from flask import render_template, session
from . import main_bp

@main_bp.route('/contato')
def contato_page():
    return render_template('contato.html', user=session.get('username'))