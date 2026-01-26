"""
Service para gerenciar formas de pagamento do Bling
===================================================

Mapeia formas de pagamento do checkout para formas de pagamento do Bling
"""
from flask import current_app
from typing import Dict, Optional, List
from .bling_api_service import make_bling_api_request
import json

# Cache para formas de pagamento do Bling
_formas_pagamento_cache = None
_cache_timestamp = None
CACHE_DURATION = 86400  # 1 dia (formas de pagamento raramente mudam)


def get_bling_payment_methods(force_refresh: bool = False) -> List[Dict]:
    """
    Busca todas as formas de pagamento do Bling
    
    Args:
        force_refresh: Se True, força atualização do cache
    
    Returns:
        Lista de formas de pagamento do Bling
    """
    global _formas_pagamento_cache, _cache_timestamp
    import time
    
    # Verificar cache
    if not force_refresh and _formas_pagamento_cache and _cache_timestamp:
        if time.time() - _cache_timestamp < CACHE_DURATION:
            current_app.logger.debug(
                f"📋 Usando cache de formas de pagamento ({len(_formas_pagamento_cache)} formas)"
            )
            return _formas_pagamento_cache
    
    try:
        current_app.logger.info("🔍 Buscando formas de pagamento do Bling...")
        
        response = make_bling_api_request(
            'GET',
            '/formas-pagamentos',
            params={'limite': 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            formas_pagamento = data.get('data', [])
            
            # Atualizar cache
            _formas_pagamento_cache = formas_pagamento
            _cache_timestamp = time.time()
            
            current_app.logger.info(
                f"✅ {len(formas_pagamento)} forma(s) de pagamento encontrada(s) no Bling"
            )
            
            # Logar todas as formas para referência
            for forma in formas_pagamento:
                current_app.logger.debug(
                    f"   - ID: {forma.get('id')}, Descrição: {forma.get('descricao', 'N/A')}, "
                    f"Tipo: {forma.get('tipoPagamento', 'N/A')}"
                )
            
            return formas_pagamento
        else:
            current_app.logger.error(
                f"❌ Erro ao buscar formas de pagamento: HTTP {response.status_code}"
            )
            return []
            
    except Exception as e:
        current_app.logger.error(
            f"❌ Erro ao buscar formas de pagamento do Bling: {e}", 
            exc_info=True
        )
        return []


def map_checkout_payment_to_bling(forma_pagamento_tipo: str, num_parcelas: int = None) -> Optional[int]:
    """
    Mapeia forma de pagamento do checkout para ID do Bling
    
    Baseado na documentação do Bling:
    - tipoPagamento 3 = Cartão de Crédito
    - tipoPagamento 4 = Cartão de Débito
    - tipoPagamento 15 = Boleto Bancário
    - tipoPagamento 17 = PIX Dinâmico
    - tipoPagamento 20 = PIX Estático
    
    Args:
        forma_pagamento_tipo: Tipo de pagamento do checkout (PIX, CREDIT_CARD, BOLETO, etc.)
        num_parcelas: Número de parcelas (opcional, usado para cartão de crédito)
    
    Returns:
        ID da forma de pagamento no Bling ou None se não encontrado
    """
    formas_pagamento = get_bling_payment_methods()
    
    if not formas_pagamento:
        current_app.logger.warning(
            f"⚠️ Nenhuma forma de pagamento encontrada no Bling para mapear '{forma_pagamento_tipo}'"
        )
        return None
    
    # Filtrar apenas formas ativas
    formas_ativas = [f for f in formas_pagamento if f.get('situacao') == 1]
    
    if not formas_ativas:
        current_app.logger.warning(
            f"⚠️ Nenhuma forma de pagamento ativa encontrada no Bling"
        )
        return None
    
    # Normalizar tipo de pagamento
    tipo_normalizado = forma_pagamento_tipo.upper().strip()
    
    # Mapeamento de tipoPagamento conforme documentação do Bling
    tipo_pagamento_map = {
        'PIX': [17, 20],  # PIX Dinâmico e Estático
        'CREDIT_CARD': [3],  # Cartão de Crédito
        'BOLETO': [15],  # Boleto Bancário
        'DEBIT_CARD': [4],  # Cartão de Débito
    }
    
    current_app.logger.info(
        f"🔍 Mapeando '{forma_pagamento_tipo}' para forma de pagamento do Bling"
    )
    
    # Estratégia 1: Buscar por tipoPagamento (mais confiável)
    tipos_pagamento = tipo_pagamento_map.get(tipo_normalizado)
    
    if tipos_pagamento:
        formas_filtradas = [
            f for f in formas_ativas 
            if f.get('tipoPagamento') in tipos_pagamento
        ]
        
        if formas_filtradas:
            # Para PIX, priorizar PIX Dinâmico (17) sobre Estático (20)
            if tipo_normalizado == 'PIX':
                pix_dinamico = [f for f in formas_filtradas if f.get('tipoPagamento') == 17]
                if pix_dinamico:
                    formas_filtradas = pix_dinamico
            
            # Para CREDIT_CARD, escolher forma baseada no número de parcelas
            if tipo_normalizado == 'CREDIT_CARD':
                if num_parcelas and num_parcelas > 1:
                    # Tentar encontrar forma específica para o número de parcelas
                    formas_parcelas = [
                        f for f in formas_filtradas 
                        if f'{num_parcelas}x' in f.get('descricao', '').lower()
                    ]
                    if formas_parcelas:
                        formas_filtradas = formas_parcelas
                    else:
                        # Se não encontrou específica, usar a primeira disponível
                        current_app.logger.info(
                            f"⚠️ Forma de pagamento específica para {num_parcelas}x não encontrada, "
                            f"usando primeira disponível"
                        )
                else:
                    # Para pagamento à vista (1 parcela), priorizar formas genéricas
                    # IMPORTANTE: Excluir formas que contenham números de parcelas maiores (2x, 3x, 11x, etc)
                    formas_genericas = []
                    for f in formas_filtradas:
                        descricao_lower = f.get('descricao', '').lower()
                        # Verificar se contém "1x" explicitamente OU não contém nenhum número seguido de "x"
                        tem_1x = '1x' in descricao_lower
                        # Verificar se tem outros números de parcelas (2x, 3x, 4x, 5x, 6x, 7x, 8x, 9x, 10x, 11x, 12x)
                        tem_outras_parcelas = any(f'{i}x' in descricao_lower for i in range(2, 13))
                        
                        if tem_1x and not tem_outras_parcelas:
                            # Tem "1x" e não tem outras parcelas
                            formas_genericas.append(f)
                        elif not tem_1x and not tem_outras_parcelas and 'x' not in descricao_lower:
                            # Não tem "x" (forma genérica sem especificar parcelas)
                            formas_genericas.append(f)
                    
                    if formas_genericas:
                        formas_filtradas = formas_genericas
                    else:
                        # Se não encontrou forma genérica, logar aviso e usar a primeira disponível
                        current_app.logger.warning(
                            f"⚠️ Não encontrada forma de pagamento genérica para 1 parcela. "
                            f"Usando primeira disponível: {formas_filtradas[0].get('descricao') if formas_filtradas else 'N/A'}"
                        )
            
            # Escolher a primeira forma disponível
            forma_escolhida = formas_filtradas[0]
            bling_id = forma_escolhida.get('id')
            
            current_app.logger.info(
                f"✅ Mapeamento encontrado (tipoPagamento): "
                f"'{forma_pagamento_tipo}' → Bling ID {bling_id} "
                f"('{forma_escolhida.get('descricao')}', tipoPagamento: {forma_escolhida.get('tipoPagamento')})"
            )
            return bling_id
    
    # Estratégia 2: Buscar por descrição (fallback)
    search_terms_map = {
        'PIX': ['pix', 'pagamento instantâneo', 'pagamento instantaneo'],
        'CREDIT_CARD': ['cartão de crédito', 'cartao de credito', 'crédito', 'credito'],
        'BOLETO': ['boleto', 'boleto bancário', 'boleto bancario'],
        'DEBIT_CARD': ['cartão de débito', 'cartao de debito', 'débito', 'debito'],
    }
    
    search_terms = search_terms_map.get(tipo_normalizado, [tipo_normalizado.lower()])
    
    for forma in formas_ativas:
        descricao = forma.get('descricao', '').lower().strip()
        
        for term in search_terms:
            term_lower = term.lower()
            if term_lower in descricao:
                bling_id = forma.get('id')
                current_app.logger.info(
                    f"✅ Mapeamento encontrado (descrição): "
                    f"'{forma_pagamento_tipo}' → Bling ID {bling_id} "
                    f"('{forma.get('descricao')}')"
                )
                return bling_id
    
    # Se não encontrou, listar formas disponíveis para debug
    formas_disponiveis = [
        f"ID {f.get('id')}: {f.get('descricao', 'N/A')} "
        f"(tipoPagamento: {f.get('tipoPagamento')}, situacao: {f.get('situacao')})"
        for f in formas_ativas[:10]
    ]
    
    current_app.logger.warning(
        f"⚠️ Forma de pagamento '{forma_pagamento_tipo}' não encontrada no Bling.\n"
        f"📋 Formas ativas disponíveis no Bling (primeiras 10):\n"
        f"   {chr(10).join(formas_disponiveis)}"
    )
    
    return None


def get_payment_method_by_id(bling_id: int) -> Optional[Dict]:
    """
    Busca forma de pagamento do Bling por ID
    
    Args:
        bling_id: ID da forma de pagamento no Bling
    
    Returns:
        Dict com dados da forma de pagamento ou None se não encontrado
    """
    formas_pagamento = get_bling_payment_methods()
    
    for forma in formas_pagamento:
        if forma.get('id') == bling_id:
            return forma
    
    return None
