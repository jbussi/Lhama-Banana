"""
Templates de Email
==================
Templates HTML para diferentes tipos de emails do sistema.
"""

from flask import url_for, current_app
from typing import Optional
from datetime import datetime


def get_base_email_template(
    title: str,
    content: str,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
    footer_text: Optional[str] = None
) -> str:
    """
    Template base para emails com estilo da marca.
    
    Args:
        title: Título do email
        content: Conteúdo principal (HTML)
        button_text: Texto do botão (opcional)
        button_url: URL do botão (opcional)
        footer_text: Texto do rodapé (opcional)
        
    Returns:
        HTML completo do email
    """
    base_url = current_app.config.get('BASE_URL', 'https://lhama-banana.com.br')
    
    button_html = ""
    if button_text and button_url:
        button_html = f"""
        <div style="text-align: center; margin: 30px 0;">
            <a href="{button_url}" style="display: inline-block; background: linear-gradient(135deg, #40e0d0, #2ab7a9); color: white; padding: 14px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 12px rgba(64, 224, 208, 0.3);">
                {button_text}
            </a>
        </div>
        """
    
    footer = footer_text or f"""
    <p style="color: #666; font-size: 12px; margin-top: 30px; text-align: center;">
        © 2025 LhamaBanana™. Todos os direitos reservados.<br>
        Este é um email automático, por favor não responda.
    </p>
    """
    
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #40e0d0, #2ab7a9);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px 30px;
                background-color: #ffffff;
            }}
            .content p {{
                margin: 15px 0;
                color: #555;
                font-size: 16px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                border-top: 1px solid #e0e0e0;
            }}
            .warning-box {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .info-box {{
                background-color: #d1ecf1;
                border-left: 4px solid #40e0d0;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            @media only screen and (max-width: 600px) {{
                .email-container {{
                    width: 100% !important;
                }}
                .content {{
                    padding: 30px 20px !important;
                }}
            }}
        </style>
    </head>
    <body>
        <div style="padding: 20px 0;">
            <div class="email-container">
                <div class="header">
                    <h1>🦙 LhamaBanana™</h1>
                </div>
                <div class="content">
                    <h2 style="color: #2ab7a9; margin-top: 0;">{title}</h2>
                    {content}
                    {button_html}
                </div>
                <div class="footer">
                    {footer}
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def get_welcome_email_template(user_name: str, verification_url: Optional[str] = None) -> tuple[str, str]:
    """
    Template de email de boas-vindas/confirmação de conta.
    
    Args:
        user_name: Nome do usuário
        verification_url: URL de verificação (opcional)
        
    Returns:
        Tupla (HTML, texto)
    """
    title = "Bem-vindo à LhamaBanana™!"
    
    content = f"""
    <p>Olá <strong>{user_name}</strong>!</p>
    <p>É um prazer ter você conosco! 🎉</p>
    <p>Sua conta foi criada com sucesso. Agora você pode:</p>
    <ul style="color: #555; line-height: 2;">
        <li>Explorar nossa coleção completa de produtos</li>
        <li>Fazer pedidos com segurança</li>
        <li>Acompanhar seus pedidos em tempo real</li>
        <li>Receber ofertas exclusivas e novidades</li>
    </ul>
    """
    
    if verification_url:
        content += f"""
        <div class="info-box">
            <p style="margin: 0;"><strong>⚠️ Importante:</strong> Para garantir a segurança da sua conta, 
            precisamos verificar seu endereço de email. Clique no botão abaixo para confirmar:</p>
        </div>
        """
        button_text = "Verificar Email"
        button_url = verification_url
    else:
        button_text = None
        button_url = None
    
    content += """
    <p>Se você tiver alguma dúvida, nossa equipe está sempre pronta para ajudar!</p>
    <p>Bem-vindo à família LhamaBanana™! 🦙✨</p>
    """
    
    html = get_base_email_template(title, content, button_text, button_url)
    
    text = f"""
Bem-vindo à LhamaBanana™!

Olá {user_name}!

É um prazer ter você conosco! Sua conta foi criada com sucesso.

Agora você pode:
- Explorar nossa coleção completa de produtos
- Fazer pedidos com segurança
- Acompanhar seus pedidos em tempo real
- Receber ofertas exclusivas e novidades

{f'Verifique seu email acessando: {verification_url}' if verification_url else ''}

Se você tiver alguma dúvida, nossa equipe está sempre pronta para ajudar!

Bem-vindo à família LhamaBanana™!

© 2025 LhamaBanana™. Todos os direitos reservados.
    """
    
    return html, text


def get_password_reset_email_template(user_name: str, reset_url: str) -> tuple[str, str]:
    """
    Template de email de recuperação de senha.
    
    Args:
        user_name: Nome do usuário
        reset_url: URL para redefinir senha
        
    Returns:
        Tupla (HTML, texto)
    """
    title = "Redefinir sua Senha"
    
    content = f"""
    <p>Olá <strong>{user_name}</strong>!</p>
    <p>Recebemos uma solicitação para redefinir a senha da sua conta na LhamaBanana™.</p>
    <p>Se você fez esta solicitação, clique no botão abaixo para criar uma nova senha:</p>
    <div class="warning-box">
        <p style="margin: 0;"><strong>⚠️ Importante:</strong> Este link expira em 1 hora por motivos de segurança.</p>
    </div>
    <p>Se você <strong>não</strong> solicitou a redefinição de senha, ignore este email. Sua senha permanecerá a mesma.</p>
    """
    
    html = get_base_email_template(title, content, "Redefinir Senha", reset_url)
    
    text = f"""
Redefinir sua Senha - LhamaBanana™

Olá {user_name}!

Recebemos uma solicitação para redefinir a senha da sua conta.

Se você fez esta solicitação, acesse o link abaixo para criar uma nova senha:

{reset_url}

⚠️ IMPORTANTE: Este link expira em 1 hora por motivos de segurança.

Se você NÃO solicitou a redefinição de senha, ignore este email. Sua senha permanecerá a mesma.

© 2025 LhamaBanana™. Todos os direitos reservados.
    """
    
    return html, text


def get_password_changed_email_template(user_name: str) -> tuple[str, str]:
    """
    Template de email de confirmação de alteração de senha.
    
    Args:
        user_name: Nome do usuário
        
    Returns:
        Tupla (HTML, texto)
    """
    title = "Senha Alterada com Sucesso"
    
    content = f"""
    <p>Olá <strong>{user_name}</strong>!</p>
    <p>Sua senha foi alterada com sucesso.</p>
    <div class="info-box">
        <p style="margin: 0;"><strong>✅ Confirmação:</strong> A alteração foi realizada em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.</p>
    </div>
    <p>Se você <strong>não</strong> realizou esta alteração, entre em contato conosco imediatamente através do nosso 
    <a href="{current_app.config.get('BASE_URL', 'https://lhama-banana.com.br')}/contato" style="color: #40e0d0;">formulário de contato</a>.</p>
    <p>Para sua segurança, recomendamos:</p>
    <ul style="color: #555; line-height: 2;">
        <li>Usar uma senha forte e única</li>
        <li>Não compartilhar sua senha com ninguém</li>
        <li>Alterar sua senha periodicamente</li>
    </ul>
    """
    
    html = get_base_email_template(title, content)
    
    text = f"""
Senha Alterada com Sucesso - LhamaBanana™

Olá {user_name}!

Sua senha foi alterada com sucesso.

Confirmação: A alteração foi realizada em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.

Se você NÃO realizou esta alteração, entre em contato conosco imediatamente.

Para sua segurança, recomendamos:
- Usar uma senha forte e única
- Não compartilhar sua senha com ninguém
- Alterar sua senha periodicamente

© 2025 LhamaBanana™. Todos os direitos reservados.
    """
    
    return html, text


def get_order_confirmation_email_template(
    user_name: str,
    order_number: str,
    order_total: float,
    order_items: list
) -> tuple[str, str]:
    """
    Template de email de confirmação de pedido.
    
    Args:
        user_name: Nome do usuário
        order_number: Número do pedido
        order_total: Valor total do pedido
        order_items: Lista de itens do pedido
        
    Returns:
        Tupla (HTML, texto)
    """
    title = "Pedido Confirmado!"
    
    items_html = ""
    items_text = ""
    for item in order_items:
        items_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0;">{item.get('nome', 'Produto')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: center;">{item.get('quantidade', 1)}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e0e0e0; text-align: right;">R$ {item.get('preco', 0):.2f}</td>
        </tr>
        """
        items_text += f"- {item.get('nome', 'Produto')} x{item.get('quantidade', 1)} - R$ {item.get('preco', 0):.2f}\n"
    
    content = f"""
    <p>Olá <strong>{user_name}</strong>!</p>
    <p>Seu pedido foi confirmado com sucesso! 🎉</p>
    <div class="info-box">
        <p style="margin: 0;"><strong>Número do Pedido:</strong> {order_number}</p>
        <p style="margin: 0;"><strong>Valor Total:</strong> R$ {order_total:.2f}</p>
    </div>
    <p><strong>Itens do Pedido:</strong></p>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <thead>
            <tr style="background-color: #f8f9fa;">
                <th style="padding: 10px; text-align: left; border-bottom: 2px solid #40e0d0;">Produto</th>
                <th style="padding: 10px; text-align: center; border-bottom: 2px solid #40e0d0;">Qtd</th>
                <th style="padding: 10px; text-align: right; border-bottom: 2px solid #40e0d0;">Preço</th>
            </tr>
        </thead>
        <tbody>
            {items_html}
        </tbody>
    </table>
    <p>Você receberá um email com o código de rastreamento assim que seu pedido for enviado.</p>
    <p>Obrigado por escolher a LhamaBanana™! 🦙</p>
    """
    
    base_url = current_app.config.get('BASE_URL', 'https://lhama-banana.com.br')
    button_text = "Acompanhar Pedido"
    button_url = f"{base_url}/pedido/{order_number}"
    
    html = get_base_email_template(title, content, button_text, button_url)
    
    text = f"""
Pedido Confirmado! - LhamaBanana™

Olá {user_name}!

Seu pedido foi confirmado com sucesso!

Número do Pedido: {order_number}
Valor Total: R$ {order_total:.2f}

Itens do Pedido:
{items_text}

Você receberá um email com o código de rastreamento assim que seu pedido for enviado.

Acompanhe seu pedido: {base_url}/pedido/{order_number}

Obrigado por escolher a LhamaBanana™!

© 2025 LhamaBanana™. Todos os direitos reservados.
    """
    
    return html, text
