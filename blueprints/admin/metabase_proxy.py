"""
Proxy reverso para o Metabase Analytics.
Todas as requisições para /analytics/* são redirecionadas para o Metabase.
Protegido com autenticação admin via decorador admin_required_email.
"""

from flask import request, Response, current_app
import requests
from . import admin_bp
from .decorators import admin_required_email

# URL base do Metabase (configurável via variável de ambiente)
# No Docker, usa o nome do serviço para comunicação interna
METABASE_URL = 'http://metabase:3000'

def get_metabase_url():
    """Obtém a URL do Metabase da configuração"""
    return current_app.config.get('METABASE_URL', METABASE_URL)

@admin_bp.route('/analytics', methods=['GET'])
@admin_required_email
def analytics_root():
    """
    Rota raiz do analytics - faz proxy para o Metabase.
    Protegido com autenticação admin.
    """
    metabase_base_url = get_metabase_url()
    # O Metabase tem sua interface em /, então fazemos proxy direto
    metabase_url = f"{metabase_base_url}/"
    
    # Headers básicos
    headers = {}
    for header_name in ['Content-Type', 'Accept', 'Accept-Language', 'Authorization', 'User-Agent', 'Cookie']:
        if header_name in request.headers:
            headers[header_name] = request.headers[header_name]
    
    try:
        resp = requests.get(metabase_url, headers=headers, timeout=30, stream=True, allow_redirects=False)
        
        response_headers = {}
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response_headers[key] = value
        
        content = resp.content
        
        # Ajustar URLs no HTML para funcionar via proxy
        content_type = resp.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            import re
            # Substituir URLs absolutas do Metabase para funcionar via proxy
            content = re.sub(
                rb'(href|src|action)="/(?!analytics/)',
                rb'\1="/analytics/',
                content
            )
            # Ajustar URLs de API do Metabase
            content = re.sub(
                rb'(href|src|action)="/api/',
                rb'\1="/analytics/api/',
                content
            )
        
        actual_content_type = resp.headers.get('Content-Type', 'application/json')
        if resp.status_code >= 400:
            if 'application/json' not in actual_content_type and 'text/html' not in actual_content_type:
                actual_content_type = 'text/plain'
        
        return Response(
            content,
            status=resp.status_code,
            headers=response_headers,
            content_type=actual_content_type
        )
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao fazer proxy para Metabase: {e}")
        return Response(
            f"<html><body><h1>Erro 502</h1><p>Erro ao conectar com Metabase: {str(e)}</p><p>URL: {metabase_url}</p></body></html>",
            status=502,
            content_type='text/html'
        )

@admin_bp.route('/analytics/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@admin_required_email
def metabase_proxy(path):
    """
    Proxy reverso para o Metabase.
    Todas as requisições para /analytics/* são redirecionadas para o Metabase.
    Protegido com autenticação admin.
    """
    
    # URL do Metabase - mapear /analytics/* para /* no Metabase
    metabase_base_url = get_metabase_url()
    
    # Remover 'analytics/' do início do path se existir (evitar duplicação)
    if path.startswith('analytics/'):
        path = path[10:]  # Remove 'analytics/'
    
    # Construir URL do Metabase
    if path:
        metabase_url = f"{metabase_base_url}/{path}"
    else:
        metabase_url = f"{metabase_base_url}/"
    
    # Headers básicos
    headers = {}
    for header_name in ['Content-Type', 'Accept', 'Accept-Language', 'Authorization', 'User-Agent', 'Referer', 'Cookie', 'X-Requested-With']:
        if header_name in request.headers:
            headers[header_name] = request.headers[header_name]
    
    # Preparar dados da requisição
    request_kwargs = {
        'headers': headers,
        'timeout': 30,
        'stream': True,
        'allow_redirects': False,
    }
    
    # Adicionar query string se houver
    if request.args:
        request_kwargs['params'] = request.args
    
    # Adicionar body para métodos que suportam
    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.is_json:
            request_kwargs['json'] = request.get_json()
        elif request.form:
            request_kwargs['data'] = request.form
        elif request.data:
            request_kwargs['data'] = request.data
        elif request.files:
            request_kwargs['files'] = request.files
    
    # Fazer requisição para o Metabase
    try:
        if request.method == 'GET':
            resp = requests.get(metabase_url, **request_kwargs)
        elif request.method == 'POST':
            resp = requests.post(metabase_url, **request_kwargs)
        elif request.method == 'PUT':
            resp = requests.put(metabase_url, **request_kwargs)
        elif request.method == 'DELETE':
            resp = requests.delete(metabase_url, **request_kwargs)
        elif request.method == 'PATCH':
            resp = requests.patch(metabase_url, **request_kwargs)
        elif request.method == 'OPTIONS':
            resp = requests.options(metabase_url, **request_kwargs)
        elif request.method == 'HEAD':
            resp = requests.head(metabase_url, **request_kwargs)
        else:
            current_app.logger.warning(f"Método HTTP não suportado: {request.method}")
            return Response(
                f"Method {request.method} not allowed",
                status=405,
                content_type='text/plain'
            )
        
        # Preparar headers da resposta
        response_headers = {}
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response_headers[key] = value
        
        # Ajustar URLs no conteúdo HTML para funcionar via proxy
        content = resp.content
        content_type = resp.headers.get('Content-Type', '')
        
        if 'text/html' in content_type:
            import re
            # Substituir URLs absolutas do Metabase para funcionar via proxy
            content = re.sub(
                rb'(href|src|action)="/(?!analytics/)',
                rb'\1="/analytics/',
                content
            )
            # Ajustar URLs de API do Metabase
            content = re.sub(
                rb'(href|src|action)="/api/',
                rb'\1="/analytics/api/',
                content
            )
            # Ajustar URLs de assets estáticos
            content = re.sub(
                rb'(href|src)="/app/',
                rb'\1="/analytics/app/',
                content
            )
        
        # Verificar o Content-Type real antes de definir
        actual_content_type = resp.headers.get('Content-Type', 'application/json')
        
        # Se for erro (status >= 400), garantir que o Content-Type está correto
        if resp.status_code >= 400:
            if 'application/json' not in actual_content_type and 'text/html' not in actual_content_type:
                actual_content_type = 'text/plain'
        
        return Response(
            content,
            status=resp.status_code,
            headers=response_headers,
            content_type=actual_content_type
        )
        
    except requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"Erro de conexão com Metabase: {e}")
        current_app.logger.error(f"Tentando conectar em: {metabase_url}")
        current_app.logger.error("Verifique se o Metabase está rodando na porta 3000")
        return Response(
            f"<html><body><h1>Erro 502 - Bad Gateway</h1><p>Não foi possível conectar ao Metabase.</p><p>Verifique se o Metabase está rodando em {metabase_base_url}</p><p>URL tentada: {metabase_url}</p></body></html>",
            status=502,
            content_type='text/html'
        )
    except requests.exceptions.Timeout:
        current_app.logger.error("Timeout ao conectar com Metabase")
        return Response(
            "<html><body><h1>Erro 504 - Gateway Timeout</h1><p>O Metabase demorou muito para responder.</p></body></html>",
            status=504,
            content_type='text/html'
        )
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao fazer proxy para Metabase: {e}")
        current_app.logger.error(f"URL tentada: {metabase_url}")
        return Response(
            f"<html><body><h1>Erro 502 - Bad Gateway</h1><p>Erro ao comunicar com Metabase: {str(e)}</p><p>URL: {metabase_url}</p></body></html>",
            status=502,
            content_type='text/html'
        )


