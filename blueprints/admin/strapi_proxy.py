"""
Proxy reverso para o Strapi Admin.
Todas as requisições para /admin/* são redirecionadas para o Strapi.
Autenticação temporariamente desabilitada para configuração inicial.
"""

from flask import request, Response, current_app
import requests
from . import admin_bp

# URL base do Strapi (configurável via variável de ambiente)
# No Docker, usa o nome do serviço para comunicação interna
STRAPI_URL = 'http://strapi:1337'

def get_strapi_url():
    """Obtém a URL do Strapi da configuração"""
    return current_app.config.get('STRAPI_URL', STRAPI_URL)

@admin_bp.route('/', methods=['GET'])
def admin_root():
    """
    Rota raiz do admin - faz proxy para o Strapi admin.
    Autenticação temporariamente desabilitada para configuração.
    """
    strapi_base_url = get_strapi_url()
    # O Strapi tem seu admin em /admin, então fazemos proxy direto
    strapi_url = f"{strapi_base_url}/admin"
    
    # Headers básicos (sem autenticação por enquanto)
    headers = {}
    for header_name in ['Content-Type', 'Accept', 'Accept-Language', 'Authorization', 'User-Agent']:
        if header_name in request.headers:
            headers[header_name] = request.headers[header_name]
    
    try:
        resp = requests.get(strapi_url, headers=headers, timeout=30, stream=True, allow_redirects=False)
        
        response_headers = {}
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        for key, value in resp.headers.items():
            if key.lower() not in excluded_headers:
                response_headers[key] = value
        
        content = resp.content
        
        # Ajustar URLs no HTML
        content_type = resp.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            import re
            # Remover duplicações primeiro
            content = re.sub(
                rb'(href|src)="/admin/admin/',
                rb'\1="/admin/',
                content
            )
            # Depois substituir URLs que não começam com /admin/
            content = re.sub(
                rb'(href|src)="/(?!admin/|api/|_health|favicon\.ico)',
                rb'\1="/admin/',
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
        current_app.logger.error(f"Erro ao fazer proxy para Strapi: {e}")
        return Response(
            f"<html><body><h1>Erro 502</h1><p>Erro ao conectar com Strapi: {str(e)}</p><p>URL: {strapi_url}</p></body></html>",
            status=502,
            content_type='text/html'
        )

@admin_bp.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def strapi_proxy(path):
    """
    Proxy reverso para o Strapi.
    Todas as requisições para /admin/* são redirecionadas para o Strapi.
    Mapeia /admin/* para /* no Strapi.
    Autenticação temporariamente desabilitada para configuração.
    """
    
    # URL do Strapi - mapear /admin/* para /* no Strapi
    strapi_base_url = get_strapi_url()
    
    # Remover 'admin/' do início do path se existir (evitar duplicação)
    if path.startswith('admin/'):
        path = path[6:]  # Remove 'admin/'
    
    # Construir URL do Strapi
    if path:
        strapi_url = f"{strapi_base_url}/{path}"
    else:
        strapi_url = f"{strapi_base_url}/admin"
    
    # Headers básicos (sem autenticação por enquanto)
    headers = {}
    for header_name in ['Content-Type', 'Accept', 'Accept-Language', 'Authorization', 'User-Agent', 'Referer']:
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
    
    # Fazer requisição para o Strapi
    try:
        if request.method == 'GET':
            resp = requests.get(strapi_url, **request_kwargs)
        elif request.method == 'POST':
            resp = requests.post(strapi_url, **request_kwargs)
        elif request.method == 'PUT':
            resp = requests.put(strapi_url, **request_kwargs)
        elif request.method == 'DELETE':
            resp = requests.delete(strapi_url, **request_kwargs)
        elif request.method == 'PATCH':
            resp = requests.patch(strapi_url, **request_kwargs)
        elif request.method == 'OPTIONS':
            resp = requests.options(strapi_url, **request_kwargs)
        elif request.method == 'HEAD':
            resp = requests.head(strapi_url, **request_kwargs)
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
            # O Strapi retorna URLs com /admin/ porque está configurado assim
            # Quando acessado via proxy Flask em /admin, essas URLs já estão corretas
            # Apenas garantir que não há duplicações e ajustar URLs absolutas
            content = re.sub(
                rb'/admin/admin/',
                rb'/admin/',
                content
            )
            # Substituir apenas URLs absolutas que NÃO são do admin
            # (assets, APIs, etc que o Strapi pode referenciar)
            content = re.sub(
                rb'(href|src|action)="/(?!admin/|api/|_health|favicon\.ico)',
                rb'\1="/admin/',
                content
            )
        
        # Verificar o Content-Type real antes de definir
        actual_content_type = resp.headers.get('Content-Type', 'application/json')
        
        # Se for erro (status >= 400), garantir que o Content-Type está correto
        if resp.status_code >= 400:
            # Se não for HTML e não for JSON, tratar como texto
            if 'application/json' not in actual_content_type and 'text/html' not in actual_content_type:
                actual_content_type = 'text/plain'
        
        return Response(
            content,
            status=resp.status_code,
            headers=response_headers,
            content_type=actual_content_type
        )
        
    except requests.exceptions.ConnectionError as e:
        current_app.logger.error(f"Erro de conexão com Strapi: {e}")
        current_app.logger.error(f"Tentando conectar em: {strapi_url}")
        current_app.logger.error("Verifique se o Strapi está rodando na porta 1337")
        return Response(
            f"<html><body><h1>Erro 502 - Bad Gateway</h1><p>Não foi possível conectar ao Strapi.</p><p>Verifique se o Strapi está rodando em {strapi_base_url}</p><p>URL tentada: {strapi_url}</p></body></html>",
            status=502,
            content_type='text/html'
        )
    except requests.exceptions.Timeout:
        current_app.logger.error("Timeout ao conectar com Strapi")
        return Response(
            "<html><body><h1>Erro 504 - Gateway Timeout</h1><p>O Strapi demorou muito para responder.</p></body></html>",
            status=504,
            content_type='text/html'
        )
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao fazer proxy para Strapi: {e}")
        current_app.logger.error(f"URL tentada: {strapi_url}")
        return Response(
            f"<html><body><h1>Erro 502 - Bad Gateway</h1><p>Erro ao comunicar com Strapi: {str(e)}</p><p>URL: {strapi_url}</p></body></html>",
            status=502,
            content_type='text/html'
        )
