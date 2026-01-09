"""
Integração Bling - OAuth 2.0 e API
==================================

Este módulo implementa a integração OAuth 2.0 com o Bling e fornece
endpoints para autorização e callback.

Fluxo OAuth:
1. GET /api/bling/authorize - Redireciona para página de autorização do Bling
2. GET /api/bling/callback - Recebe código de autorização e troca por tokens
3. POST /api/bling/tokens - Informações sobre tokens armazenados
4. POST /api/bling/revoke - Revoga autorização (desconectar)
"""
from flask import Blueprint, request, jsonify, redirect, current_app, session
from urllib.parse import urlencode
import requests
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
import json

from ..services import get_db
import psycopg2.extras
from ..services.bling_api_service import BlingAPIError, BlingErrorType

bling_bp = Blueprint('bling', __name__, url_prefix='/api/bling')


def generate_state_token() -> str:
    """
    Gera token state para proteção CSRF
    """
    return secrets.token_urlsafe(32)


def store_state_token(state: str, user_id: str = None):
    """
    Armazena state token temporariamente (para validação no callback)
    Usa session ou pode usar Redis/banco para armazenamento temporário
    """
    if 'bling_oauth_states' not in session:
        session['bling_oauth_states'] = {}
    
    session['bling_oauth_states'][state] = {
        'user_id': user_id,
        'created_at': datetime.now().isoformat()
    }
    session.modified = True


def validate_state_token(state: str) -> bool:
    """
    Valida state token (proteção CSRF)
    """
    if 'bling_oauth_states' not in session:
        return False
    
    states = session.get('bling_oauth_states', {})
    
    if state not in states:
        return False
    
    # Verificar expiração (5 minutos)
    state_data = states[state]
    created_at = datetime.fromisoformat(state_data['created_at'])
    
    if datetime.now() - created_at > timedelta(minutes=5):
        # Remover token expirado
        del session['bling_oauth_states'][state]
        session.modified = True
        return False
    
    # Remover token após uso (one-time use)
    del session['bling_oauth_states'][state]
    session.modified = True
    
    return True


@bling_bp.errorhandler(BlingAPIError)
def handle_bling_api_error(e: BlingAPIError):
    """
    Error handler padronizado para erros da API Bling
    """
    current_app.logger.error(
        f"❌ BlingAPIError: {e.error_type.value} - {e.message} "
        f"(Status: {e.status_code})"
    )
    
    # Mapear tipos de erro para status HTTP
    status_code_map = {
        BlingErrorType.AUTHENTICATION_ERROR: 401,
        BlingErrorType.VALIDATION_ERROR: 400,
        BlingErrorType.RATE_LIMIT_ERROR: 429,
        BlingErrorType.NOT_FOUND_ERROR: 404,
        BlingErrorType.SERVER_ERROR: 502,  # Bad Gateway
        BlingErrorType.NETWORK_ERROR: 503,  # Service Unavailable
        BlingErrorType.UNKNOWN_ERROR: 500
    }
    
    http_status = e.status_code or status_code_map.get(e.error_type, 500)
    
    return jsonify({
        'success': False,
        'error': e.error_type.value,
        'message': e.message,
        'status_code': e.status_code,
        'details': e.error_details if current_app.config.get('DEBUG', False) else None
    }), http_status


