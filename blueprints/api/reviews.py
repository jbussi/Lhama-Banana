from . import api_bp
from flask import jsonify, request
from ..services import get_db
from ..services.auth_service import verify_firebase_token
from ..services.user_service import get_user_by_firebase_uid

@api_bp.route('/base_products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Endpoint para obter todas as avaliações de um produto."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Buscar avaliações aprovadas do produto
        cur.execute("""
            SELECT 
                a.id,
                a.rating,
                a.comentario,
                a.criado_em,
                u.nome as usuario_nome,
                u.id as usuario_id
            FROM avaliacoes a
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.nome_produto_id = %s AND a.aprovado = TRUE
            ORDER BY a.criado_em DESC
        """, (product_id,))
        
        reviews = cur.fetchall()
        
        # Calcular média de avaliações
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(rating) as media,
                COUNT(CASE WHEN rating = 5 THEN 1 END) as cinco_estrelas,
                COUNT(CASE WHEN rating = 4 THEN 1 END) as quatro_estrelas,
                COUNT(CASE WHEN rating = 3 THEN 1 END) as tres_estrelas,
                COUNT(CASE WHEN rating = 2 THEN 1 END) as duas_estrelas,
                COUNT(CASE WHEN rating = 1 THEN 1 END) as uma_estrela
            FROM avaliacoes a
            WHERE a.nome_produto_id = %s AND a.aprovado = TRUE
        """, (product_id,))
        
        stats = cur.fetchone()
        
        reviews_list = []
        for review in reviews:
            reviews_list.append({
                'id': review[0],
                'rating': review[1],
                'comentario': review[2],
                'criado_em': review[3].strftime('%d/%m/%Y') if review[3] else None,
                'usuario_nome': review[4],
                'usuario_id': review[5]
            })
        
        return jsonify({
            'reviews': reviews_list,
            'stats': {
                'total': stats[0] if stats[0] else 0,
                'media': float(stats[1]) if stats[1] else 0,
                'distribuicao': {
                    '5': stats[2] if stats[2] else 0,
                    '4': stats[3] if stats[3] else 0,
                    '3': stats[4] if stats[4] else 0,
                    '2': stats[5] if stats[5] else 0,
                    '1': stats[6] if stats[6] else 0
                }
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro ao carregar avaliações: {str(e)}"}), 500
    finally:
        cur.close()

@api_bp.route('/base_products/<int:product_id>/reviews', methods=['POST'])
def create_product_review(product_id):
    """Endpoint para criar uma nova avaliação de produto."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verificar autenticação
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"erro": "Token de autenticação necessário"}), 401
        
        token = auth_header.split(' ')[1]
        decoded_token = verify_firebase_token(token)
        
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token.get('uid')
        user = get_user_by_firebase_uid(firebase_uid)
        
        if not user:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        # Obter dados do corpo da requisição
        data = request.get_json()
        rating = data.get('rating')
        comentario = data.get('comentario', '').strip()
        
        # Validações
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"erro": "Rating deve ser um número entre 1 e 5"}), 400
        
        # Verificar se o produto existe
        cur.execute("SELECT id FROM nome_produto WHERE id = %s", (product_id,))
        if not cur.fetchone():
            return jsonify({"erro": "Produto não encontrado"}), 404
        
        # Verificar se o usuário já avaliou este produto
        cur.execute("""
            SELECT id FROM avaliacoes 
            WHERE nome_produto_id = %s AND usuario_id = %s
        """, (product_id, user['id']))
        
        existing_review = cur.fetchone()
        
        if existing_review:
            # Atualizar avaliação existente
            cur.execute("""
                UPDATE avaliacoes
                SET rating = %s, comentario = %s, atualizado_em = NOW()
                WHERE id = %s
            """, (rating, comentario, existing_review[0]))
            review_id = existing_review[0]
        else:
            # Criar nova avaliação
            cur.execute("""
                INSERT INTO avaliacoes (nome_produto_id, usuario_id, rating, comentario)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (product_id, user['id'], rating, comentario))
            review_id = cur.fetchone()[0]
        
        conn.commit()
        
        return jsonify({
            "mensagem": "Avaliação salva com sucesso",
            "review_id": review_id
        }), 201
        
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro ao salvar avaliação: {str(e)}"}), 500
    finally:
        cur.close()

@api_bp.route('/base_products/<int:product_id>/reviews/me', methods=['GET'])
def get_my_review(product_id):
    """Endpoint para obter a avaliação do usuário logado para um produto."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verificar autenticação
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"review": None}), 200
        
        token = auth_header.split(' ')[1]
        decoded_token = verify_firebase_token(token)
        
        if not decoded_token:
            return jsonify({"review": None}), 200
        
        firebase_uid = decoded_token.get('uid')
        user = get_user_by_firebase_uid(firebase_uid)
        
        if not user:
            return jsonify({"review": None}), 200
        
        # Buscar avaliação do usuário
        cur.execute("""
            SELECT id, rating, comentario, criado_em
            FROM avaliacoes
            WHERE nome_produto_id = %s AND usuario_id = %s
        """, (product_id, user['id']))
        
        review = cur.fetchone()
        
        if review:
            return jsonify({
                "review": {
                    "id": review[0],
                    "rating": review[1],
                    "comentario": review[2],
                    "criado_em": review[3].strftime('%d/%m/%Y') if review[3] else None
                }
            }), 200
        else:
            return jsonify({"review": None}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"review": None}), 200
    finally:
        cur.close()

@api_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Endpoint para deletar uma avaliação (apenas o próprio autor)."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verificar autenticação
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"erro": "Token de autenticação necessário"}), 401
        
        token = auth_header.split(' ')[1]
        decoded_token = verify_firebase_token(token)
        
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token.get('uid')
        user = get_user_by_firebase_uid(firebase_uid)
        
        if not user:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        # Verificar se a avaliação existe e pertence ao usuário
        cur.execute("""
            SELECT id FROM avaliacoes
            WHERE id = %s AND usuario_id = %s
        """, (review_id, user['id']))
        
        if not cur.fetchone():
            return jsonify({"erro": "Avaliação não encontrada ou você não tem permissão para deletá-la"}), 404
        
        # Deletar avaliação
        cur.execute("DELETE FROM avaliacoes WHERE id = %s", (review_id,))
        conn.commit()
        
        return jsonify({"mensagem": "Avaliação deletada com sucesso"}), 200
        
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro ao deletar avaliação: {str(e)}"}), 500
    finally:
        cur.close()

