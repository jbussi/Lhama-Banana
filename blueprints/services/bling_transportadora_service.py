"""
Service para gerenciar transportadoras do Bling
===============================================

Busca e mapeia transportadoras cadastradas no Bling usando a API de contatos
"""
from flask import current_app
from typing import Dict, Optional, List
from .bling_api_service import make_bling_api_request
import re

# Cache para transportadoras do Bling
_transportadoras_cache = None
_cache_timestamp = None
CACHE_DURATION = 86400  # 1 dia (transportadoras raramente mudam)


def get_bling_transportadoras(force_refresh: bool = False) -> List[Dict]:
    """
    Busca todas as transportadoras cadastradas no Bling
    
    Args:
        force_refresh: Se True, força atualização do cache
    
    Returns:
        Lista de transportadoras (contatos do tipo transportadora)
    """
    global _transportadoras_cache, _cache_timestamp
    import time
    
    # Verificar cache
    if not force_refresh and _transportadoras_cache and _cache_timestamp:
        if time.time() - _cache_timestamp < CACHE_DURATION:
            current_app.logger.debug(
                f"📋 Usando cache de transportadoras ({len(_transportadoras_cache)} transportadoras)"
            )
            return _transportadoras_cache
    
    try:
        current_app.logger.info("🔍 Buscando transportadoras do Bling...")
        
        # Buscar contatos do tipo transportadora
        # Tipos de contato: 1=Cliente, 2=Fornecedor, 3=Transportadora, etc.
        # Formato do array: tiposContato[]=3
        response = make_bling_api_request(
            'GET',
            '/contatos',
            params={
                'limite': 100,
                'tiposContato[]': 3  # Tipo 3 = Transportadora (formato esperado pela API)
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            transportadoras = data.get('data', [])
            
            # Atualizar cache
            _transportadoras_cache = transportadoras
            _cache_timestamp = time.time()
            
            current_app.logger.info(
                f"✅ {len(transportadoras)} transportadora(s) encontrada(s) no Bling"
            )
            
            # Logar transportadoras para referência
            for trans in transportadoras[:10]:
                current_app.logger.debug(
                    f"   - ID: {trans.get('id')}, Nome: {trans.get('nome', 'N/A')}, "
                    f"CNPJ: {trans.get('numeroDocumento', 'N/A')}"
                )
            
            return transportadoras
        else:
            current_app.logger.error(
                f"❌ Erro ao buscar transportadoras: HTTP {response.status_code}"
            )
            return []
            
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao buscar transportadoras do Bling: {e}", 
            exc_info=True
        )
        return []


def get_transportadora_by_id(bling_id: int) -> Optional[Dict]:
    """
    Busca transportadora do Bling por ID usando /contatos/{idContato}
    
    Args:
        bling_id: ID do contato no Bling
    
    Returns:
        Dict com dados completos da transportadora ou None se não encontrado
    """
    try:
        current_app.logger.info(f"🔍 Buscando transportadora ID {bling_id} no Bling...")
        
        response = make_bling_api_request(
            'GET',
            f'/contatos/{bling_id}'
        )
        
        if response.status_code == 200:
            data = response.json()
            transportadora = data.get('data', {})
            
            current_app.logger.info(
                f"✅ Transportadora encontrada: {transportadora.get('nome', 'N/A')} "
                f"(ID: {bling_id})"
            )
            
            return transportadora
        elif response.status_code == 404:
            current_app.logger.warning(
                f"⚠️ Transportadora ID {bling_id} não encontrada no Bling"
            )
            return None
        else:
            current_app.logger.error(
                f"❌ Erro ao buscar transportadora ID {bling_id}: HTTP {response.status_code}"
            )
            return None
            
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao buscar transportadora ID {bling_id} no Bling: {e}", 
            exc_info=True
        )
        return None