@bling_bp.route('/authorize', methods=['GET'])
def authorize_bling():
    """
    Inicia fluxo OAuth 2.0 do Bling
    
    Redireciona o usuário para a página de autorização do Bling.
    Após autorização, o Bling redireciona para /api/bling/callback
    """
    # URLs fixas do Bling
    BLING_AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
    
    # Scopes necessários
    BLING_SCOPES = [
        'produtos',      # Gerenciar produtos
        'pedidos',       # Gerenciar pedidos de venda
        'nfe',           # Emitir NF-e
        'estoques',      # Controlar estoque
        'contatos',      # Gerenciar clientes
        'financeiro'     # Contas a receber/pagar
    ]
    
    # Verificar se credenciais estão configuradas
    client_id = current_app.config.get('BLING_CLIENT_ID')
    redirect_uri = current_app.config.get('BLING_REDIRECT_URI')
    
    if not client_id:
        return jsonify({
            'error': 'BLING_CLIENT_ID não configurado',
            'message': 'Configure BLING_CLIENT_ID nas variáveis de ambiente'
        }), 500
    
    if not redirect_uri:
        return jsonify({
            'error': 'BLING_REDIRECT_URI não configurado',
            'message': 'Configure BLING_REDIRECT_URI nas variáveis de ambiente'
        }), 500
    
    # Gerar state token (proteção CSRF)
    state = generate_state_token()
    store_state_token(state)
    
    # Parâmetros para autorização
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(BLING_SCOPES),
        'state': state
    }
    
    # Construir URL de autorização
    auth_url = f"{BLING_AUTH_URL}?{urlencode(params)}"
    
    current_app.logger.info(f"Iniciando autorização Bling. State: {state[:16]}...")
    
    # Redirecionar para página de autorização do Bling
    return redirect(auth_url)


