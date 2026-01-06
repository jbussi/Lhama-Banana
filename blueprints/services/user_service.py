from .db import get_db
from functools import wraps
from flask import session, redirect, url_for, flash, g

def get_user_by_firebase_uid(firebase_uid):
    """Busca os dados principais de um usuário pelo seu Firebase UID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, firebase_uid, nome, email, cpf, data_nascimento, criado_em, telefone, role, 
               mfa_enabled, mfa_secret
        FROM usuarios WHERE firebase_uid = %s
    """, (firebase_uid,))
    user_data = cur.fetchone()
    cur.close()

    if user_data:
        # Retorna um dicionário para facilitar o acesso por nome da coluna
        # Adapte os índices conforme a ordem das colunas no seu SELECT
        return {
            'id': user_data[0],
            'firebase_uid': user_data[1],
            'nome': user_data[2],
            'email': user_data[3],
            'cpf': user_data[4],
            'data_nascimento': str(user_data[5]) if user_data[5] else None,
            'criado_em': str(user_data[6]),
            'telefone': user_data[7],
            'role': user_data[8] if len(user_data) > 8 else 'user',  # role do usuário
            'mfa_enabled': user_data[9] if len(user_data) > 9 else False,
            'mfa_secret': user_data[10] if len(user_data) > 10 else None,
        }
    return None

def insert_new_user(firebase_uid, nome, email):
    """Insere um novo usuário na tabela 'usuarios'."""
    conn = get_db() # Obtém a conexão do pool
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (firebase_uid, nome, email) VALUES (%s, %s, %s) RETURNING id",
            (firebase_uid, nome, email)
        )
        new_user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        return new_user_id
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao inserir novo usuário: {e}")
        return None

def update_user_profile_db(user_id, data):
    """Atualiza os dados de perfil de um usuário."""
    conn = get_db() # Obtém a conexão do pool
    cur = conn.cursor()
    try:
        cur = conn.cursor()
        # Construa a query dinamicamente para atualizar apenas campos presentes em 'data'
        updates = []
        params = []
        
        if 'nome' in data:
            updates.append("nome = %s")
            params.append(data['nome'])
        if 'email' in data: # Cuidado ao permitir atualização de email que é também UID no Firebase
            updates.append("email = %s")
            params.append(data['email'])
        if 'cpf' in data:
            updates.append("cpf = %s")
            params.append(data['cpf'])
        if 'data_nascimento' in data:
            updates.append("data_nascimento = %s")
            # Converta string para date object se necessário, ex: datetime.date.fromisoformat(data['data_nascimento'])
            params.append(data['data_nascimento']) 
        if 'telefone' in data:
            updates.append("telefone = %s")
            params.append(data['telefone'])

        if not updates: # Nenhuma atualização para fazer
            cur.close()
            return True

        query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
        params.append(user_id)
        
        cur.execute(query, tuple(params))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao atualizar perfil do usuário {user_id}: {e}")
        return False

def login_required_and_load_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid = session.get('uid')
        if not uid:
            return redirect(url_for('auth.login_page')) # Sua rota de login HTML

        user_data = get_user_by_firebase_uid(uid) # Usa a função auxiliar
        if not user_data:
            session.pop('uid', None) # Limpa sessão se usuário não existe no DB
            return redirect(url_for('auth.login_page'))

        g.user = user_data # g.user agora é um dicionário com os dados principais

        # Busca endereços do usuário e adiciona a g.user
        addresses = get_user_addresses(user_data['id'])
        g.user['addresses'] = addresses

        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorador que verifica se o usuário tem permissão de administrador.
    Assume que `login_required_and_load_user` já foi aplicado e `g.user_db_data` está preenchido.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # g.user_db_data já deve estar preenchido por login_required_and_load_user
        if not hasattr(g, 'user_db_data') or g.user_db_data.get('role') != 'admin':
            flash("Acesso negado: Você não possui permissões de administrador.")
            # Você pode escolher redirecionar para uma página de acesso negado
            # ou simplesmente retornar um 404 (para não dar dicas sobre a existência da página)
            return redirect(url_for('home')) # Redireciona para a home
            # from flask import abort
            # abort(404) # Se quiser um 404 para esconder a página

        return f(*args, **kwargs)
    return decorated_function

