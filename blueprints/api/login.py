from . import api_bp
from flask import request, jsonify, session
from firebase_admin import auth
from ..services import get_db

@api_bp.route('/login_user', methods=["POST"])
def login_api():
        # método POST:
    data = request.get_json()
    id_token = data.get("id_token") # pode ser None se não enviado
    
    if not id_token:
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401


    try:
        # Verifica o token com tolerância para clock skew
        # Se falhar com "too early", tenta novamente após um pequeno delay
        decoded_token = None
        max_retries = 3
        retry_count = 0
        import time
        
        while retry_count < max_retries:
            try:
                decoded_token = auth.verify_id_token(id_token, check_revoked=False)
                break
            except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError) as e:
                # Erros específicos do Firebase que não são clock skew - re-raise imediatamente
                raise
            except Exception as e:
                error_str = str(e).lower()
                # Verifica se é o erro de "too early" ou clock skew
                if ("too early" in error_str or "clock" in error_str) and retry_count < max_retries - 1:
                    time.sleep(0.5)  # Espera 500ms antes de tentar novamente
                    retry_count += 1
                    print(f"Tentativa {retry_count} de verificação do token após delay (clock skew)...")
                    continue
                else:
                    # Se não for erro de clock skew ou se já tentou muitas vezes, re-raise
                    raise
        
        if not decoded_token:
            return jsonify({"erro": "Falha ao verificar token após várias tentativas"}), 401
            
        uid = decoded_token['uid']        
        conn = get_db() # Obtém a conexão do pool
        cur = conn.cursor()
        # Buscar dados do usuário
        cur.execute("""
            SELECT id, nome, email, cpf, data_nascimento, criado_em, telefone
            FROM usuarios WHERE firebase_uid = %s
        """, (uid,))
        user = cur.fetchone()

        if user is None:
            cur.close()
            return jsonify({"erro": "Usuário não encontrado em seu sistema. Por favor, registre-se."}), 404

        cur.close()

        session['uid'] = uid
        return jsonify({"mensagem": "Login efetuado com sucesso"}), 200
    except auth.InvalidIdTokenError as e:
        print(f"Token inválido: {e}")
        return jsonify({"erro": "Token inválido"}), 401
    except auth.ExpiredIdTokenError as e:
        print(f"Token expirado: {e}")
        return jsonify({"erro": "Token expirado"}), 401
    except Exception as e:
        print(f"Erro ao consultar usuário: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Erro interno do servidor ao efetuar login: {str(e)}"}), 500