@bling_bp.route('/callback', methods=['GET'])
def bling_callback():
    """
    Callback OAuth - Recebe código de autorização do Bling
    
    Este endpoint é chamado pelo Bling após o usuário autorizar a aplicação.
    Troca o código de autorização por access token e refresh token.
    """
    # Obter parâmetros da URL
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # Verificar se houve erro na autorização
    if error:
        current_app.logger.error(f"Erro na autorização Bling: {error} - {error_description}")
        return jsonify({
            'error': 'Erro na autorização',
            'details': error_description or error
        }), 400
    
    # Verificar se code foi fornecido
    if not code:
        current_app.logger.error("Callback Bling sem código de autorização")
        return jsonify({
            'error': 'Código de autorização não fornecido'
        }), 400
    
    # Validar state token (proteção CSRF)
    if not state or not validate_state_token(state):
        current_app.logger.error("State token inválido ou expirado")
        return jsonify({
            'error': 'State token inválido ou expirado'
        }), 400
    
    try:
        # Trocar código por tokens
        token_data = exchange_code_for_token(code)
        
        if not token_data:
            return jsonify({
                'error': 'Falha ao obter tokens do Bling'
            }), 500
        
        # Armazenar tokens
        stored = store_bling_tokens(
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            expires_in=token_data.get('expires_in', 3600),
            token_type=token_data.get('token_type', 'Bearer')
        )
        
        if stored:
            current_app.logger.info("✅ Tokens Bling armazenados com sucesso")
            
            # Retornar sucesso (pode redirecionar para página de sucesso)
            return jsonify({
                'success': True,
                'message': 'Autorização Bling concluída com sucesso',
                'access_token_preview': token_data['access_token'][:20] + '...',
                'expires_in': token_data.get('expires_in'),
                'redirect': '/admin/bling'  # Pode redirecionar para página admin
            }), 200
        else:
            return jsonify({
                'error': 'Falha ao armazenar tokens'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Erro no callback Bling: {e}", exc_info=True)
        return jsonify({
            'error': 'Erro ao processar autorização',
            'message': str(e)
        }), 500


def exchange_code_for_token(code: str) -> dict:
    """
    Troca código de autorização por access token e refresh token
    
    O Bling requer autenticação Basic Auth com client_id:client_secret
    """
    BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
    
    client_id = current_app.config['BLING_CLIENT_ID']
    client_secret = current_app.config['BLING_CLIENT_SECRET']
    
    # Criar Basic Auth header (client_id:client_secret em base64)
    credentials = f"{client_id}:{client_secret}"
    credentials_b64 = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': current_app.config['BLING_REDIRECT_URI']
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'Authorization': f'Basic {credentials_b64}'
    }
    
    try:
        response = requests.post(
            BLING_TOKEN_URL,
            data=data,
            headers=headers,
            timeout=30
        )
        
        current_app.logger.info(f"Resposta token Bling: Status {response.status_code}")
        
        if response.status_code != 200:
            current_app.logger.error(f"Erro ao obter token: {response.status_code} - {response.text}")
            return None
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro na requisição de token: {e}")
        return None


def store_bling_tokens(access_token: str, refresh_token: str = None, 
                      expires_in: int = 3600, token_type: str = 'Bearer') -> bool:
    """
    Armazena tokens do Bling no banco de dados
    """
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verificar se tabela existe, criar se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bling_tokens (
                id SERIAL PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type VARCHAR(20) DEFAULT 'Bearer',
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT unique_bling_token CHECK (id = 1)
            );
            
            -- Criar índice único para garantir apenas um registro
            CREATE UNIQUE INDEX IF NOT EXISTS idx_bling_tokens_single ON bling_tokens ((1));
        """)
        
        conn.commit()
        
        # Inserir ou atualizar token (apenas um registro permitido)
        cur.execute("""
            INSERT INTO bling_tokens (id, access_token, refresh_token, token_type, expires_at, updated_at)
            VALUES (1, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE
            SET access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_type = EXCLUDED.token_type,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
        """, (access_token, refresh_token, token_type, expires_at))
        
        conn.commit()
        
        current_app.logger.info(f"Tokens Bling armazenados. Expira em: {expires_at}")
        return True
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao armazenar tokens Bling: {e}", exc_info=True)
        return False
    finally:
        cur.close()


@bling_bp.route('/tokens', methods=['GET'])
def get_bling_tokens_info():
    """
    Retorna informações sobre tokens armazenados (sem expor tokens completos)
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                id,
                LEFT(access_token, 20) || '...' as access_token_preview,
                CASE WHEN refresh_token IS NOT NULL 
                     THEN LEFT(refresh_token, 20) || '...' 
                     ELSE NULL END as refresh_token_preview,
                token_type,
                expires_at,
                created_at,
                updated_at,
                CASE 
                    WHEN expires_at > NOW() THEN 'Válido'
                    ELSE 'Expirado'
                END as status
            FROM bling_tokens
            WHERE id = 1
        """)
        
        token_info = cur.fetchone()
        
        if not token_info:
            return jsonify({
                'authorized': False,
                'message': 'Bling não autorizado. Use /api/bling/authorize para autorizar.'
            }), 200
        
        return jsonify({
            'authorized': True,
            'token_type': token_info['token_type'],
            'access_token_preview': token_info['access_token_preview'],
            'refresh_token_preview': token_info['refresh_token_preview'],
            'expires_at': token_info['expires_at'].isoformat() if token_info['expires_at'] else None,
            'status': token_info['status'],
            'created_at': token_info['created_at'].isoformat() if token_info['created_at'] else None,
            'updated_at': token_info['updated_at'].isoformat() if token_info['updated_at'] else None
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar tokens: {e}")
        return jsonify({
            'error': 'Erro ao buscar informações de tokens',
            'message': str(e)
        }), 500
    finally:
        cur.close()


@bling_bp.route('/revoke', methods=['POST'])
def revoke_bling_authorization():
    """
    Revoga autorização do Bling (remove tokens)
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM bling_tokens WHERE id = 1")
        conn.commit()
        
        current_app.logger.info("Autorização Bling revogada")
        
        return jsonify({
            'success': True,
            'message': 'Autorização Bling revogada com sucesso'
        }), 200
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao revogar autorização: {e}")
        return jsonify({
            'error': 'Erro ao revogar autorização',
            'message': str(e)
        }), 500
    finally:
        cur.close()


@bling_bp.route('/status', methods=['GET'])
def bling_status():
    """
    Endpoint para verificar status da integração Bling
    """
    BLING_AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
    
    client_id = current_app.config.get('BLING_CLIENT_ID', '')
    redirect_uri = current_app.config.get('BLING_REDIRECT_URI', '')
    
    info = {
        'client_id_configured': bool(client_id),
        'client_secret_configured': bool(current_app.config.get('BLING_CLIENT_SECRET')),
        'redirect_uri': redirect_uri,
        'authorize_url': f"{BLING_AUTH_URL}?client_id={client_id or 'NOT_SET'}&redirect_uri={redirect_uri or 'NOT_SET'}"
    }
    
    return jsonify(info), 200


@bling_bp.errorhandler(BlingAPIError)
def handle_bling_api_error(e: BlingAPIError):
    """
    Error handler padronizado para erros da API Bling
    """
    current_app.logger.error(
        f"❌ BlingAPIError: {e.error_type.value} - {e.message} "
        f"(Status: {e.status_code})"
    )
    
    # Mapear tipos de erro para status HTTP
    status_code_map = {
        BlingErrorType.AUTHENTICATION_ERROR: 401,
        BlingErrorType.VALIDATION_ERROR: 400,
        BlingErrorType.RATE_LIMIT_ERROR: 429,
        BlingErrorType.NOT_FOUND_ERROR: 404,
        BlingErrorType.SERVER_ERROR: 502,  # Bad Gateway
        BlingErrorType.NETWORK_ERROR: 503,  # Service Unavailable
        BlingErrorType.UNKNOWN_ERROR: 500
    }
    
    http_status = e.status_code or status_code_map.get(e.error_type, 500)
    
    return jsonify({
        'success': False,
        'error': e.error_type.value,
        'message': e.message,
        'status_code': e.status_code,
        'details': e.error_details if current_app.config.get('DEBUG', False) else None
    }), http_status


@bling_bp.route('/test', methods=['GET'])
def test_bling_api():
    """
    Endpoint de teste - Faz requisição simples à API Bling para verificar conexão
    """
    from ..services.bling_api_service import make_bling_api_request
    
    try:
        # Testar listando produtos (endpoint simples)
        response = make_bling_api_request('GET', '/produtos', params={'limite': 1})
        
        # Se chegou aqui, a requisição foi bem-sucedida (make_bling_api_request já tratou erros)
        data = response.json()
        return jsonify({
            'success': True,
            'message': 'Conexão com API Bling funcionando!',
            'status_code': response.status_code,
            'products_count': len(data.get('data', [])),
            'sample_data': data.get('data', [])[:1] if data.get('data') else None
        }), 200
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'authentication_required',
            'message': str(e),
            'hint': 'Autorize o Bling primeiro em /api/bling/authorize'
        }), 401
    except Exception as e:
        # Outros erros serão tratados pelo errorhandler se forem BlingAPIError
        current_app.logger.error(f"Erro inesperado no teste da API Bling: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'unknown_error',
            'message': str(e) if current_app.config.get('DEBUG', False) else 'Erro interno'
        }), 500


