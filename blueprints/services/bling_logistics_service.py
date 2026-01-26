"""
Serviço para gerenciamento de serviços de logística no Bling
============================================================
Gerencia busca e criação de serviços de logística (Melhor Envio, etc.) no Bling.
"""

from flask import current_app
from typing import Dict, Optional
import logging

from .bling_api_service import make_bling_api_request

logger = logging.getLogger(__name__)

# Mapeamento fixo de IDs de serviços logísticos no Bling
# Cada serviço do Melhor Envio tem um ID único no Bling
# ATUALIZAR ESTES IDs APÓS CADASTRAR OS SERVIÇOS MANUALMENTE NO BLING
# 
# CORREÇÃO: Azul Cargo Express usa IDs 15 e 16, NÃO o ID 4
# ID 4 é exclusivo do Jadlog ".Com"
SERVICOS_LOGISTICOS_IDS = {
    1: 899551,   # PAC - Correios
    2: 899552,   # SEDEX - Correios
    3: 899553,   # Package - Jadlog
    4: 899554,   # .Com - Jadlog
    12: 899556,  # éFácil - LATAM Cargo
    15: 899557,  # Expresso - Azul Cargo Express
    16: 899558,  # e-commerce - Azul Cargo Express
    17: 899555,  # Correios PAC Mini
    22: 899559,  # Rodoviário - Buslog
    27: 899560,  # Package Centralizado - Jadlog
    31: 899561,  # Express - Loggi
    32: 899562,  # Coleta - Loggi
    33: 899563,  # Standard - JeT
    34: 899564,  # Loggi Ponto - Loggi
}


def get_or_create_logistics_service(melhor_envio_service_id: int, service_name: str, transportadora_nome: Optional[str] = None) -> Optional[Dict]:
    """
    Busca ou retorna ID fixo de serviço de logística no Bling baseado no código do Melhor Envio.
    
    CORREÇÃO: Azul Cargo Express usa IDs 15 e 16, não o ID 4.
    ID 4 é exclusivo do Jadlog ".Com".
    
    Args:
        melhor_envio_service_id: ID do serviço no Melhor Envio (1, 2, 3, 15, 16, etc.)
        service_name: Nome do serviço (PAC, SEDEX, .Com, Expresso, etc.)
        transportadora_nome: Nome da transportadora (opcional, para validação)
    
    Returns:
        Dict com dados do serviço no Bling:
        {
            'id': int,  # ID do serviço no Bling (fixo)
            'codigo': str,  # Código do serviço (igual ao melhor_envio_service_id)
            'descricao': str,  # Descrição do serviço
            'created': bool  # False (IDs são fixos, não criados)
        }
        ou None se não encontrar ID mapeado
    """
    try:
        # Usar mapeamento padrão direto (não precisa mais de lógica especial para ID 4)
        if melhor_envio_service_id in SERVICOS_LOGISTICOS_IDS:
            bling_service_id = SERVICOS_LOGISTICOS_IDS[melhor_envio_service_id]
        else:
            logger.warning(
                f"⚠️ Service ID {melhor_envio_service_id} não encontrado no mapeamento padrão"
            )
            bling_service_id = None
        
        if bling_service_id:
            logger.info(
                f"✅ Serviço encontrado no mapeamento: {service_name} "
                f"(Melhor Envio ID: {melhor_envio_service_id}, Transportadora: {transportadora_nome or 'N/A'}, "
                f"Bling ID: {bling_service_id})"
            )
            return {
                'id': bling_service_id,
                'codigo': str(melhor_envio_service_id),
                'descricao': f"{service_name} (LhamaBanana)",
                'created': False
            }
        
        # Se não tem ID mapeado, tentar buscar no Bling (fallback)
        logger.warning(
            f"⚠️ Serviço {service_name} (ID: {melhor_envio_service_id}) não tem ID mapeado. "
            f"Tentando buscar no Bling..."
        )
        
        response = make_bling_api_request(
            'GET',
            '/logisticas/servicos',
            params={
                'tipoIntegracao': 'MelhorEnvio',
                'limite': 100
            }
        )
        
        if response.status_code == 200:
            servicos_data = response.json().get('data', [])
            
            # Procurar serviço com código correspondente
            # Preferir serviços específicos da loja (LhamaBanana) se existirem
            servico_bling = None
            
            # Primeiro, tentar encontrar serviço específico da loja
            for servico in servicos_data:
                if (servico.get('codigo') == str(melhor_envio_service_id) and 
                    'LhamaBanana' in servico.get('descricao', '')):
                    servico_bling = servico
                    break
            
            # Se não encontrou específico, usar qualquer serviço com o código
            if not servico_bling:
                for servico in servicos_data:
                    if servico.get('codigo') == str(melhor_envio_service_id):
                        servico_bling = servico
                        break
            
            if servico_bling:
                bling_service_id = servico_bling.get('id')
                logger.info(
                    f"✅ Serviço encontrado no Bling: {service_name} "
                    f"(Melhor Envio ID: {melhor_envio_service_id}, Bling ID: {bling_service_id})"
                )
                # Atualizar mapeamento para próxima vez
                SERVICOS_LOGISTICOS_IDS[melhor_envio_service_id] = bling_service_id
                logger.info(
                    f"💡 Mapeamento atualizado: {melhor_envio_service_id} → {bling_service_id}"
                )
                return {
                    'id': bling_service_id,
                    'codigo': servico_bling.get('codigo'),
                    'descricao': servico_bling.get('descricao', service_name),
                    'created': False
                }
        
        # Se não encontrou, logar aviso
        logger.warning(
            f"⚠️ Serviço {service_name} (ID: {melhor_envio_service_id}) não encontrado no Bling. "
            f"Por favor, cadastre manualmente e atualize o mapeamento SERVICOS_LOGISTICOS_IDS."
        )
        
        return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar serviço de logística no Bling: {e}", exc_info=True)
        return None


def get_transportadora_id_in_bling(cnpj: str) -> Optional[int]:
    """
    Busca ID da transportadora no Bling por CNPJ.
    
    Args:
        cnpj: CNPJ da transportadora (com ou sem formatação)
    
    Returns:
        ID da transportadora no Bling ou None se não encontrada
    """
    try:
        from .bling_contact_service import find_contact_in_bling
        
        transportadora = find_contact_in_bling(cnpj)
        
        if transportadora:
            transportadora_id = transportadora.get('id')
            transportadora_nome = transportadora.get('nome', '')
            logger.info(
                f"✅ Transportadora encontrada no Bling: {transportadora_nome} "
                f"(CNPJ: {cnpj}, ID: {transportadora_id})"
            )
            return transportadora_id
        
        logger.warning(f"⚠️ Transportadora não encontrada no Bling (CNPJ: {cnpj})")
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar transportadora no Bling: {e}", exc_info=True)
        return None