def get_user_addresses(user_id):
    """Busca todos os endereços ativos de um usuário."""
    conn = get_db()
    cur = conn.cursor()
    try:
        print(f"Buscando endereços para user_id: {user_id}")
        
        # Primeiro, verificar quantos endereços existem (incluindo inativos)
        cur.execute("SELECT COUNT(*) FROM enderecos WHERE usuario_id = %s", (user_id,))
        total_count = cur.fetchone()[0]
        print(f"Total de endereços (incluindo inativos) para user {user_id}: {total_count}")
        
        # Buscar apenas ativos
        cur.execute("""
            SELECT id, nome_endereco, cep, rua, numero, complemento, bairro, cidade, estado, 
                   referencia, is_default, telefone, email, criado_em, atualizado_em, ativo
            FROM enderecos 
            WHERE usuario_id = %s AND ativo = TRUE
            ORDER BY is_default DESC, criado_em DESC
        """, (user_id,))
        addresses = cur.fetchall()
        print(f"Endereços ativos encontrados: {len(addresses)}")
        
        # Se não encontrou ativos, verificar todos (para debug)
        if len(addresses) == 0:
            cur.execute("SELECT id, nome_endereco, ativo FROM enderecos WHERE usuario_id = %s", (user_id,))
            all_addresses = cur.fetchall()
            print(f"Todos os endereços (incluindo inativos) para user {user_id}: {all_addresses}")
        
        cur.close()
        
        result = []
        for addr in addresses:
            result.append({
                'id': addr[0],
                'type': 'home' if addr[1] == 'Casa' else ('work' if addr[1] == 'Trabalho' else 'other'),
                'zipcode': addr[2],
                'street': addr[3],
                'number': addr[4],
                'complement': addr[5] or '',
                'neighborhood': addr[6],
                'city': addr[7],
                'state': addr[8],
                'reference': addr[9] or '',
                'isDefault': addr[10],
                'phone': addr[11] or '',
                'email': addr[12] or '',
                'created_at': str(addr[13]) if addr[13] else None,
                'updated_at': str(addr[14]) if addr[14] else None,
            })
        print(f"Retornando {len(result)} endereços formatados")
        return result
    except Exception as e:
        print(f"Erro ao buscar endereços do usuário {user_id}: {e}")
        import traceback
        traceback.print_exc()
        cur.close()
        return []

