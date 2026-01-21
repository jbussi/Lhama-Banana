"""
Serviço para criação de contatos no Bling
==========================================
Gerencia criação de contatos (transportadoras, fornecedores, etc.) no Bling.
"""

from flask import current_app
from typing import Dict, Optional
import logging
import re

from .bling_api_service import make_bling_api_request

logger = logging.getLogger(__name__)


def create_contact_in_bling(contact_data: Dict) -> Dict:
    """
    Cria um contato no Bling usando a API v3.
    
    Args:
        contact_data: Dict com dados do contato no formato da API Bling
        
    Returns:
        Dict com resultado da operação:
        {
            'success': bool,
            'contact_id': int (se sucesso),
            'error': str (se erro)
        }
    """
    try:
        # Preparar payload para Bling API v3
        payload = {
            'nome': contact_data.get('nome'),
            'codigo': contact_data.get('codigo', ''),
            'situacao': contact_data.get('situacao', 'A'),  # A = Ativo
            'tipo': contact_data.get('tipo', 'J'),  # J = Jurídica, F = Física
        }
        
        # Número de documento (CPF/CNPJ)
        if contact_data.get('numeroDocumento'):
            payload['numeroDocumento'] = re.sub(r'[^0-9]', '', str(contact_data['numeroDocumento']))
        
        # Telefones
        if contact_data.get('telefone'):
            payload['telefone'] = contact_data['telefone']
        if contact_data.get('celular'):
            payload['celular'] = contact_data['celular']
        
        # Email
        if contact_data.get('email'):
            payload['email'] = contact_data['email']
        if contact_data.get('emailNotaFiscal'):
            payload['emailNotaFiscal'] = contact_data['emailNotaFiscal']
        
        # Nome fantasia
        if contact_data.get('fantasia'):
            payload['fantasia'] = contact_data['fantasia']
        
        # Inscrições
        if contact_data.get('ie'):
            payload['ie'] = contact_data['ie']
        if contact_data.get('rg'):
            payload['rg'] = contact_data['rg']
        if contact_data.get('orgaoEmissor'):
            payload['orgaoEmissor'] = contact_data['orgaoEmissor']
        if contact_data.get('inscricaoMunicipal'):
            payload['inscricaoMunicipal'] = contact_data['inscricaoMunicipal']
        
        # Indicador IE
        if contact_data.get('indicadorIe') is not None:
            payload['indicadorIe'] = contact_data['indicadorIe']
        
        # Endereço
        if contact_data.get('endereco'):
            endereco_data = contact_data['endereco']
            payload['endereco'] = {}
            
            # Endereço geral
            if endereco_data.get('geral'):
                geral = endereco_data['geral']
                payload['endereco']['geral'] = {
                    'endereco': geral.get('endereco', ''),
                    'numero': str(geral.get('numero', '')),
                    'complemento': geral.get('complemento', ''),
                    'bairro': geral.get('bairro', ''),
                    'municipio': geral.get('municipio', ''),
                    'uf': geral.get('uf', ''),
                    'cep': re.sub(r'[^0-9]', '', str(geral.get('cep', ''))),
                    'pais': geral.get('pais', 'Brasil')
                }
            
            # Endereço de cobrança (se fornecido, senão usa o geral)
            if endereco_data.get('cobranca'):
                cobranca = endereco_data['cobranca']
                payload['endereco']['cobranca'] = {
                    'endereco': cobranca.get('endereco', ''),
                    'numero': str(cobranca.get('numero', '')),
                    'complemento': cobranca.get('complemento', ''),
                    'bairro': cobranca.get('bairro', ''),
                    'municipio': cobranca.get('municipio', ''),
                    'uf': cobranca.get('uf', ''),
                    'cep': re.sub(r'[^0-9]', '', str(cobranca.get('cep', ''))),
                    'pais': cobranca.get('pais', 'Brasil')
                }
            elif endereco_data.get('geral'):
                # Se não fornecido, usar endereço geral como cobrança também
                geral = endereco_data['geral']
                payload['endereco']['cobranca'] = {
                    'endereco': geral.get('endereco', ''),
                    'numero': str(geral.get('numero', '')),
                    'complemento': geral.get('complemento', ''),
                    'bairro': geral.get('bairro', ''),
                    'municipio': geral.get('municipio', ''),
                    'uf': geral.get('uf', ''),
                    'cep': re.sub(r'[^0-9]', '', str(geral.get('cep', ''))),
                    'pais': geral.get('pais', 'Brasil')
                }
        
        # Vendedor (opcional)
        if contact_data.get('vendedor_id'):
            payload['vendedor'] = {'id': contact_data['vendedor_id']}
        
        # Dados adicionais (opcional)
        if contact_data.get('dadosAdicionais'):
            payload['dadosAdicionais'] = contact_data['dadosAdicionais']
        
        # Financeiro (opcional)
        if contact_data.get('financeiro'):
            payload['financeiro'] = contact_data['financeiro']
        
        # País (opcional)
        if contact_data.get('pais'):
            if isinstance(contact_data['pais'], dict):
                payload['pais'] = contact_data['pais']
            else:
                payload['pais'] = {'nome': contact_data['pais']}
        
        # Tipos de contato (opcional)
        if contact_data.get('tiposContato'):
            payload['tiposContato'] = contact_data['tiposContato']
        
        # Pessoas de contato (opcional)
        if contact_data.get('pessoasContato'):
            payload['pessoasContato'] = contact_data['pessoasContato']
        
        # Observações
        if contact_data.get('observacoes'):
            payload['observacoes'] = contact_data['observacoes']
        
        logger.info(f"📤 Criando contato no Bling: {payload.get('nome')} ({payload.get('numeroDocumento')})")
        logger.debug(f"Payload completo: {payload}")
        
        # Fazer requisição para criar contato
        response = make_bling_api_request(
            'POST',
            '/contatos',
            json=payload
        )
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            contact_id = response_data.get('data', {}).get('id')
            
            if not contact_id:
                # Tentar extrair ID de outras formas
                if 'data' in response_data and isinstance(response_data['data'], dict):
                    contact_id = response_data['data'].get('id')
                elif 'id' in response_data:
                    contact_id = response_data['id']
            
            if contact_id:
                logger.info(f"✅ Contato criado no Bling: {payload.get('nome')} (ID: {contact_id})")
                return {
                    'success': True,
                    'contact_id': contact_id,
                    'nome': payload.get('nome')
                }
            else:
                logger.error(f"❌ Resposta do Bling não contém ID do contato: {response_data}")
                return {
                    'success': False,
                    'error': 'Resposta do Bling não contém ID do contato',
                    'response': response_data
                }
        else:
            error_text = response.text
            logger.error(f"❌ Erro ao criar contato no Bling: {response.status_code} - {error_text}")
            
            # Tentar extrair detalhes do erro
            try:
                error_json = response.json()
                return {
                    'success': False,
                    'error': f"Erro HTTP {response.status_code}",
                    'details': error_json
                }
            except:
                return {
                    'success': False,
                    'error': f"Erro HTTP {response.status_code}",
                    'details': error_text
                }
            
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao criar contato no Bling: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def find_contact_in_bling(cnpj: str) -> Optional[Dict]:
    """
    Busca contato no Bling por CNPJ.
    Primeiro busca na listagem, depois busca detalhes completos por ID se encontrado.
    
    Args:
        cnpj: CNPJ (com ou sem formatação)
    
    Returns:
        Dict com dados completos do contato se encontrado, None caso contrário
    """
    cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
    
    try:
        # Primeiro: buscar na listagem
        response = make_bling_api_request(
            'GET',
            '/contatos',
            params={
                'numeroDocumento': cnpj_clean,
                'limite': 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            contatos = data.get('data', [])
            
            # Procurar exatamente o CNPJ
            for contato in contatos:
                contato_doc = re.sub(r'[^0-9]', '', contato.get('numeroDocumento', '') or '')
                if contato_doc == cnpj_clean:
                    contact_id = contato.get('id')
                    logger.info(f"✅ Contato encontrado no Bling: {cnpj_clean} (ID: {contact_id})")
                    
                    # Buscar detalhes completos do contato por ID (pode ter mais campos)
                    if contact_id:
                        try:
                            detail_response = make_bling_api_request(
                                'GET',
                                f'/contatos/{contact_id}'
                            )
                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()
                                full_contact = detail_data.get('data', {})
                                if full_contact:
                                    logger.info(f"✅ Dados completos do contato obtidos (ID: {contact_id})")
                                    return full_contact
                        except Exception as detail_error:
                            logger.warning(f"⚠️ Erro ao buscar detalhes do contato {contact_id}: {detail_error}. Usando dados da listagem.")
                    
                    # Se não conseguir buscar detalhes, retorna dados da listagem
                    return contato
            
            return None
        
        elif response.status_code == 404:
            return None
        else:
            logger.warning(f"⚠️ Erro ao buscar contato no Bling: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar contato no Bling: {e}", exc_info=True)
        return None
