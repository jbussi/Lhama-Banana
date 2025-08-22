from . import auth_bp
from flask import render_template

@auth_bp.route('/login', methods=["GET"])
def login_page():
    return render_template('login.html')