def create_user_address(user_id, address_data):
    """Cria um novo endereço para o usuário. Retorna o ID do endereço criado ou None."""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Verificar se já tem 4 endereços ativos
        cur.execute("SELECT COUNT(*) FROM enderecos WHERE usuario_id = %s AND ativo = TRUE", (user_id,))
        count = cur.fetchone()[0]
        if count >= 4:
            cur.close()
            return None, "Limite de 4 endereços atingido. Remova um endereço antes de adicionar outro."
        
        # Se for o primeiro endereço, definir como padrão
        if count == 0:
            is_default = True
        else:
            is_default = address_data.get('isDefault', False)
            # Se este for definido como padrão, remover padrão dos outros
            if is_default:
                cur.execute("UPDATE enderecos SET is_default = FALSE WHERE usuario_id = %s", (user_id,))
        
        # Mapear campos do frontend para o banco
        nome_endereco_map = {
            'home': 'Casa',
            'work': 'Trabalho',
            'other': 'Outro'
        }
        nome_endereco = nome_endereco_map.get(address_data.get('type', 'home'), 'Casa')
        
        cur.execute("""
            INSERT INTO enderecos (usuario_id, nome_endereco, cep, rua, numero, complemento, 
                                 bairro, cidade, estado, referencia, is_default, telefone, email, ativo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id,
            nome_endereco,
            address_data.get('zipcode', '').replace('-', '').replace(' ', '')[:8],
            address_data.get('street', ''),
            address_data.get('number', ''),
            address_data.get('complement', '') or None,
            address_data.get('neighborhood', ''),
            address_data.get('city', ''),
            address_data.get('state', ''),
            address_data.get('reference', '') or None,
            is_default,
            address_data.get('phone', '') or None,
            address_data.get('email', '') or None,
            True  # Garantir que ativo = TRUE explicitamente
        ))
        
        new_address_id = cur.fetchone()[0]
        conn.commit()
        print(f"Endereço criado com sucesso. ID: {new_address_id}, User ID: {user_id}")
        
        # Verificar se o endereço foi realmente criado
        cur.execute("SELECT id, ativo FROM enderecos WHERE id = %s", (new_address_id,))
        check = cur.fetchone()
        if check:
            print(f"Endereço verificado no banco. ID: {check[0]}, Ativo: {check[1]}")
        else:
            print(f"ERRO: Endereço {new_address_id} não encontrado após criação!")
        
        cur.close()
        return new_address_id, None
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao criar endereço: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Erro ao criar endereço: {str(e)}"

def update_user_address(user_id, address_id, address_data):
    """Atualiza um endereço do usuário."""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Verificar se o endereço pertence ao usuário
        cur.execute("SELECT id FROM enderecos WHERE id = %s AND usuario_id = %s AND ativo = TRUE", 
                   (address_id, user_id))
        if not cur.fetchone():
            cur.close()
            return False, "Endereço não encontrado ou não pertence a este usuário."
        
        # Se for definido como padrão, remover padrão dos outros
        if address_data.get('isDefault', False):
            cur.execute("UPDATE enderecos SET is_default = FALSE WHERE usuario_id = %s AND id != %s", 
                       (user_id, address_id))
        
        nome_endereco_map = {
            'home': 'Casa',
            'work': 'Trabalho',
            'other': 'Outro'
        }
        nome_endereco = nome_endereco_map.get(address_data.get('type', 'home'), 'Casa')
        
        cur.execute("""
            UPDATE enderecos 
            SET nome_endereco = %s, cep = %s, rua = %s, numero = %s, complemento = %s,
                bairro = %s, cidade = %s, estado = %s, referencia = %s, is_default = %s,
                telefone = %s, email = %s, atualizado_em = NOW()
            WHERE id = %s AND usuario_id = %s
        """, (
            nome_endereco,
            address_data.get('zipcode', '').replace('-', '').replace(' ', '')[:8],
            address_data.get('street', ''),
            address_data.get('number', ''),
            address_data.get('complement', '') or None,
            address_data.get('neighborhood', ''),
            address_data.get('city', ''),
            address_data.get('state', ''),
            address_data.get('reference', '') or None,
            address_data.get('isDefault', False),
            address_data.get('phone', '') or None,
            address_data.get('email', '') or None,
            address_id,
            user_id,
        ))
        
        conn.commit()
        cur.close()
        return True, None
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao atualizar endereço: {e}")
        return False, f"Erro ao atualizar endereço: {str(e)}"

def get_user_orders(user_id):
    """Busca todos os pedidos de um usuário com seus itens."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                v.id,
                v.codigo_pedido,
                v.data_venda,
                v.valor_total,
                v.valor_frete,
                v.valor_desconto,
                v.status_pedido,
                v.rua_entrega,
                v.numero_entrega,
                v.complemento_entrega,
                v.bairro_entrega,
                v.cidade_entrega,
                v.estado_entrega,
                v.cep_entrega,
                v.data_envio,
                v.data_entrega_estimada,
                v.data_entrega_real,
                v.observacoes_cliente,
                o.public_token,
                o.status as order_status
            FROM vendas v
            LEFT JOIN orders o ON o.venda_id = v.id
            WHERE v.usuario_id = %s
            ORDER BY v.data_venda DESC
        """, (user_id,))
        
        orders = cur.fetchall()
        
        result = []
        for order in orders:
            # Buscar itens do pedido
            cur.execute("""
                SELECT 
                    iv.id,
                    iv.quantidade,
                    iv.preco_unitario,
                    iv.subtotal,
                    iv.nome_produto_snapshot,
                    iv.sku_produto_snapshot,
                    iv.detalhes_produto_snapshot
                FROM itens_venda iv
                WHERE iv.venda_id = %s
                ORDER BY iv.id ASC
            """, (order[0],))
            
            items = cur.fetchall()
            order_items = []
            for item in items:
                order_items.append({
                    'id': item[0],
                    'quantidade': item[1],
                    'preco_unitario': float(item[2]),
                    'subtotal': float(item[3]),
                    'nome_produto': item[4],
                    'sku': item[5],
                    'detalhes': item[6] if item[6] else {}
                })
            
            # Mapear status para português
            status_map = {
                'pendente': 'Pendente',
                'pendente_pagamento': 'Aguardando Pagamento',
                'processando_envio': 'Processando Envio',
                'enviado': 'Enviado',
                'entregue': 'Entregue',
                'cancelado_pelo_cliente': 'Cancelado',
                'cancelado_pelo_vendedor': 'Cancelado',
                'devolvido': 'Devolvido',
                'reembolsado': 'Reembolsado'
            }
            
            result.append({
                'id': order[0],
                'codigo_pedido': order[1],
                'data_venda': str(order[2]) if order[2] else None,
                'valor_total': float(order[3]),
                'valor_frete': float(order[4]),
                'valor_desconto': float(order[5]),
                'status': order[6],
                'status_display': status_map.get(order[6], order[6]),
                'endereco': {
                    'rua': order[7],
                    'numero': order[8],
                    'complemento': order[9] or '',
                    'bairro': order[10],
                    'cidade': order[11],
                    'estado': order[12],
                    'cep': order[13]
                },
                'data_envio': str(order[14]) if order[14] else None,
                'data_entrega_estimada': str(order[15]) if order[15] else None,
                'data_entrega_real': str(order[16]) if order[16] else None,
                'observacoes': order[17] or '',
                'public_token': str(order[18]) if order[18] else None,
                'order_status': order[19] if order[19] else None,
                'itens': order_items
            })
        
        cur.close()
        return result
    except Exception as e:
        print(f"Erro ao buscar pedidos do usuário {user_id}: {e}")
        import traceback
        traceback.print_exc()
        cur.close()
        return []

def delete_user_address(user_id, address_id):
    """Remove (desativa) um endereço do usuário."""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Verificar se o endereço pertence ao usuário
        cur.execute("SELECT id, is_default FROM enderecos WHERE id = %s AND usuario_id = %s AND ativo = TRUE", 
                   (address_id, user_id))
        addr = cur.fetchone()
        if not addr:
            cur.close()
            return False, "Endereço não encontrado ou não pertence a este usuário."
        
        # Se for o endereço padrão, definir outro como padrão
        if addr[1]:  # is_default
            cur.execute("""
                UPDATE enderecos SET is_default = TRUE 
                WHERE id = (
                    SELECT id FROM enderecos 
                    WHERE usuario_id = %s AND id != %s AND ativo = TRUE
                    LIMIT 1
                )
            """, (user_id, address_id))
        
        # Desativar o endereço (soft delete)
        cur.execute("UPDATE enderecos SET ativo = FALSE WHERE id = %s AND usuario_id = %s", 
                   (address_id, user_id))
        
        conn.commit()
        cur.close()
        return True, None
    except Exception as e:
        conn.rollback()
        cur.close()
        print(f"Erro ao remover endereço: {e}")
        return False, f"Erro ao remover endereço: {str(e)}"