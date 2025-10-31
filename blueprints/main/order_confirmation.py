from flask import render_template, request, session, redirect, url_for
from . import main_bp
from ..services import get_order_status
from ..services.user_service import get_user_by_firebase_uid

@main_bp.route('/order-status/<string:codigo_pedido>')
def order_confirmation(codigo_pedido):
    """
    Página de confirmação e acompanhamento de pedido
    """
    try:
        # Buscar dados do pedido
        order_data = get_order_status(codigo_pedido=codigo_pedido)
        
        if not order_data:
            return render_template('order_confirmation.html', 
                                 error="Pedido não encontrado",
                                 codigo_pedido=codigo_pedido)
        
        # Verificar se o usuário tem permissão para ver este pedido
        uid = session.get('uid')
        user_data = None
        if uid:
            user_data = get_user_by_firebase_uid(uid)
        
        # Se o usuário estiver logado, verificar se é o dono do pedido
        if user_data and order_data.get('usuario_id') != user_data['id']:
            return render_template('order_confirmation.html', 
                                 error="Acesso negado",
                                 codigo_pedido=codigo_pedido)
        
        # Preparar dados para o template
        context = {
            'order': order_data,
            'codigo_pedido': codigo_pedido,
            'user': user_data,
            'is_logged_in': bool(user_data)
        }
        
        # Adicionar parâmetros da URL se existirem (para PIX, boleto, etc.)
        pix_qr = request.args.get('pix_qr')
        pix_text = request.args.get('pix_text')
        boleto_link = request.args.get('boleto_link')
        boleto_barcode = request.args.get('boleto_barcode')
        
        if pix_qr:
            context['pix_qr'] = pix_qr
            context['pix_text'] = pix_text
        elif boleto_link:
            context['boleto_link'] = boleto_link
            context['boleto_barcode'] = boleto_barcode
        
        # Adicionar dados de pagamento do pedido se disponível
        if order_data and 'forma_pagamento' in order_data:
            context['payment_method'] = order_data.get('forma_pagamento')
            context['payment_status'] = order_data.get('status_pagamento')
        
        return render_template('order_confirmation.html', **context)
        
    except Exception as e:
        print(f"Erro ao carregar confirmação do pedido: {e}")
        return render_template('order_confirmation.html', 
                             error="Erro ao carregar dados do pedido",
                             codigo_pedido=codigo_pedido)
