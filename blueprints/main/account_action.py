"""
Rotas para processar links de ação do Firebase (verificação de email, reset de senha, etc.)
"""
from flask import render_template, request, redirect, url_for, flash, current_app
from ..main import main_bp
from firebase_admin import auth as firebase_auth

@main_bp.route('/account-action', methods=['GET'])
def account_action():
    """
    Processa links de ação do Firebase (verificação de email, reset de senha, etc.)
    
    Parâmetros esperados:
    - mode: Tipo de ação (verifyEmail, resetPassword, recoverEmail, changeEmail)
    - oobCode: Código de ação do Firebase
    """
    mode = request.args.get('mode')
    oob_code = request.args.get('oobCode')
    
    if not mode or not oob_code:
        return render_template('account_action_error.html', 
                             error="Link inválido",
                             message="O link de ação está incompleto. Por favor, use o link completo enviado por email."), 400
    
    try:
        # Verificar o código de ação
        action_code_info = firebase_auth.verify_action_code(oob_code)
        
        action_type = action_code_info.get('operation')
        email = action_code_info.get('data', {}).get('email', '')
        
        # Renderizar página apropriada baseada no tipo de ação
        if action_type == 'VERIFY_EMAIL':
            return render_template('account_action_verify_email.html',
                                 oob_code=oob_code,
                                 email=email,
                                 action_type='verifyEmail')
        
        elif action_type == 'PASSWORD_RESET':
            return render_template('account_action_reset_password.html',
                                 oob_code=oob_code,
                                 email=email,
                                 action_type='resetPassword')
        
        elif action_type == 'RECOVER_EMAIL':
            return render_template('account_action_recover_email.html',
                                 oob_code=oob_code,
                                 email=email,
                                 action_type='recoverEmail')
        
        elif action_type == 'EMAIL_SIGNIN':
            return render_template('account_action_email_signin.html',
                                 oob_code=oob_code,
                                 email=email,
                                 action_type='emailSignin')
        
        else:
            return render_template('account_action_error.html',
                                 error="Ação não suportada",
                                 message=f"O tipo de ação '{action_type}' não é suportado."), 400
    
    except firebase_auth.InvalidActionCodeError:
        return render_template('account_action_error.html',
                             error="Link expirado ou inválido",
                             message="Este link já foi usado ou expirou. Por favor, solicite um novo link."), 400
    
    except Exception as e:
        current_app.logger.error(f"Erro ao processar ação de conta: {e}")
        return render_template('account_action_error.html',
                             error="Erro ao processar ação",
                             message="Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente."), 500
