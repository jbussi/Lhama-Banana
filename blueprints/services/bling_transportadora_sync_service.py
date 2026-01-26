"""
Serviço para sincronizar transportadoras do Bling com banco de dados local
===========================================================================

Busca todas as transportadoras cadastradas no Bling e armazena no banco de dados
para uso rápido na emissão de NF-e.
"""
from flask import current_app
from typing import Dict, List, Optional
from .bling_api_service import make_bling_api_request
from .db import get_db
import psycopg2.extras
import re
import json
import time

def sync_transportadoras_from_bling(force_refresh: bool = True) -> Dict:
    """
    Sincroniza todas as transportadoras do Bling com o banco de dados local
    
    IMPORTANTE: Esta função deve ser chamada manualmente via:
    - Endpoint: POST /api/admin/transportadoras/sync
    - Script: python scripts/sync_transportadoras.py --force
    
    Args:
        force_refresh: Sempre True para sincronização manual (padrão: True)
    
    Returns:
        Dict com resultado da sincronização:
        {
            'success': bool,
            'total_encontradas': int,
            'total_salvas': int,
            'total_atualizadas': int,
            'errors': List[str]
        }
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    result = {
        'success': False,
        'total_encontradas': 0,
        'total_salvas': 0,
        'total_atualizadas': 0,
        'errors': []
    }
    
    try:
        current_app.logger.info("🔄 Sincronizando transportadoras do Bling (manual)...")
        
        # Buscar todas as transportadoras do Bling (tipo 3)
        response = make_bling_api_request(
            'GET',
            '/contatos',
            params={
                'limite': 100,
                'tiposContato[]': 3  # Tipo 3 = Transportadora
            }
        )
        
        if response.status_code != 200:
            error_msg = f"Erro ao buscar transportadoras: HTTP {response.status_code}"
            current_app.logger.error(f"❌ {error_msg}")
            result['errors'].append(error_msg)
            return result
        
        data = response.json()
        transportadoras = data.get('data', [])
        result['total_encontradas'] = len(transportadoras)
        
        current_app.logger.info(f"📦 Encontradas {len(transportadoras)} transportadora(s) no Bling")
        
        # Buscar detalhes completos de cada transportadora e salvar
        for transportadora in transportadoras:
            bling_id = transportadora.get('id')
            if not bling_id:
                continue
            
            try:
                # Buscar detalhes completos
                detail_response = make_bling_api_request(
                    'GET',
                    f'/contatos/{bling_id}'
                )
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    transportadora_completa = detail_data.get('data', transportadora)
                else:
                    # Se não conseguir detalhes, usar dados da listagem
                    transportadora_completa = transportadora
                
                # Extrair e salvar dados
                save_result = save_transportadora_to_db(transportadora_completa, cur)
                if save_result['saved']:
                    result['total_salvas'] += 1
                elif save_result['updated']:
                    result['total_atualizadas'] += 1
                elif save_result.get('error'):
                    result['errors'].append(f"Erro ao salvar {transportadora.get('nome', 'N/A')}: {save_result['error']}")
                    
            except Exception as e:
                error_msg = f"Erro ao processar transportadora ID {bling_id}: {str(e)}"
                current_app.logger.error(f"❌ {error_msg}", exc_info=True)
                result['errors'].append(error_msg)
        
        conn.commit()
        result['success'] = True
        
        current_app.logger.info(
            f"✅ Sincronização concluída: "
            f"{result['total_salvas']} salvas, "
            f"{result['total_atualizadas']} atualizadas, "
            f"{len(result['errors'])} erros"
        )
        
    except Exception as e:
        conn.rollback()
        error_msg = f"Erro ao sincronizar transportadoras: {str(e)}"
        current_app.logger.error(f"❌ {error_msg}", exc_info=True)
        result['errors'].append(error_msg)
    finally:
        cur.close()
    
    return result


def save_transportadora_to_db(transportadora_bling: Dict, cur) -> Dict:
    """
    Salva ou atualiza transportadora no banco de dados
    
    Args:
        transportadora_bling: Dict com dados completos da transportadora do Bling
        cur: Cursor do banco de dados
    
    Returns:
        Dict com resultado: {'saved': bool, 'updated': bool, 'error': str}
    """
    result = {'saved': False, 'updated': False, 'error': None}
    
    try:
        bling_id = transportadora_bling.get('id')
        if not bling_id:
            result['error'] = 'ID do Bling não encontrado'
            return result
        
        # Extrair dados básicos
        nome = transportadora_bling.get('nome', '')
        fantasia = transportadora_bling.get('fantasia')
        numero_doc = transportadora_bling.get('numeroDocumento', '')
        cnpj = re.sub(r'[^\d]', '', str(numero_doc)) if numero_doc else None
        
        if not cnpj or len(cnpj) != 14:
            result['error'] = f'CNPJ inválido: {numero_doc}'
            return result
        
        # Extrair IE
        ie = transportadora_bling.get('ie')
        indicador_ie = transportadora_bling.get('indicadorIe')
        
        # Extrair endereço
        endereco_data = transportadora_bling.get('endereco', {})
        endereco_geral = endereco_data.get('geral', {}) or endereco_data.get('cobranca', {})
        if not endereco_geral and isinstance(endereco_data, dict):
            # Tentar usar endereco_data diretamente
            if endereco_data.get('endereco'):
                endereco_geral = endereco_data
        
        endereco = endereco_geral.get('endereco') if endereco_geral else None
        numero = endereco_geral.get('numero') if endereco_geral else None
        complemento = endereco_geral.get('complemento') if endereco_geral else None
        bairro = endereco_geral.get('bairro') if endereco_geral else None
        municipio = endereco_geral.get('municipio') if endereco_geral else None
        uf = endereco_geral.get('uf') if endereco_geral else None
        cep = endereco_geral.get('cep') if endereco_geral else None
        if cep:
            cep = re.sub(r'[^\d]', '', str(cep))
        
        # Extrair outros dados
        telefone = transportadora_bling.get('telefone')
        email = transportadora_bling.get('email')
        email_nota_fiscal = transportadora_bling.get('emailNotaFiscal')
        situacao = transportadora_bling.get('situacao', 'A')
        tipos_contato = transportadora_bling.get('tiposContato', [])
        
        # Verificar se já existe
        cur.execute("""
            SELECT id FROM transportadoras_bling 
            WHERE bling_id = %s OR cnpj = %s
        """, (bling_id, cnpj))
        existing = cur.fetchone()
        
        if existing:
            # Atualizar
            cur.execute("""
                UPDATE transportadoras_bling SET
                    nome = %s,
                    fantasia = %s,
                    cnpj = %s,
                    ie = %s,
                    indicador_ie = %s,
                    telefone = %s,
                    email = %s,
                    email_nota_fiscal = %s,
                    endereco = %s,
                    numero = %s,
                    complemento = %s,
                    bairro = %s,
                    municipio = %s,
                    uf = %s,
                    cep = %s,
                    situacao = %s,
                    tipos_contato = %s,
                    dados_completos = %s,
                    ultima_sincronizacao = NOW()
                WHERE id = %s
            """, (
                nome, fantasia, cnpj, ie, indicador_ie,
                telefone, email, email_nota_fiscal,
                endereco, numero, complemento, bairro, municipio, uf, cep,
                situacao, json.dumps(tipos_contato) if tipos_contato else None,
                json.dumps(transportadora_bling),
                existing['id']
            ))
            result['updated'] = True
            current_app.logger.debug(f"🔄 Transportadora atualizada: {nome} (CNPJ: {cnpj})")
        else:
            # Inserir
            cur.execute("""
                INSERT INTO transportadoras_bling (
                    bling_id, nome, fantasia, cnpj, ie, indicador_ie,
                    telefone, email, email_nota_fiscal,
                    endereco, numero, complemento, bairro, municipio, uf, cep,
                    situacao, tipos_contato, dados_completos
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
            """, (
                bling_id, nome, fantasia, cnpj, ie, indicador_ie,
                telefone, email, email_nota_fiscal,
                endereco, numero, complemento, bairro, municipio, uf, cep,
                situacao, json.dumps(tipos_contato) if tipos_contato else None,
                json.dumps(transportadora_bling)
            ))
            result['saved'] = True
            current_app.logger.debug(f"✅ Transportadora salva: {nome} (CNPJ: {cnpj})")
        
    except Exception as e:
        result['error'] = str(e)
        current_app.logger.error(f"❌ Erro ao salvar transportadora: {e}", exc_info=True)
    
    return result


def get_transportadora_by_cnpj(cnpj: str) -> Optional[Dict]:
    """
    Busca transportadora no banco de dados local por CNPJ
    
    Args:
        cnpj: CNPJ (com ou sem formatação)
    
    Returns:
        Dict com dados da transportadora ou None se não encontrada
    """
    if not cnpj:
        return None
    
    cnpj_limpo = re.sub(r'[^\d]', '', str(cnpj))
    if len(cnpj_limpo) != 14:
        return None
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT * FROM transportadoras_bling
            WHERE cnpj = %s AND situacao = 'A'
            ORDER BY atualizado_em DESC
            LIMIT 1
        """, (cnpj_limpo,))
        
        transportadora = cur.fetchone()
        if transportadora:
            return dict(transportadora)
        return None
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar transportadora por CNPJ: {e}", exc_info=True)
        return None
    finally:
        cur.close()


