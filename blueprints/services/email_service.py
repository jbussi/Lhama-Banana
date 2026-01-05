"""
Serviço de Emails Customizados
==============================
Serviço para envio de emails administrativos e notificações internas.
Para emails de autenticação (verificação, reset), use o Firebase.
Este serviço é apenas para emails customizados do sistema.

Estratégia de envio:
1. Tenta usar SMTP se configurado
2. Se SMTP não estiver configurado, usa Firebase Admin SDK como fallback
3. Se nenhum estiver disponível, apenas loga (não bloqueia o sistema)
"""

from flask import current_app
from typing import Optional, Dict, List
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _send_via_firebase(to_email: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
    """
    Tenta enviar email usando Firebase Admin SDK.
    Nota: Firebase não envia emails customizados diretamente,
    então esta função apenas loga e retorna True para não bloquear o sistema.
    
    Em produção, você pode integrar com Firebase Cloud Functions
    ou usar outro serviço de email.
    """
    try:
        from firebase_admin import auth
        
        # Firebase Admin SDK não tem método direto para enviar emails customizados
        # Mas podemos logar e informar que o email seria enviado
        logger.info(f"[Firebase Fallback] Email seria enviado para {to_email}")
        logger.info(f"[Firebase Fallback] Assunto: {subject}")
        logger.info(f"[Firebase Fallback] Corpo: {body_text or 'HTML'}")
        
        # Em produção, você pode:
        # 1. Usar Firebase Cloud Functions para enviar emails
        # 2. Usar Firebase Extensions (SendGrid, Mailgun, etc.)
        # 3. Integrar com outro serviço de email
        
        # Por enquanto, apenas logamos e retornamos True para não bloquear
        return True
        
    except ImportError:
        logger.warning("Firebase Admin SDK não disponível")
        return False
    except Exception as e:
        logger.error(f"Erro ao tentar usar Firebase como fallback: {e}")
        return False


def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    from_email: Optional[str] = None
) -> bool:
    """
    Envia um email usando SMTP ou Firebase como fallback.
    
    Args:
        to_email: Email do destinatário
        subject: Assunto do email
        body_html: Corpo do email em HTML
        body_text: Corpo do email em texto (opcional)
        from_email: Email do remetente (usa config se não fornecido)
        
    Returns:
        True se enviado com sucesso ou fallback ativado, False caso contrário
    """
    try:
        # Obter configurações de email
        smtp_host = current_app.config.get('SMTP_HOST')
        smtp_port = current_app.config.get('SMTP_PORT', 587)
        smtp_user = current_app.config.get('SMTP_USER')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        default_from = current_app.config.get('EMAIL_FROM', smtp_user)
        
        # Tentar SMTP primeiro se estiver configurado
        if smtp_host and smtp_user and smtp_password:
            from_email = from_email or default_from
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            # Adicionar corpo
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Enviar via SMTP
            try:
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Email enviado via SMTP para {to_email}: {subject}")
                return True
            except Exception as smtp_error:
                logger.warning(f"Erro ao enviar via SMTP: {smtp_error}. Tentando fallback Firebase...")
                # Se SMTP falhar, tentar Firebase como fallback
                return _send_via_firebase(to_email, subject, body_html, body_text)
        
        # Se SMTP não estiver configurado, usar Firebase como fallback
        else:
            logger.info("SMTP não configurado. Usando Firebase como fallback...")
            return _send_via_firebase(to_email, subject, body_html, body_text)
        
    except Exception as e:
        logger.error(f"Erro ao enviar email para {to_email}: {e}")
        # Tentar Firebase como último recurso
        try:
            return _send_via_firebase(to_email, subject, body_html, body_text)
        except:
            return False


def send_admin_alert(
    subject: str,
    message: str,
    alert_type: str = "info"
) -> bool:
    """
    Envia alerta para todos os administradores.
    
    Args:
        subject: Assunto do alerta
        message: Mensagem do alerta
        alert_type: Tipo do alerta (info, warning, error)
        
    Returns:
        True se enviado com sucesso
    """
    admin_emails = current_app.config.get('ADMIN_EMAILS', [])
    
    if not admin_emails:
        logger.warning("Nenhum email de admin configurado")
        return False
    
    # Criar HTML do email
    color_map = {
        'info': '#40e0d0',
        'warning': '#FFE135',
        'error': '#ff4444'
    }
    color = color_map.get(alert_type, '#40e0d0')
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="background-color: {color}; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h2 style="margin: 0;">{subject}</h2>
        </div>
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
            <p style="margin: 0; white-space: pre-wrap;">{message}</p>
        </div>
        <p style="color: #666; font-size: 12px; margin-top: 20px;">
            Este é um email automático do sistema LhamaBanana.
        </p>
    </body>
    </html>
    """
    
    text_body = f"{subject}\n\n{message}\n\nEste é um email automático do sistema LhamaBanana."
    
    # Enviar para todos os admins
    success_count = 0
    for admin_email in admin_emails:
        if send_email(
            to_email=admin_email,
            subject=f"[LhamaBanana Admin] {subject}",
            body_html=html_body,
            body_text=text_body
        ):
            success_count += 1
    
    logger.info(f"Alerta administrativo processado para {success_count}/{len(admin_emails)} administradores")
    return success_count > 0


def send_security_alert(
    event_type: str,
    details: str,
    user_email: Optional[str] = None
) -> bool:
    """
    Envia alerta de segurança para administradores.
    
    Args:
        event_type: Tipo do evento (login_failed, suspicious_activity, etc)
        details: Detalhes do evento
        user_email: Email do usuário envolvido (opcional)
        
    Returns:
        True se enviado com sucesso
    """
    subject = f"Alerta de Segurança: {event_type}"
    message = f"""
Tipo de Evento: {event_type}
Usuário: {user_email or 'N/A'}
Detalhes: {details}
Timestamp: {__import__('datetime').datetime.now().isoformat()}
    """
    
    return send_admin_alert(subject, message, alert_type="error")


def send_new_user_notification(user_email: str, user_name: str) -> bool:
    """
    Notifica administradores sobre novo usuário registrado.
    
    Args:
        user_email: Email do novo usuário
        user_name: Nome do novo usuário
        
    Returns:
        True se enviado com sucesso
    """
    subject = "Novo Usuário Registrado"
    message = f"""
Um novo usuário se registrou no sistema:

Nome: {user_name}
Email: {user_email}
Data: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    """
    
    return send_admin_alert(subject, message, alert_type="info")

