"""
Service para requisições à API do Bling
========================================

Camada de abstração para integração com API do Bling, incluindo:
- Retry automático com backoff exponencial
- Tratamento de erros padronizado
- Rate limiting
- Logs estruturados
- Idempotência
"""
from flask import current_app
import requests
import json
from .db import get_db
import psycopg2.extras
from datetime import datetime, timedelta
import base64
import time
from typing import Dict, Optional, Any, Tuple
from enum import Enum


class BlingErrorType(Enum):
    """Tipos de erros do Bling"""
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    NOT_FOUND_ERROR = "not_found_error"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class BlingAPIError(Exception):
    """Exceção customizada para erros da API do Bling"""
    def __init__(self, message: str, status_code: int = None, 
                 error_type: BlingErrorType = BlingErrorType.UNKNOWN_ERROR,
                 error_details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.error_details = error_details or {}
        super().__init__(self.message)


class BlingRateLimiter:
    """
    Rate Limiter para API do Bling
    
    Bling tem limite de ~100 requisições/minuto
    Implementa delay automático entre requisições
    """
    def __init__(self, min_delay_seconds: float = 0.5):
        self.min_delay_seconds = min_delay_seconds
        self.last_request_time = 0.0
    
    def wait_if_needed(self):
        """Aguarda tempo mínimo entre requisições"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay_seconds:
            sleep_time = self.min_delay_seconds - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


# Instância global do rate limiter
_rate_limiter = BlingRateLimiter(min_delay_seconds=0.5)


def get_valid_access_token() -> str:
    """
    Obtém access token válido do banco de dados
    Renova automaticamente se expirado (usando refresh_token)
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT access_token, refresh_token, expires_at, token_type
            FROM bling_tokens
            WHERE id = 1
        """)
        
        token_data = cur.fetchone()
        
        if not token_data:
            raise ValueError("Bling não autorizado. Use /api/bling/authorize")
        
        # Verificar se token expirou (com margem de 5 minutos)
        expires_at = token_data['expires_at']
        if expires_at and datetime.now() + timedelta(minutes=5) > expires_at:
            # Token expirado ou próximo de expirar - tentar renovar
            current_app.logger.info("Token Bling expirado ou próximo de expirar. Tentando renovar...")
            
            refresh_token = token_data.get('refresh_token')
            if refresh_token:
                new_tokens = refresh_bling_token(refresh_token)
                
                if new_tokens:
                    # Atualizar tokens no banco
                    new_expires_at = datetime.now() + timedelta(seconds=new_tokens.get('expires_in', 3600))
                    cur.execute("""
                        UPDATE bling_tokens
                        SET access_token = %s,
                            refresh_token = %s,
                            expires_at = %s,
                            updated_at = NOW()
                        WHERE id = 1
                    """, (
                        new_tokens['access_token'],
                        new_tokens.get('refresh_token', refresh_token),
                        new_expires_at
                    ))
                    conn.commit()
                    
                    current_app.logger.info("✅ Token Bling renovado com sucesso")
                    return new_tokens['access_token']
                else:
                    current_app.logger.warning("⚠️ Falha ao renovar token. Usando token expirado.")
        
        return token_data['access_token']
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter access token: {e}")
        raise
    finally:
        cur.close()


def refresh_bling_token(refresh_token: str) -> dict:
    """
    Renova access token usando refresh token
    """
    BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
    
    client_id = current_app.config['BLING_CLIENT_ID']
    client_secret = current_app.config['BLING_CLIENT_SECRET']
    
    # Basic Auth
    credentials = f"{client_id}:{client_secret}"
    credentials_b64 = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
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
        
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error(f"Erro ao renovar token: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro na requisição de renovação: {e}")
        return None


def _classify_bling_error(response: requests.Response) -> Tuple[BlingErrorType, str]:
    """
    Classifica erro da API do Bling baseado na resposta
    
    Returns:
        Tuple (error_type, error_message)
    """
    status_code = response.status_code
    
    try:
        error_data = response.json()
        error_info = error_data.get('error', {})
        error_message = error_info.get('description') or error_info.get('message') or response.text
        error_type_str = error_info.get('type', '')
        
        if status_code == 401:
            return BlingErrorType.AUTHENTICATION_ERROR, error_message or "Token inválido ou expirado"
        elif status_code == 404:
            return BlingErrorType.NOT_FOUND_ERROR, error_message or "Recurso não encontrado"
        elif status_code == 429:
            return BlingErrorType.RATE_LIMIT_ERROR, error_message or "Rate limit excedido"
        elif status_code >= 500:
            return BlingErrorType.SERVER_ERROR, error_message or "Erro no servidor Bling"
        elif "VALIDATION_ERROR" in error_type_str or status_code == 400:
            return BlingErrorType.VALIDATION_ERROR, error_message or "Erro de validação"
        else:
            return BlingErrorType.UNKNOWN_ERROR, error_message or f"Erro HTTP {status_code}"
    except:
        # Se não conseguir parsear JSON, retornar erro genérico
        if status_code == 401:
            return BlingErrorType.AUTHENTICATION_ERROR, "Token inválido ou expirado"
        elif status_code == 429:
            return BlingErrorType.RATE_LIMIT_ERROR, "Rate limit excedido"
        elif status_code >= 500:
            return BlingErrorType.SERVER_ERROR, f"Erro no servidor Bling ({status_code})"
        else:
            return BlingErrorType.UNKNOWN_ERROR, f"Erro HTTP {status_code}: {response.text[:200]}"


def _should_retry(status_code: int, attempt: int, max_retries: int) -> bool:
    """
    Decide se deve tentar novamente baseado no status code
    
    Retry para:
    - 429 (Rate Limit)
    - 500-503 (Server Errors)
    - Timeout/Network errors
    """
    if attempt >= max_retries:
        return False
    
    # Sempre retry em rate limit (mas com delay maior)
    if status_code == 429:
        return True
    
    # Retry em erros de servidor (mas não mais que 3 vezes)
    if 500 <= status_code <= 503:
        return attempt < 3
    
    return False


def _calculate_backoff_delay(attempt: int, base_delay: float = 1.0, 
                             max_delay: float = 60.0, is_rate_limit: bool = False) -> float:
    """
    Calcula delay exponencial para retry
    
    Args:
        attempt: Número da tentativa (0-indexed)
        base_delay: Delay base em segundos
        max_delay: Delay máximo em segundos
        is_rate_limit: Se True, usa delay maior para rate limit
    """
    if is_rate_limit:
        # Para rate limit, aguardar mais tempo (60s, 120s, 180s)
        delay = 60.0 * (attempt + 1)
    else:
        # Backoff exponencial: 1s, 2s, 4s, 8s...
        delay = base_delay * (2 ** attempt)
    
    return min(delay, max_delay)


def make_bling_api_request(method: str, endpoint: str, max_retries: int = 3,
                           retry_on_rate_limit: bool = True, **kwargs) -> requests.Response:
    """
    Faz requisição autenticada para API do Bling com retry automático
    
    Args:
        method: Método HTTP (GET, POST, PUT, DELETE)
        endpoint: Endpoint da API (ex: '/produtos', '/pedidos/vendas')
        max_retries: Número máximo de tentativas (padrão: 3)
        retry_on_rate_limit: Se True, faz retry em rate limit (padrão: True)
        **kwargs: Argumentos adicionais para requests (json, params, etc.)
    
    Returns:
        Response object da requisição
    
    Raises:
        BlingAPIError: Em caso de erro na requisição
    """
    BLING_API_BASE_URL = "https://www.bling.com.br/Api/v3"
    
    # Rate limiting
    _rate_limiter.wait_if_needed()
    
    # Obter token
    access_token = get_valid_access_token()
    
    # Preparar headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Mesclar com headers customizados se fornecidos
    if 'headers' in kwargs:
        headers.update(kwargs['headers'])
        del kwargs['headers']
    
    kwargs['headers'] = headers
    url = f"{BLING_API_BASE_URL}{endpoint}"
    
    # Log da requisição
    current_app.logger.info(f"🌐 Bling API Request: {method} {endpoint}")
    
    last_exception = None
    
    # Loop de retry
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            
            # Log da resposta
            current_app.logger.debug(
                f"   → Status: {response.status_code} "
                f"(tentativa {attempt + 1}/{max_retries + 1})"
            )
            
            # Sucesso
            if 200 <= response.status_code < 300:
                current_app.logger.info(f"✅ Bling API: {method} {endpoint} - OK ({response.status_code})")
                return response
            
            # Token expirado - renovar e tentar novamente (apenas uma vez)
            if response.status_code == 401 and attempt == 0:
                current_app.logger.warning("⚠️ Token expirado. Renovando e tentando novamente...")
                access_token = get_valid_access_token()  # Força renovação
                headers['Authorization'] = f'Bearer {access_token}'
                kwargs['headers'] = headers
                continue  # Tentar novamente sem incrementar attempt
            
            # Verificar se deve fazer retry
            if _should_retry(response.status_code, attempt, max_retries):
                error_type, error_msg = _classify_bling_error(response)
                is_rate_limit = (response.status_code == 429)
                
                delay = _calculate_backoff_delay(attempt, is_rate_limit=is_rate_limit)
                
                current_app.logger.warning(
                    f"⚠️ Erro {response.status_code} na requisição. "
                    f"Tentando novamente em {delay:.1f}s... "
                    f"(tentativa {attempt + 1}/{max_retries + 1})"
                )
                
                time.sleep(delay)
                continue
            
            # Erro que não deve ser retried ou já esgotou tentativas
            error_type, error_msg = _classify_bling_error(response)
            
            error_data = {}
            try:
                error_data = response.json()
                current_app.logger.error(f"📋 Response JSON completo: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                
                error_details = error_data.get('error', {})
                
                # Tentar extrair erros de validação mais detalhados
                if 'error' in error_data:
                    error_obj = error_data['error']
                    if isinstance(error_obj, dict):
                        # Bling pode retornar array de erros em 'fields' para validação
                        if 'fields' in error_obj:
                            fields_errors = error_obj['fields']
                            if isinstance(fields_errors, list):
                                error_details['fields'] = fields_errors
                                # Extrair mensagens de cada campo com erro
                                field_messages = []
                                for field_error in fields_errors:
                                    if isinstance(field_error, dict):
                                        field_msg = f"{field_error.get('element', 'unknown')}: {field_error.get('msg', 'Erro desconhecido')}"
                                        field_messages.append(field_msg)
                                if field_messages:
                                    error_msg = f"{error_msg}\n📋 Detalhes: " + "\n".join(field_messages)
                        
                        # Extrair descrição mais detalhada se disponível
                        if 'description' in error_obj:
                            error_details['description'] = error_obj['description']
                        if 'message' in error_obj:
                            error_details['message'] = error_obj['message']
                
                # Log completo do erro
                current_app.logger.error(
                    f"❌ Bling API Error: {method} {endpoint} - {error_type.value} "
                    f"({response.status_code}): {error_msg}"
                )
                
            except Exception as parse_error:
                error_details = {'raw_response': response.text[:2000]}
                current_app.logger.error(f"❌ Erro ao parsear resposta de erro do Bling: {parse_error}")
                current_app.logger.error(f"📋 Response text completo ({len(response.text)} chars): {response.text[:2000]}")
            
            # Sempre logar a resposta completa
            current_app.logger.error(
                f"❌ Bling API Error: {method} {endpoint} - {error_type.value} "
                f"({response.status_code}): {error_msg}"
            )
            
            raise BlingAPIError(
                message=error_msg,
                status_code=response.status_code,
                error_type=error_type,
                error_details=error_details
            )
            
        except BlingAPIError:
            # Re-raise erros do Bling
            raise
        
        except requests.exceptions.Timeout as e:
            last_exception = e
            if attempt < max_retries:
                delay = _calculate_backoff_delay(attempt)
                current_app.logger.warning(
                    f"⏱️ Timeout na requisição. Tentando novamente em {delay:.1f}s..."
                )
                time.sleep(delay)
                continue
            else:
                current_app.logger.error(f"❌ Timeout após {max_retries + 1} tentativas")
                raise BlingAPIError(
                    message=f"Timeout na requisição ao Bling: {str(e)}",
                    error_type=BlingErrorType.NETWORK_ERROR
                )
        
        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < max_retries:
                delay = _calculate_backoff_delay(attempt)
                current_app.logger.warning(
                    f"🔌 Erro de rede. Tentando novamente em {delay:.1f}s..."
                )
                time.sleep(delay)
                continue
            else:
                current_app.logger.error(f"❌ Erro de rede após {max_retries + 1} tentativas: {e}")
                raise BlingAPIError(
                    message=f"Erro de rede ao conectar com Bling: {str(e)}",
                    error_type=BlingErrorType.NETWORK_ERROR
                )
    
    # Se chegou aqui, todas as tentativas falharam
    if last_exception:
        raise BlingAPIError(
            message=f"Falha após {max_retries + 1} tentativas: {str(last_exception)}",
            error_type=BlingErrorType.NETWORK_ERROR
        )
    
    raise BlingAPIError(
        message="Falha desconhecida na requisição",
        error_type=BlingErrorType.UNKNOWN_ERROR
    )

