"""
Serviço Centralizado de Autenticação Firebase
==============================================
Centraliza todas as operações relacionadas ao Firebase Authentication.
O Firebase é a fonte de verdade para identidade, este serviço apenas
coordena validações, sincronização com banco local e regras de negócio.
"""

from firebase_admin import auth
from flask import current_app
from typing import Dict, Optional, Tuple
from .user_service import get_user_by_firebase_uid, insert_new_user, update_user_profile_db
from .db import get_db
import logging
import pyotp
import qrcode
import io
import base64

logger = logging.getLogger(__name__)


def verify_firebase_token(id_token: str, check_revoked: bool = False) -> Optional[Dict]:
    """
    Verifica e decodifica um token Firebase.
    Inclui retry logic para lidar com clock skew.
    
    Args:
        id_token: Token JWT do Firebase
        check_revoked: Se True, verifica se o token foi revogado
        
    Returns:
        Dict com dados do token decodificado ou None se inválido
    """
    import time
    
    max_retries = 3  # Reduzido para 3 tentativas (suficiente com delays otimizados)
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            decoded_token = auth.verify_id_token(id_token, check_revoked=check_revoked)
            if retry_count > 0:
                logger.info(f"Token verificado com sucesso após {retry_count} tentativa(s). UID: {decoded_token.get('uid')}, Email: {decoded_token.get('email')}")
            else:
                logger.info(f"Token verificado com sucesso. UID: {decoded_token.get('uid')}, Email: {decoded_token.get('email')}")
            return decoded_token
        except auth.InvalidIdTokenError as e:
            error_str = str(e).lower()
            error_message = str(e)
            # Verificar se é erro de "too early" (clock skew) - mesmo sendo InvalidIdTokenError
            if ("too early" in error_str or "clock" in error_str or "not yet valid" in error_str) and retry_count < max_retries - 1:
                # Tentar extrair a diferença de tempo do erro para calcular delay apropriado
                import re
                delay_match = re.search(r'(\d+)\s*<\s*(\d+)', error_message)
                if delay_match:
                    token_time = int(delay_match.group(1))
                    server_time = int(delay_match.group(2))
                    time_diff = server_time - token_time
                    # Aguardar a diferença + margem de segurança menor
                    wait_time = max(time_diff + 1, 1.5)  # Pelo menos 1.5 segundos, ou diferença + 1
                    logger.warning(f"[RETRY {retry_count + 1}/{max_retries}] Token usado muito cedo (clock skew): diferença de {time_diff}s. Aguardando {wait_time}s...")
                else:
                    # Se não conseguir extrair, usar delay progressivo menor
                    wait_time = 1.5 + (retry_count * 0.5)  # Delay: 1.5s, 2s, 2.5s, 3s, 3.5s
                    logger.warning(f"[RETRY {retry_count + 1}/{max_retries}] Token usado muito cedo (clock skew): {error_message}")
                
                logger.info(f"Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)
                retry_count += 1
                logger.info(f"Tentando novamente (tentativa {retry_count}/{max_retries})...")
                continue
            else:
                # Token inválido por outro motivo ou já tentou todas as vezes - não tentar novamente
                if retry_count >= max_retries - 1:
                    logger.error(f"Token Firebase inválido após {max_retries} tentativas: {e}")
                else:
                    logger.warning(f"Token Firebase inválido (não é clock skew): {e}")
                logger.debug(f"Detalhes do erro: {type(e).__name__}: {str(e)}")
                return None
        except auth.ExpiredIdTokenError as e:
            # Token expirado - não tentar novamente
            logger.warning(f"Token Firebase expirado: {e}")
            return None
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__
            logger.debug(f"Erro ao verificar token (tentativa {retry_count + 1}/{max_retries}): {error_type}: {str(e)}")
            
            # Verifica se é o erro de "too early" ou clock skew
            if ("too early" in error_str or "clock" in error_str or "not yet valid" in error_str) and retry_count < max_retries - 1:
                wait_time = 0.5 * (retry_count + 1)  # Aumenta o delay a cada tentativa
                time.sleep(wait_time)
                retry_count += 1
                logger.debug(f"Tentativa {retry_count} de verificação do token após delay de {wait_time}s (clock skew)...")
                continue
            else:
                # Se não for erro de clock skew ou se já tentou muitas vezes, logar e retornar None
                logger.error(f"Erro ao verificar token Firebase após {retry_count + 1} tentativas: {error_type}: {str(e)}")
                return None
    
    logger.warning("Falha ao verificar token após várias tentativas")
    return None


def sync_user_from_firebase(decoded_token: Dict) -> Tuple[Optional[Dict], bool]:
    """
    Sincroniza dados do usuário do Firebase com o banco local.
    Cria o usuário se não existir, atualiza se necessário.
    
    Args:
        decoded_token: Token decodificado do Firebase
        
    Returns:
        Tuple (user_data, is_new_user)
    """
    uid = decoded_token.get('uid')
    email = decoded_token.get('email', '').lower()
    email_verified = decoded_token.get('email_verified', False)
    display_name = decoded_token.get('name') or decoded_token.get('display_name') or email.split('@')[0]
    
    # Verificar se usuário já existe
    user_data = get_user_by_firebase_uid(uid)
    is_new_user = user_data is None
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        if is_new_user:
            # Criar novo usuário
            cur.execute("""
                INSERT INTO usuarios (firebase_uid, nome, email, email_verificado)
                VALUES (%s, %s, %s, %s)
                RETURNING id, firebase_uid, nome, email, email_verificado, role, criado_em, mfa_enabled, mfa_secret
            """, (uid, display_name, email, email_verified))
            
            result = cur.fetchone()
            conn.commit()
            
            user_data = {
                'id': result[0],
                'firebase_uid': result[1],
                'nome': result[2],
                'email': result[3],
                'email_verificado': result[4],
                'role': result[5] if len(result) > 5 else 'user',
                'criado_em': str(result[6]) if len(result) > 6 else None,
                'mfa_enabled': result[7] if len(result) > 7 else False,
                'mfa_secret': result[8] if len(result) > 8 else None
            }
            
            logger.info(f"Novo usuário criado: {email} (UID: {uid})")
        else:
            # Atualizar dados existentes (especialmente email_verificado)
            # Não atualizar mfa_enabled ou mfa_secret aqui - apenas sincronizar dados do Firebase
            cur.execute("""
                UPDATE usuarios 
                SET email_verificado = %s,
                    email = %s,
                    nome = COALESCE(NULLIF(%s, ''), nome)
                WHERE firebase_uid = %s
                RETURNING id, firebase_uid, nome, email, email_verificado, role, criado_em, mfa_enabled, mfa_secret
            """, (email_verified, email, display_name, uid))
            
            result = cur.fetchone()
            conn.commit()
            
            if result:
                user_data = {
                    'id': result[0],
                    'firebase_uid': result[1],
                    'nome': result[2],
                    'email': result[3],
                    'email_verificado': result[4],
                    'role': result[5] if len(result) > 5 else 'user',
                    'criado_em': str(result[6]) if len(result) > 6 else None,
                    'mfa_enabled': result[7] if len(result) > 7 else False,
                    'mfa_secret': result[8] if len(result) > 8 else None
                }
                
                logger.info(f"Usuário sincronizado: {email} (email_verificado: {email_verified}, mfa_enabled: {user_data.get('mfa_enabled', False)})")
        
        cur.close()
        return user_data, is_new_user
        
    except Exception as e:
        conn.rollback()
        cur.close()
        logger.error(f"Erro ao sincronizar usuário: {e}")
        return None, False


def get_email_verification_link(firebase_uid: str) -> Tuple[bool, Optional[str], str]:
    """
    Gera link de verificação de email usando Firebase Admin SDK.
    Nota: O Firebase envia o email automaticamente quando o usuário
    chama sendEmailVerification() no cliente. Este método gera o link
    caso você queira enviar manualmente via seu próprio serviço de email.
    
    Args:
        firebase_uid: UID do usuário no Firebase
        
    Returns:
        Tuple (success, link, message)
    """
    try:
        user_record = auth.get_user(firebase_uid)
        
        # Gerar link de verificação
        link = auth.generate_email_verification_link(
            email=user_record.email,
            action_code_settings=None
        )
        
        logger.info(f"Link de verificação gerado para {user_record.email}")
        return True, link, "Link gerado com sucesso"
        
    except auth.UserNotFoundError:
        return False, None, "Usuário não encontrado no Firebase"
    except Exception as e:
        logger.error(f"Erro ao gerar link de verificação: {e}")
        return False, None, f"Erro ao gerar link: {str(e)}"


def get_password_reset_link(email: str) -> Tuple[bool, Optional[str], str]:
    """
    Gera link de recuperação de senha usando Firebase Admin SDK.
    Nota: O Firebase envia o email automaticamente quando o usuário
    chama sendPasswordResetEmail() no cliente. Este método gera o link
    caso você queira enviar manualmente via seu próprio serviço de email.
    
    Args:
        email: Email do usuário
        
    Returns:
        Tuple (success, link, message)
    """
    try:
        # Gerar link de reset de senha
        link = auth.generate_password_reset_link(
            email=email,
            action_code_settings=None
        )
        
        logger.info(f"Link de reset de senha gerado para {email}")
        return True, link, "Link gerado com sucesso"
        
    except auth.UserNotFoundError:
        return False, None, "Usuário não encontrado"
    except Exception as e:
        logger.error(f"Erro ao gerar link de reset: {e}")
        return False, None, f"Erro ao gerar link: {str(e)}"


def check_admin_access(user_data: Dict) -> bool:
    """
    Verifica se o usuário tem acesso de administrador.
    
    Args:
        user_data: Dados do usuário do banco
        
    Returns:
        True se é admin, False caso contrário
    """
    if not user_data:
        return False
    
    # Verificar role no banco
    role = user_data.get('role', 'user')
    if role == 'admin':
        return True
    
    # Verificar email na lista de admins
    email = user_data.get('email', '').lower()
    admin_emails = current_app.config.get('ADMIN_EMAILS', [])
    
    if admin_emails and email in [e.lower() for e in admin_emails]:
        return True
    
    return False


def require_email_verified(user_data: Dict) -> Tuple[bool, str]:
    """
    Verifica se o email do usuário está verificado.
    Necessário para acesso a áreas sensíveis.
    
    Args:
        user_data: Dados do usuário do banco
        
    Returns:
        Tuple (is_verified, error_message)
    """
    if not user_data:
        return False, "Usuário não encontrado"
    
    email_verified = user_data.get('email_verificado', False)
    
    if not email_verified:
        return False, "Email não verificado. Verifique seu email antes de continuar."
    
    return True, ""


def log_auth_event(event_type: str, firebase_uid: str, success: bool, details: str = "", ip_address: str = None):
    """
    Registra eventos de autenticação para auditoria.
    
    Args:
        event_type: Tipo do evento (login, logout, register, password_reset, etc)
        firebase_uid: UID do Firebase
        success: Se a operação foi bem-sucedida
        details: Detalhes adicionais
        ip_address: Endereço IP do cliente (opcional)
    """
    # Log no console sempre (não depende do banco)
    logger.info(f"[AUDIT] {event_type} - UID: {firebase_uid} - Success: {success} - IP: {ip_address or 'N/A'} - {details}")
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Buscar ID do usuário no banco
        user_data = get_user_by_firebase_uid(firebase_uid) if firebase_uid != 'unknown' else None
        user_id = user_data.get('id') if user_data else None
        
        # Verificar se a tabela existe antes de tentar inserir
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'auditoria_logs'
            );
        """)
        table_exists = cur.fetchone()[0]
        
        if table_exists:
            try:
                cur.execute("""
                    INSERT INTO auditoria_logs (
                        tabela_afetada,
                        registro_id,
                        acao,
                        dados_novos,
                        usuario_id,
                        ip_address
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    'autenticacao',
                    firebase_uid,
                    f"{event_type}_{'sucesso' if success else 'falha'}",
                    details,
                    user_id,
                    ip_address
                ))
                
                conn.commit()
            except Exception as db_error:
                # Se houver erro ao inserir, apenas logar (não quebrar o fluxo)
                conn.rollback()
                logger.debug(f"Erro ao inserir log de auditoria: {db_error}")
        else:
            logger.debug("Tabela auditoria_logs não existe. Log apenas no console.")
        
        cur.close()
        
        # Enviar alerta de segurança para eventos suspeitos (apenas se sucesso)
        if not success and event_type in ['login', 'register']:
            try:
                from .email_service import send_security_alert
                user_email = user_data.get('email') if user_data else None
                send_security_alert(
                    event_type=f"{event_type}_failed",
                    details=details,
                    user_email=user_email
                )
            except Exception as email_error:
                logger.debug(f"Erro ao enviar alerta de segurança: {email_error}")
        
    except Exception as e:
        # Se houver erro geral, apenas logar (não quebrar o fluxo)
        logger.debug(f"Erro ao registrar log de auditoria: {e}")


