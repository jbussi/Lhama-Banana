from . import auth_bp
from flask import render_template

@auth_bp.route('/register', methods=["GET"])
def register_page():
        return render_template('register.html')