def find_transportadora_by_cnpj(cnpj: str) -> Optional[Dict]:
    """
    Busca transportadora no Bling por CNPJ
    
    Args:
        cnpj: CNPJ da transportadora (com ou sem formatação)
    
    Returns:
        Dict com dados da transportadora ou None se não encontrado
    """
    if not cnpj:
        return None
    
    # Limpar formatação do CNPJ
    cnpj_limpo = re.sub(r'[^\d]', '', str(cnpj))
    
    if len(cnpj_limpo) != 14:
        current_app.logger.warning(
            f"⚠️ CNPJ inválido: {cnpj} (limpo: {cnpj_limpo}, tamanho: {len(cnpj_limpo)})"
        )
        return None
    
    try:
        current_app.logger.info(f"🔍 Buscando transportadora por CNPJ: {cnpj_limpo}")
        
        # Buscar contatos por CNPJ
        response = make_bling_api_request(
            'GET',
            '/contatos',
            params={
                'limite': 100,
                'numeroDocumento': cnpj_limpo,
                'tiposContato[]': 3  # Tipo 3 = Transportadora
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            transportadoras = data.get('data', [])
            
            if transportadoras:
                transportadora = transportadoras[0]  # Pegar a primeira
                current_app.logger.info(
                    f"✅ Transportadora encontrada por CNPJ: {transportadora.get('nome', 'N/A')} "
                    f"(ID: {transportadora.get('id')})"
                )
                return transportadora
            else:
                current_app.logger.info(
                    f"ℹ️ Nenhuma transportadora encontrada com CNPJ {cnpj_limpo}"
                )
                return None
        else:
            current_app.logger.error(
                f"❌ Erro ao buscar transportadora por CNPJ: HTTP {response.status_code}"
            )
            return None
            
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao buscar transportadora por CNPJ {cnpj_limpo}: {e}", 
            exc_info=True
        )
        return None


def map_transportadora_to_bling_format(transportadora_bling: Dict) -> Dict:
    """
    Mapeia dados da transportadora do Bling para formato usado na NF-e/Pedido
    
    Args:
        transportadora_bling: Dict com dados completos da transportadora do Bling
    
    Returns:
        Dict formatado para uso em transporte.transportador
    """
    transportador_data = {}
    
    # Nome
    if transportadora_bling.get('nome'):
        transportador_data['nome'] = transportadora_bling.get('nome')
    elif transportadora_bling.get('fantasia'):
        transportador_data['nome'] = transportadora_bling.get('fantasia')
    
    # CNPJ (limpar formatação)
    numero_doc = transportadora_bling.get('numeroDocumento', '')
    if numero_doc:
        cnpj_limpo = re.sub(r'[^\d]', '', str(numero_doc))
        transportador_data['numeroDocumento'] = cnpj_limpo
    
    # Inscrição Estadual
    if transportadora_bling.get('ie'):
        transportador_data['ie'] = transportadora_bling.get('ie')
    
    # Endereço
    endereco_data = transportadora_bling.get('endereco', {})
    endereco_geral = endereco_data.get('geral', {})
    
    if endereco_geral:
        endereco_transportador = {}
        
        if endereco_geral.get('endereco'):
            endereco_transportador['endereco'] = endereco_geral.get('endereco')
        
        if endereco_geral.get('numero'):
            endereco_transportador['numero'] = endereco_geral.get('numero')
        
        if endereco_geral.get('complemento'):
            endereco_transportador['complemento'] = endereco_geral.get('complemento')
        
        if endereco_geral.get('bairro'):
            endereco_transportador['bairro'] = endereco_geral.get('bairro')
        
        if endereco_geral.get('municipio'):
            endereco_transportador['municipio'] = endereco_geral.get('municipio')
        
        if endereco_geral.get('uf'):
            endereco_transportador['uf'] = endereco_geral.get('uf')
        
        if endereco_geral.get('cep'):
            cep_limpo = re.sub(r'[^\d]', '', str(endereco_geral.get('cep')))
            endereco_transportador['cep'] = cep_limpo
        
        if endereco_transportador:
            transportador_data['endereco'] = endereco_transportador
    
    # NOTA: Não incluir 'id' do contato no transportador da NF-e
    # A documentação do Bling não especifica esse campo no transportador
    # O ID é usado apenas para referência interna
    
    return transportador_data


def get_or_find_transportadora_bling(transportadora_cnpj: str, transportadora_nome: str = None) -> Optional[Dict]:
    """
    Busca ou encontra transportadora no Bling e retorna dados formatados
    
    Args:
        transportadora_cnpj: CNPJ da transportadora
        transportadora_nome: Nome da transportadora (opcional, para log)
    
    Returns:
        Dict formatado para uso em transporte.transportador ou None se não encontrado
    """
    if not transportadora_cnpj:
        return None
    
    # Tentar buscar por CNPJ
    transportadora_bling = find_transportadora_by_cnpj(transportadora_cnpj)
    
    if transportadora_bling:
        # Se encontrou, buscar dados completos pelo ID
        transportadora_id = transportadora_bling.get('id')
        if transportadora_id:
            transportadora_completa = get_transportadora_by_id(transportadora_id)
            if transportadora_completa:
                # Mapear para formato usado na NF-e/Pedido
                transportador_formatado = map_transportadora_to_bling_format(transportadora_completa)
                current_app.logger.info(
                    f"✅ Transportadora mapeada do Bling: {transportadora_nome or 'N/A'} "
                    f"(ID: {transportadora_id}, CNPJ: {transportadora_cnpj})"
                )
                return transportador_formatado
    
    current_app.logger.warning(
        f"⚠️ Transportadora não encontrada no Bling: {transportadora_nome or 'N/A'} "
        f"(CNPJ: {transportadora_cnpj})"
    )
    return None