@bling_bp.route('/produtos/sync/<int:produto_id>', methods=['POST'])
def sync_product(produto_id: int):
    """
    Sincroniza um produto específico com Bling
    """
    from ..services.bling_product_service import sync_product_to_bling
    
    try:
        result = sync_product_to_bling(produto_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar produto {produto_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/produtos/sync-all', methods=['POST'])
def sync_all_products():
    """
    Sincroniza todos os produtos com Bling
    """
    from flask import request
    from ..services.bling_product_service import sync_all_products
    
    try:
        # Parâmetros opcionais
        limit = request.json.get('limit') if request.is_json else None
        only_active = request.json.get('only_active', True) if request.is_json else True
        
        result = sync_all_products(limit=limit, only_active=only_active)
        
        return jsonify({
            'success': True,
            'message': 'Sincronização concluída',
            **result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar produtos: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/produtos/status/<int:produto_id>', methods=['GET'])
def get_product_sync_status(produto_id: int):
    """
    Verifica status de sincronização de um produto
    """
    from ..services.bling_product_service import get_bling_product_by_local_id
    
    try:
        bling_produto = get_bling_product_by_local_id(produto_id)
        
        if bling_produto:
            return jsonify({
                'synced': True,
                'bling_id': bling_produto['bling_id'],
                'bling_codigo': bling_produto['bling_codigo'],
                'status': bling_produto['status_sincronizacao'],
                'ultima_sincronizacao': bling_produto['ultima_sincronizacao'].isoformat() if bling_produto.get('ultima_sincronizacao') else None,
                'erro': bling_produto.get('erro_ultima_sync')
            }), 200
        else:
            return jsonify({
                'synced': False,
                'message': 'Produto não sincronizado com Bling'
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar status: {e}")
        return jsonify({
            'error': str(e)
        }), 500


# Funções de API movidas para bling_api_service.py
# Endpoints de sincronização acima usam essas funções via import


@bling_bp.route('/produtos/import', methods=['POST'])
def import_products_from_bling():
    """
    Importa produtos do Bling para o banco local
    """
    from flask import request
    from ..services.bling_product_service import sync_products_from_bling
    
    try:
        limit = request.json.get('limit', 50) if request.is_json else 50
        
        result = sync_products_from_bling(limit=limit)
        
        return jsonify({
            'success': True,
            'message': 'Importação concluída',
            **result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao importar produtos: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/estoque/sync-from-bling', methods=['POST'])
def sync_stock_from_bling_endpoint():
    """
    Sincroniza estoque do Bling para o banco local
    """
    from flask import request
    from ..services.bling_product_service import sync_stock_from_bling
    
    try:
        produto_id = request.json.get('produto_id') if request.is_json else None
        
        result = sync_stock_from_bling(produto_id=produto_id)
        
        return jsonify({
            'success': True,
            'message': 'Sincronização de estoque concluída',
            **result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar estoque do Bling: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/estoque/sync-to-bling', methods=['POST'])
def sync_stock_to_bling_endpoint():
    """
    Sincroniza estoque do banco local para o Bling
    """
    from flask import request
    from ..services.bling_product_service import sync_stock_to_bling
    
    try:
        produto_id = request.json.get('produto_id') if request.is_json else None
        
        result = sync_stock_to_bling(produto_id=produto_id)
        
        return jsonify({
            'success': True,
            'message': 'Sincronização de estoque concluída',
            **result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar estoque para Bling: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/estoque/consistency', methods=['POST'])
def ensure_stock_consistency_endpoint():
    """
    Garante consistência de estoque entre LhamaBanana e Bling
    """
    from flask import request
    from ..services.bling_stock_service import ensure_stock_consistency
    
    try:
        produto_id = request.json.get('produto_id') if request.is_json else None
        
        result = ensure_stock_consistency(produto_id=produto_id)
        
        return jsonify({
            'success': True,
            'message': 'Verificação de consistência concluída',
            **result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar consistência de estoque: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/estoque/sync/<int:produto_id>', methods=['POST'])
def sync_stock_product(produto_id: int):
    """
    Sincroniza estoque de um produto específico (bidirecional)
    """
    from flask import request
    from ..services.bling_product_service import sync_stock_from_bling, sync_stock_to_bling
    
    try:
        direction = request.json.get('direction', 'both') if request.is_json else 'both'
        
        results = {}
        
        if direction in ['both', 'from']:
            # Sincronizar do Bling para banco
            results['from_bling'] = sync_stock_from_bling(produto_id=produto_id)
        
        if direction in ['both', 'to']:
            # Sincronizar do banco para Bling
            results['to_bling'] = sync_stock_to_bling(produto_id=produto_id)
        
        return jsonify({
            'success': True,
            'message': 'Sincronização de estoque concluída',
            **results
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar estoque: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =====================================================
# ENDPOINTS DE PEDIDOS/VENDAS
# =====================================================

@bling_bp.route('/pedidos/sync/<int:venda_id>', methods=['POST'])
def sync_order(venda_id: int):
    """
    Sincroniza um pedido/venda específico com Bling
    """
    from ..services.bling_order_service import sync_order_to_bling
    
    try:
        result = sync_order_to_bling(venda_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar pedido {venda_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/pedidos/status/<int:venda_id>', methods=['POST'])
def sync_order_status(venda_id: int):
    """
    Sincroniza status do pedido do Bling para o banco local
    """
    from ..services.bling_order_service import sync_order_status_from_bling
    
    try:
        result = sync_order_status_from_bling(venda_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar status do pedido {venda_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/pedidos/status/sync-all', methods=['POST'])
def sync_all_orders_status():
    """
    Sincroniza status de todos os pedidos sincronizados com Bling
    """
    from ..services.bling_order_service import sync_all_orders_status
    
    try:
        result = sync_all_orders_status()
        
        return jsonify({
            'success': True,
            'message': 'Sincronização de status concluída',
            **result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar status dos pedidos: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/pedidos/nfe/emitir/<int:venda_id>', methods=['POST'])
def emit_nfe(venda_id: int):
    """
    Emite NF-e para um pedido/venda específico
    """
    from ..services.bling_nfe_service import emit_nfe_for_order
    
    try:
        result = emit_nfe_for_order(venda_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao emitir NF-e para venda {venda_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/pedidos/nfe/status/<int:venda_id>', methods=['GET'])
def get_nfe_status(venda_id: int):
    """
    Consulta status da NF-e de um pedido/venda
    """
    from ..services.bling_order_service import get_bling_order_by_local_id
    from ..services.bling_nfe_service import check_nfe_status
    
    try:
        bling_pedido = get_bling_order_by_local_id(venda_id)
        
        if not bling_pedido:
            return jsonify({
                'success': False,
                'error': 'Pedido não encontrado no Bling'
            }), 404
        
        result = check_nfe_status(venda_id, bling_pedido['bling_pedido_id'])
        
        return jsonify(result), 200 if result.get('success') else 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao consultar status da NF-e para venda {venda_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/financeiro/conta-receber/<int:venda_id>', methods=['POST'])
def create_account_receivable(venda_id: int):
    """
    Cria conta a receber no Bling para uma venda
    """
    from ..services.bling_financial_service import create_account_receivable_for_order
    
    try:
        result = create_account_receivable_for_order(venda_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao criar conta a receber para venda {venda_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/analytics/dashboard', methods=['GET'])
def get_dashboard():
    """
    Dashboard financeiro com métricas do Bling
    """
    from ..services.bling_analytics_service import get_financial_dashboard
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        result = get_financial_dashboard(start_date, end_date)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar dashboard: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/analytics/vendas/periodo', methods=['GET'])
def get_sales_by_period():
    """
    Vendas agrupadas por período (dia/semana/mês)
    """
    from ..services.bling_analytics_service import get_sales_by_period
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'day')  # day, week, month
    
    try:
        result = get_sales_by_period(start_date, end_date, group_by)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar vendas por período: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/analytics/produtos/top', methods=['GET'])
def get_top_products():
    """
    Produtos mais vendidos
    """
    from ..services.bling_analytics_service import get_top_products
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 10))
    
    try:
        result = get_top_products(start_date, end_date, limit)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar produtos mais vendidos: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/analytics/comparacao', methods=['GET'])
def get_comparison():
    """
    Comparação entre dados locais e Bling
    """
    from ..services.bling_analytics_service import get_local_vs_bling_comparison
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        result = get_local_vs_bling_comparison(start_date, end_date)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        current_app.logger.error(f"Erro ao comparar dados: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/pedidos/info/<int:venda_id>', methods=['GET'])
def get_order_sync_status(venda_id: int):
    """
    Verifica status de sincronização de um pedido
    """
    from ..services.bling_order_service import get_bling_order_by_local_id
    
    try:
        bling_order = get_bling_order_by_local_id(venda_id)
        
        if bling_order:
            return jsonify({
                'synced': True,
                'bling_pedido_id': bling_order['bling_pedido_id'],
                'bling_nfe_id': bling_order.get('bling_nfe_id'),
                'nfe_numero': bling_order.get('nfe_numero'),
                'nfe_status': bling_order.get('nfe_status'),
                'ultima_sincronizacao': bling_order['updated_at'].isoformat() if bling_order.get('updated_at') else None
            }), 200
        else:
            return jsonify({
                'synced': False,
                'message': 'Pedido não sincronizado com Bling'
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar status: {e}")
        return jsonify({
            'error': str(e)
        }), 500