def get_transportadora_by_bling_id(bling_id: int) -> Optional[Dict]:
    """
    Busca transportadora no banco de dados local por ID do Bling
    
    Args:
        bling_id: ID do contato no Bling
    
    Returns:
        Dict com dados da transportadora ou None se não encontrada
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT * FROM transportadoras_bling
            WHERE bling_id = %s AND situacao = 'A'
            LIMIT 1
        """, (bling_id,))
        
        transportadora = cur.fetchone()
        if transportadora:
            return dict(transportadora)
        return None
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar transportadora por Bling ID: {e}", exc_info=True)
        return None
    finally:
        cur.close()


def get_transportadora_by_nome(nome: str) -> Optional[Dict]:
    """
    Busca transportadora no banco de dados local por nome (busca usando nome_normalizado)
    
    Args:
        nome: Nome da transportadora (ex: "Jadlog", "Correios")
    
    Returns:
        Dict com dados da transportadora ou None se não encontrada
    """
    if not nome:
        return None
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Normalizar o nome de busca usando a mesma função do banco
        # Isso garante que a busca seja feita com a mesma normalização dos dados
        nome_busca = nome.strip().upper()
        
        # Remover acentos e caracteres especiais (mesma lógica da função SQL)
        nome_busca = re.sub(r'[ÁÀÂÃ]', 'A', nome_busca)
        nome_busca = re.sub(r'[ÉÈÊ]', 'E', nome_busca)
        nome_busca = re.sub(r'[ÍÌÎ]', 'I', nome_busca)
        nome_busca = re.sub(r'[ÓÒÔÕ]', 'O', nome_busca)
        nome_busca = re.sub(r'[ÚÙÛ]', 'U', nome_busca)
        nome_busca = re.sub(r'Ç', 'C', nome_busca)
        nome_busca = re.sub(r'\s+', ' ', nome_busca).strip()
        nome_busca = re.sub(r'[^A-Z0-9 ]', '', nome_busca)
        
        # Se o nome for muito curto (menos de 3 caracteres), não buscar
        if len(nome_busca) < 3:
            return None
        
        # Extrair palavra principal (primeira palavra)
        palavras_chave = nome_busca.split()
        palavra_principal = palavras_chave[0] if palavras_chave else nome_busca
        
        # Buscar usando nome_normalizado e fantasia_normalizado (mais eficiente com índices)
        # Priorizar correspondência exata, depois parcial
        cur.execute("""
            SELECT * FROM transportadoras_bling
            WHERE situacao = 'A'
            AND (
                nome_normalizado = %s
                OR fantasia_normalizado = %s
                OR nome_normalizado LIKE %s
                OR fantasia_normalizado LIKE %s
                OR nome_normalizado LIKE %s
                OR fantasia_normalizado LIKE %s
            )
            ORDER BY 
                CASE 
                    WHEN nome_normalizado = %s THEN 1
                    WHEN fantasia_normalizado = %s THEN 2
                    WHEN nome_normalizado LIKE %s THEN 3
                    WHEN fantasia_normalizado LIKE %s THEN 4
                    WHEN nome_normalizado LIKE %s THEN 5
                    WHEN fantasia_normalizado LIKE %s THEN 6
                    ELSE 7
                END,
                atualizado_em DESC
            LIMIT 1
        """, (
            nome_busca,  # Exato nome_normalizado
            nome_busca,  # Exato fantasia_normalizado
            f'{nome_busca}%',  # Começa com nome completo
            f'{nome_busca}%',  # Começa com fantasia completo
            f'%{nome_busca}%',  # Contém nome completo
            f'%{nome_busca}%',  # Contém fantasia completo
            nome_busca,  # Para ORDER BY
            nome_busca,  # Para ORDER BY
            f'{palavra_principal}%',  # Para ORDER BY
            f'{palavra_principal}%',  # Para ORDER BY
            f'{nome_busca}%',  # Para ORDER BY
            f'{nome_busca}%'   # Para ORDER BY
        ))
        
        transportadora = cur.fetchone()
        if transportadora:
            current_app.logger.info(
                f"✅ Transportadora encontrada por nome: '{nome}' -> '{transportadora.get('nome')}' "
                f"(nome_normalizado: '{transportadora.get('nome_normalizado')}')"
            )
            return dict(transportadora)
        
        current_app.logger.warning(
            f"⚠️ Transportadora não encontrada por nome: '{nome}' (normalizado: '{nome_busca}')"
        )
        return None
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar transportadora por nome: {e}", exc_info=True)
        return None
    finally:
        cur.close()


def format_transportadora_for_nfe(transportadora_db: Dict) -> Dict:
    """
    Formata transportadora do banco de dados para formato da NF-e do Bling
    
    IMPORTANTE: O Bling aceita apenas nome, numeroDocumento e ie no transportador.
    Endereço não é aceito na edição via PUT.
    
    Args:
        transportadora_db: Dict com dados da transportadora do banco
    
    Returns:
        Dict formatado para NF-e: {nome, numeroDocumento, ie?}
    """
    transportador_data = {
        'nome': transportadora_db.get('nome') or transportadora_db.get('fantasia') or ''
    }
    
    # CNPJ
    if transportadora_db.get('cnpj'):
        transportador_data['numeroDocumento'] = transportadora_db['cnpj']
    
    # IE (apenas se existir - algumas transportadoras são isentas)
    if transportadora_db.get('ie'):
        transportador_data['ie'] = transportadora_db['ie']
    
    # REMOVIDO: Endereço - Bling não aceita na edição via PUT
    # Apenas nome, numeroDocumento e ie são aceitos
    
    return transportador_data