# =====================================================
# MULTI-FACTOR AUTHENTICATION (2FA) - TOTP
# =====================================================

def generate_mfa_secret(user_email: str, user_id: int) -> Tuple[str, str]:
    """
    Gera um secret TOTP para 2FA e retorna o QR code em base64.
    
    Args:
        user_email: Email do usuário (para o label do QR code)
        user_id: ID do usuário no banco
        
    Returns:
        Tuple (secret, qr_code_base64)
    """
    # Gerar secret aleatório
    secret = pyotp.random_base32()
    
    # Criar URI para o QR code
    issuer = current_app.config.get('MFA_ISSUER_NAME', 'LhamaBanana')
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name=issuer
    )
    
    # Gerar QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Converter para base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    logger.info(f"Secret 2FA gerado para usuário {user_id} ({user_email})")
    
    return secret, qr_code_base64


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verifica se um código TOTP está correto.
    
    Args:
        secret: Secret key do usuário
        code: Código de 6 dígitos fornecido pelo usuário
        
    Returns:
        True se o código estiver correto, False caso contrário
    """
    if not secret or not code:
        return False
    
    try:
        totp = pyotp.TOTP(secret)
        # Verificar código atual e códigos adjacentes (tolerância de 30s)
        return totp.verify(code, valid_window=1)
    except Exception as e:
        logger.error(f"Erro ao verificar código TOTP: {e}")
        return False


def enable_mfa_for_user(user_id: int, secret: str) -> bool:
    """
    Habilita 2FA para um usuário, salvando o secret no banco.
    
    Args:
        user_id: ID do usuário no banco
        secret: Secret key gerado
        
    Returns:
        True se habilitado com sucesso
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE usuarios 
            SET mfa_secret = %s, 
                mfa_enabled = TRUE
            WHERE id = %s
        """, (secret, user_id))
        
        conn.commit()
        cur.close()
        
        logger.info(f"2FA habilitado para usuário ID: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao habilitar 2FA: {e}")
        if conn:
            conn.rollback()
        return False


def disable_mfa_for_user(user_id: int) -> bool:
    """
    Desabilita 2FA para um usuário, removendo o secret do banco.
    
    Args:
        user_id: ID do usuário no banco
        
    Returns:
        True se desabilitado com sucesso
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE usuarios 
            SET mfa_secret = NULL, 
                mfa_enabled = FALSE
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        cur.close()
        
        logger.info(f"2FA desabilitado para usuário ID: {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao desabilitar 2FA: {e}")
        if conn:
            conn.rollback()
        return False


def is_mfa_enabled(user_data: Dict) -> bool:
    """
    Verifica se 2FA está habilitado para o usuário.
    
    Args:
        user_data: Dados do usuário do banco
        
    Returns:
        True se 2FA está habilitado
    """
    if not user_data:
        return False
    
    return user_data.get('mfa_enabled', False) or bool(user_data.get('mfa_secret'))


def get_mfa_status(user_data: Dict) -> Dict:
    """
    Retorna o status de 2FA do usuário.
    
    Args:
        user_data: Dados do usuário do banco
        
    Returns:
        Dict com status de 2FA
    """
    if not user_data:
        return {'enabled': False, 'has_secret': False}
    
    return {
        'enabled': user_data.get('mfa_enabled', False),
        'has_secret': bool(user_data.get('mfa_secret'))
    }

