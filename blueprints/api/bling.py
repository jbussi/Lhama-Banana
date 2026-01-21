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
import hmac
from datetime import datetime, timedelta
import json

from ..services import get_db
import psycopg2.extras
from ..services.bling_api_service import BlingAPIError, BlingErrorType
from ..admin.decorators import admin_required_email

bling_bp = Blueprint('bling', __name__, url_prefix='/api/bling')


def verify_bling_webhook_signature(request_body: bytes, signature_header: str) -> bool:
    """
    Verifica a assinatura HMAC do webhook do Bling
    
    Args:
        request_body: Corpo da requisição (bytes)
        signature_header: Valor do header X-Bling-Signature-256 (formato: sha256=<hash>)
    
    Returns:
        True se a assinatura for válida, False caso contrário
    """
    if not signature_header:
        return False
    
    # Extrair o hash do header (formato: sha256=<hash>)
    if not signature_header.startswith('sha256='):
        current_app.logger.warning(f"Formato de assinatura inválido: {signature_header[:50]}")
        return False
    
    received_hash = signature_header[7:]  # Remove 'sha256='
    
    # Obter client_secret do Bling
    client_secret = current_app.config.get('BLING_CLIENT_SECRET', '')
    if not client_secret:
        current_app.logger.error("BLING_CLIENT_SECRET não configurado")
        return False
    
    # Calcular hash HMAC-SHA256
    expected_hash = hmac.new(
        client_secret.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    # Comparação segura (evita timing attacks)
    is_valid = hmac.compare_digest(expected_hash, received_hash)
    
    if not is_valid:
        current_app.logger.warning(
            f"Assinatura HMAC inválida. Esperado: {expected_hash[:16]}..., Recebido: {received_hash[:16]}..."
        )
    
    return is_valid


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


# Test endpoints removidos - não essenciais para o escopo atual

# Debug endpoints removidos - não essenciais para o escopo atual

@bling_bp.route('/produtos/sync/<int:produto_id>', methods=['POST'])
def sync_product(produto_id: int):
    """
    Sincroniza um produto específico com Bling
    """
    from ..services.bling_product_service import sync_product_to_bling
    import traceback
    
    try:
        current_app.logger.info(f"[ENDPOINT] Iniciando sincronização do produto {produto_id}")
        
        # Validar se produto_id é válido
        if not produto_id or produto_id <= 0:
            return jsonify({
                'success': False,
                'error': 'ID do produto inválido',
                'produto_id': produto_id
            }), 400
        
        result = sync_product_to_bling(produto_id)
        
        current_app.logger.info(f"[ENDPOINT] Resultado da sincronização: success={result.get('success')}, error={result.get('error', 'N/A')}")
        
        # Garantir que result é um dict válido
        if not isinstance(result, dict):
            current_app.logger.error(f"[ENDPOINT] Resultado não é um dict: {type(result)}")
            result = {
                'success': False,
                'error': 'Resultado inválido do serviço',
                'produto_id': produto_id
            }
        
        if result.get('success'):
            response = jsonify(result)
            current_app.logger.info(f"[ENDPOINT] Retornando sucesso: {response.get_data(as_text=True)}")
            return response, 200
        else:
            # Garantir que sempre retorna um corpo de resposta válido
            error_response = {
                'success': False,
                'error': result.get('error', 'Erro desconhecido'),
                'details': result.get('details', []),
                'produto_id': produto_id
            }
            
            # Se details for uma lista, converter para string se necessário para JSON
            if isinstance(error_response['details'], list) and len(error_response['details']) > 0:
                # Manter como lista, JSON pode serializar
                pass
            
            current_app.logger.warning(f"[ENDPOINT] Falha ao sincronizar produto {produto_id}: {error_response}")
            response = jsonify(error_response)
            current_app.logger.info(f"[ENDPOINT] Retornando erro 400: {response.get_data(as_text=True)}")
            return response, 400
            
    except Exception as e:
        error_msg = str(e)
        error_traceback = traceback.format_exc()
        current_app.logger.error(f"[ENDPOINT] Exceção ao sincronizar produto {produto_id}: {error_msg}\n{error_traceback}", exc_info=True)
        
        error_response = {
            'success': False,
            'error': error_msg,
            'produto_id': produto_id,
            'type': type(e).__name__
        }
        
        try:
            response = jsonify(error_response)
            return response, 500
        except Exception as json_error:
            current_app.logger.error(f"[ENDPOINT] Erro ao serializar JSON: {json_error}")
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor',
                'produto_id': produto_id
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


# Sincronização de preços do Bling removida - preços são gerenciados localmente

@bling_bp.route('/categorias', methods=['GET'])
def list_bling_categories():
    """
    Lista categorias do Bling (sem sincronizar)
    """
    from ..services.bling_product_service import fetch_categories_from_bling
    
    try:
        result = fetch_categories_from_bling()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                **result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro ao buscar categorias'),
                **result
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar categorias do Bling: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/produtos/debug', methods=['GET'])
def debug_bling_products():
    """
    Endpoint de debug para ver a estrutura dos produtos do Bling
    Retorna um produto bruto para análise, incluindo campos customizados extraídos
    """
    from flask import request
    from ..services.bling_product_service import fetch_products_from_bling, extract_custom_fields_from_bling_product
    
    try:
        limit = request.args.get('limit', 5, type=int)
        result = fetch_products_from_bling(limit=limit)
        
        if result.get('success') and result.get('products'):
            # Retornar primeiro produto para debug
            primeiro_produto = result['products'][0]
            
            # Extrair campos customizados para mostrar no debug
            campos_customizados = extract_custom_fields_from_bling_product(primeiro_produto)
            
            return jsonify({
                'success': True,
                'total_products': result.get('total', 0),
                'sample_product': primeiro_produto,
                'product_keys': list(primeiro_produto.keys()) if isinstance(primeiro_produto, dict) else [],
                'custom_fields_extracted': campos_customizados,
                'custom_fields_raw': (
                    primeiro_produto.get('camposCustomizados') or
                    primeiro_produto.get('campos_customizados') or
                    primeiro_produto.get('customFields') or
                    'Nenhum campo customizado encontrado'
                )
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhum produto encontrado no Bling',
                'error': result.get('error'),
                'total': result.get('total', 0)
            }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar produtos para debug: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/produtos/import', methods=['POST'])
@bling_bp.route('/produtos/import-from-bling', methods=['POST'])
def import_products_from_bling():
    """
    ⚠️ DESABILITADO: Esta funcionalidade não está mais disponível.
    
    Segundo a nova arquitetura:
    - Produtos são criados APENAS no sistema local (Strapi/admin)
    - O Bling recebe produtos já criados (via POST /api/bling/produtos/sync/<produto_id>)
    - O Bling NÃO cria nem altera estrutura de produtos
    
    Use: POST /api/bling/produtos/sync/<produto_id> para enviar produto local para o Bling
    """
    return jsonify({
        'success': False,
        'error': 'Importação de produtos do Bling foi desabilitada. Produtos devem ser criados localmente e enviados para o Bling.',
        'message': 'Use POST /api/bling/produtos/sync/<produto_id> para enviar produto para o Bling'
    }), 410  # 410 Gone - recurso não está mais disponível


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
        
        # Normalizar retorno: success é booleano, success_count é número
        if isinstance(result.get('success'), bool) and not result.get('success'):
            # Erro na execução
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro desconhecido'),
                'total': result.get('total', 0),
                'results': result.get('results', [])
            }), 400
        else:
            # Sucesso: normalizar success_count
            return jsonify({
                'success': True,
                'message': 'Sincronização de estoque concluída',
                'total': result.get('total', 0),
                'success_count': result.get('success', 0) if isinstance(result.get('success'), int) else len([r for r in result.get('results', []) if r.get('success')]),
                'errors': result.get('errors', 0),
                'results': result.get('results', [])
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
        
        # Normalizar retorno: success é booleano, success_count é número
        if isinstance(result.get('success'), bool) and not result.get('success'):
            # Erro na execução
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro desconhecido'),
                'total': result.get('total', 0),
                'results': result.get('results', [])
            }), 400
        else:
            # Sucesso: normalizar success_count
            return jsonify({
                'success': True,
                'message': 'Sincronização de estoque concluída',
                'total': result.get('total', 0),
                'success_count': result.get('success', 0) if isinstance(result.get('success'), int) else len([r for r in result.get('results', []) if r.get('success')]),
                'errors': result.get('errors', 0),
                'results': result.get('results', [])
            }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar estoque para Bling: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Endpoint de consistência de estoque removido - não essencial para o escopo atual

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
        estoque_local = None
        estoque_bling = None
        
        if direction in ['both', 'from']:
            # Sincronizar do Bling para banco
            from_result = sync_stock_from_bling(produto_id=produto_id)
            results['from_bling'] = from_result
            if from_result.get('results') and len(from_result.get('results', [])) > 0:
                estoque_local = from_result['results'][0].get('estoque_novo')
        
        if direction in ['both', 'to']:
            # Sincronizar do banco para Bling
            to_result = sync_stock_to_bling(produto_id=produto_id)
            results['to_bling'] = to_result
            if to_result.get('results') and len(to_result.get('results', [])) > 0:
                estoque_bling = to_result['results'][0].get('estoque_enviado')
        
        # Se não temos estoque ainda, buscar do banco
        if estoque_local is None:
            from ..services import get_db
            import psycopg2.extras
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cur.execute("SELECT estoque FROM produtos WHERE id = %s", (produto_id,))
                row = cur.fetchone()
                if row:
                    estoque_local = row['estoque']
            finally:
                cur.close()
        
        return jsonify({
            'success': True,
            'message': 'Sincronização de estoque concluída',
            'estoque_local': estoque_local,
            'estoque_bling': estoque_bling or estoque_local,
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


@bling_bp.route('/pedidos/sync-all', methods=['POST'])
def sync_all_orders():
    """
    Sincroniza todos os pedidos para o Bling
    
    Aceita parâmetro opcional no body:
    - only_pending: Se true, sincroniza apenas pedidos que ainda não foram sincronizados
    """
    from flask import request
    from ..services.bling_order_service import sync_all_orders_to_bling
    
    try:
        only_pending = request.json.get('only_pending', False) if request.is_json else False
        
        result = sync_all_orders_to_bling(only_pending=only_pending)
        
        return jsonify({
            'success': True,
            'message': 'Sincronização de pedidos concluída',
            **result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar pedidos: {e}", exc_info=True)
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


# Financial endpoint removido - não essencial para o escopo atual

# Analytics endpoints removidos - não essenciais para o escopo atual

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


@bling_bp.route('/pedidos/diagnostico/<int:venda_id>', methods=['GET'])
def diagnose_order(venda_id: int):
    """
    Diagnóstico de problemas na sincronização de um pedido
    """
    from ..services.bling_order_service import get_order_for_bling_sync
    from ..services.bling_product_service import get_bling_product_by_local_id
    
    try:
        # Buscar dados da venda
        venda = get_order_for_bling_sync(venda_id)
        
        if not venda:
            return jsonify({
                'success': False,
                'error': f'Pedido {venda_id} não encontrado'
            }), 404
        
        problemas = []
        avisos = []
        
        # Verificar CPF/CNPJ
        fiscal_cpf_cnpj = venda.get('fiscal_cpf_cnpj')
        if not fiscal_cpf_cnpj:
            problemas.append('CPF/CNPJ fiscal ausente')
        else:
            cpf_cnpj_limpo = str(fiscal_cpf_cnpj).replace('.', '').replace('-', '').replace('/', '')
            if len(cpf_cnpj_limpo) not in [11, 14]:
                problemas.append(f'CPF/CNPJ inválido: {fiscal_cpf_cnpj}')
        
        # Verificar CEP
        cep = venda.get('cep_entrega')
        if not cep:
            problemas.append('CEP de entrega ausente')
        
        # Verificar endereço completo
        if not venda.get('rua_entrega'):
            problemas.append('Rua de entrega ausente')
        if not venda.get('numero_entrega'):
            problemas.append('Número de entrega ausente')
        if not venda.get('cidade_entrega'):
            problemas.append('Cidade de entrega ausente')
        if not venda.get('estado_entrega'):
            problemas.append('Estado de entrega ausente')
        
        # Verificar produtos sincronizados
        itens = venda.get('itens', [])
        produtos_nao_sincronizados = []
        for item in itens:
            produto_id = item.get('produto_id')
            if produto_id:
                bling_produto = get_bling_product_by_local_id(produto_id)
                if not bling_produto:
                    produtos_nao_sincronizados.append({
                        'produto_id': produto_id,
                        'nome': item.get('nome_produto_snapshot', 'Produto desconhecido')
                    })
        
        if produtos_nao_sincronizados:
            problemas.append(f'{len(produtos_nao_sincronizados)} produto(s) não sincronizado(s) no Bling')
            avisos.extend([f"Produto ID {p['produto_id']}: {p['nome']}" for p in produtos_nao_sincronizados])
        
        return jsonify({
            'success': True,
            'venda_id': venda_id,
            'codigo_pedido': venda.get('codigo_pedido'),
            'problemas': problemas,
            'avisos': avisos,
            'status': 'ok' if not problemas else 'com_problemas',
            'dados': {
                'fiscal_cpf_cnpj': fiscal_cpf_cnpj,
                'cep_entrega': cep,
                'total_itens': len(itens),
                'produtos_nao_sincronizados': len(produtos_nao_sincronizados)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao diagnosticar pedido {venda_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bling_bp.route('/situacoes/sync', methods=['POST'])
@admin_required_email
def sync_bling_situacoes():
    """
    Sincroniza todas as situações do Bling para o banco de dados local
    
    POST /api/bling/situacoes/sync
    """
    try:
        from ..services.bling_situacao_service import sync_bling_situacoes_to_db
        
        result = sync_bling_situacoes_to_db()
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erro desconhecido')
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar situações do Bling: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e) if current_app.config.get('DEBUG', False) else 'Erro interno'
        }), 500


@bling_bp.route('/situacoes', methods=['GET'])
@admin_required_email
def list_bling_situacoes():
    """
    Lista todas as situações do Bling sincronizadas no banco
    
    GET /api/bling/situacoes
    """
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    bling_situacao_id,
                    nome,
                    cor,
                    status_site,
                    ativo,
                    criado_em,
                    atualizado_em
                FROM bling_situacoes
                ORDER BY nome
            """)
            
            situacoes = cur.fetchall()
            
            return jsonify({
                'success': True,
                'total': len(situacoes),
                'situacoes': [dict(s) for s in situacoes]
            }), 200
            
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"Erro ao listar situações do Bling: {e}")
        return jsonify({
            'success': False,
            'error': str(e) if current_app.config.get('DEBUG', False) else 'Erro interno'
        }), 500


@bling_bp.route('/situacoes/<int:situacao_id>/map', methods=['POST'])
@admin_required_email
def update_situacao_mapping(situacao_id: int):
    """
    Atualiza o mapeamento de uma situação do Bling para status do site
    
    POST /api/bling/situacoes/<situacao_id>/map
    Body: {"status_site": "em_processamento"}
    """
    try:
        data = request.get_json()
        status_site = data.get('status_site')
        
        if not status_site:
            return jsonify({
                'success': False,
                'error': 'status_site é obrigatório'
            }), 400
        
        from ..services.bling_situacao_service import update_situacao_mapping
        
        updated = update_situacao_mapping(situacao_id, status_site)
        
        if updated:
            return jsonify({
                'success': True,
                'message': f'Mapeamento atualizado: Situação {situacao_id} → {status_site}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Situação não encontrada ou erro ao atualizar'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar mapeamento de situação: {e}")
        return jsonify({
            'success': False,
            'error': str(e) if current_app.config.get('DEBUG', False) else 'Erro interno'
        }), 500


@bling_bp.route('/pedidos/approve/<int:venda_id>', methods=['POST'])
def approve_order(venda_id: int):
    """
    Aprova pedido no Bling, mudando situação para 'E' (Em aberto)
    
    Esta operação muda o pedido de 'P' (Pendente) para 'E' (Em aberto),
    indicando que o pedido foi aprovado e está pronto para processamento/envio.
    """
    from ..services.bling_order_service import approve_order_in_bling
    
    try:
        result = approve_order_in_bling(venda_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao aprovar pedido {venda_id}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

