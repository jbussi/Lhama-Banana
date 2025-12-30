"""
Rotas para as páginas de pagamento (PIX, Boleto) e status do pedido
"""
from flask import render_template, session, request, redirect, url_for, abort
from . import main_bp
from ..services.order_service import get_order_by_token


@main_bp.route('/pagamento/pix')
@main_bp.route('/pix-payment')
def pix_payment_page():
    """
    Página de pagamento via PIX.
    Renderiza o template pix_payment.html.
    """
    token = request.args.get('token')
    
    if not token:
        abort(404, description="Token não fornecido")
    
    # Buscar dados do pedido pelo token
    order = get_order_by_token(token)
    
    if not order:
        abort(404, description="Pedido não encontrado")
    
    # Preparar dados para o template
    template_data = {
        'user_logged_in': 'user_id' in session,
        'user_email': session.get('email', ''),
        'user_name': session.get('username', ''),
        'order_code': order.get('codigo_pedido', ''),
        'payment_amount': f"R$ {order.get('valor', 0):.2f}".replace('.', ','),
        'payment_expiry': order.get('boleto_expires_at', ''),
        'status': order.get('status', 'PENDENTE'),
        'pix_code': '',  # Será preenchido via JavaScript
        'pix_qr_code_link': order.get('pix_qr_code_link', ''),
        'pix_qr_code_image': order.get('pix_qr_code_image', ''),
        'token': token
    }
    
    return render_template('pix_payment.html', **template_data)


@main_bp.route('/pagamento/boleto')
@main_bp.route('/boleto-payment')
def boleto_payment_page():
    """
    Página de pagamento via Boleto.
    Renderiza o template boleto_payment.html.
    """
    token = request.args.get('token')
    
    if not token:
        abort(404, description="Token não fornecido")
    
    # Buscar dados do pedido pelo token
    order = get_order_by_token(token)
    
    if not order:
        abort(404, description="Pedido não encontrado")
    
    # Preparar dados para o template
    template_data = {
        'user_logged_in': 'user_id' in session,
        'user_email': session.get('email', ''),
        'user_name': session.get('username', ''),
        'order_code': order.get('codigo_pedido', ''),
        'payment_amount': f"R$ {order.get('valor', 0):.2f}".replace('.', ','),
        'payment_expiry': order.get('boleto_expires_at', ''),
        'status': order.get('status', 'PENDENTE'),
        'barcode': order.get('boleto_barcode', ''),
        'boleto_url': order.get('boleto_link', '#'),
        'boleto_pdf_url': order.get('boleto_link', '#'),
        'token': token
    }
    
    return render_template('boleto_payment.html', **template_data)


@main_bp.route('/status-pedido')
@main_bp.route('/order-status')
def order_status_page():
    """
    Página de status do pedido.
    Renderiza o template order_status.html.
    """
    token = request.args.get('token')
    
    if not token:
        abort(404, description="Token não fornecido")
    
    # Buscar dados do pedido pelo token
    order = get_order_by_token(token)
    
    if not order:
        # Mostrar mensagem de erro
        return render_template('order_status.html',
                             user_logged_in='user_id' in session,
                             user_email=session.get('email', ''),
                             user_name=session.get('username', ''),
                             order_code='',
                             order_value='',
                             order_date='',
                             last_update='',
                             status='NOT_FOUND',
                             token=token,
                             error=True)
    
    # Formatar datas
    data_venda = order.get('data_venda', '')
    if data_venda:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(data_venda.replace('Z', '+00:00'))
            data_venda = dt.strftime('%d/%m/%Y %H:%M')
        except:
            data_venda = ''
    
    ultima_atualizacao = order.get('atualizado_em', '')
    if ultima_atualizacao:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(ultima_atualizacao.replace('Z', '+00:00'))
            ultima_atualizacao = dt.strftime('%d/%m/%Y %H:%M')
        except:
            ultima_atualizacao = ''
    
    # Preparar dados para o template
    template_data = {
        'user_logged_in': 'user_id' in session,
        'user_email': session.get('email', ''),
        'user_name': session.get('username', ''),
        'order_code': order.get('codigo_pedido', ''),
        'order_value': f"R$ {order.get('valor', 0):.2f}".replace('.', ','),
        'order_date': data_venda,
        'last_update': ultima_atualizacao,
        'status': order.get('status', 'PENDENTE'),
        'token': token,
        'error': False
    }
    
    return render_template('order_status.html', **template_data)

