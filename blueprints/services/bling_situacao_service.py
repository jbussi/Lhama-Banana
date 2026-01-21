"""
Service para gerenciar situações de pedidos do Bling
=====================================================

Este módulo gerencia o mapeamento entre situações do Bling (ID) e status do site.
"""
from flask import current_app
from typing import Dict, Optional, List
from datetime import datetime
import psycopg2.extras
from .db import get_db
from .bling_api_service import make_bling_api_request


def get_bling_situacao_by_id(situacao_id: int) -> Optional[Dict]:
    """
    Busca uma situação específica do Bling pelo ID
    
    Args:
        situacao_id: ID da situação no Bling
    
    Returns:
        Dict com dados da situação ou None se não encontrado
    """
    try:
        response = make_bling_api_request(
            'GET',
            f'/situacoes/{situacao_id}'
        )
        
        if response.status_code == 200:
            data = response.json()
            situacao = data.get('data', {})
            
            current_app.logger.info(
                f"✅ Situação encontrada no Bling: ID {situacao_id} - {situacao.get('nome')}"
            )
            
            return {
                'id': situacao.get('id'),
                'nome': situacao.get('nome'),
                'cor': situacao.get('cor'),
                'id_herdado': situacao.get('idHerdado', 0)
            }
        else:
            current_app.logger.warning(
                f"⚠️ Erro ao buscar situação {situacao_id} no Bling: HTTP {response.status_code}"
            )
            return None
            
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar situação {situacao_id} no Bling: {e}")
        return None


def get_all_bling_situacoes() -> List[Dict]:
    """
    Busca todas as situações disponíveis no Bling
    
    Returns:
        Lista de dicts com dados das situações
    """
    try:
        situacoes = []
        page = 1
        limit = 100
        
        while True:
            response = make_bling_api_request(
                'GET',
                '/situacoes',
                params={
                    'pagina': page,
                    'limite': limit
                }
            )
            
            if response.status_code != 200:
                current_app.logger.warning(
                    f"⚠️ Erro ao buscar situações do Bling: HTTP {response.status_code}"
                )
                break
            
            data = response.json()
            situacoes_page = data.get('data', [])
            
            if not situacoes_page:
                break
            
            for situacao in situacoes_page:
                situacoes.append({
                    'id': situacao.get('id'),
                    'nome': situacao.get('nome'),
                    'cor': situacao.get('cor'),
                    'id_herdado': situacao.get('idHerdado', 0)
                })
            
            # Verificar se há mais páginas
            paginacao = data.get('paginacao', {})
            total_paginas = paginacao.get('totalPaginas', 1)
            
            if page >= total_paginas:
                break
            
            page += 1
        
        current_app.logger.info(f"✅ Total de {len(situacoes)} situações encontradas no Bling")
        return situacoes
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar situações do Bling: {e}")
        return []


def sync_bling_situacoes_to_db() -> Dict:
    """
    Sincroniza todas as situações do Bling para o banco de dados local
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        # Buscar todas as situações do Bling
        situacoes_bling = get_all_bling_situacoes()
        
        if not situacoes_bling:
            return {
                'success': False,
                'error': 'Nenhuma situação encontrada no Bling'
            }
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            sincronizadas = 0
            atualizadas = 0
            
            for situacao in situacoes_bling:
                bling_id = situacao['id']
                nome = situacao['nome']
                cor = situacao.get('cor', '')
                id_herdado = situacao.get('id_herdado', 0)
                
                # Verificar se já existe
                cur.execute("""
                    SELECT id, nome, cor, status_site
                    FROM bling_situacoes
                    WHERE bling_situacao_id = %s
                """, (bling_id,))
                
                existente = cur.fetchone()
                
                if existente:
                    # Atualizar se houver mudanças
                    id_herdado_existente = existente.get('id_herdado', 0)
                    if (existente['nome'] != nome or 
                        existente.get('cor') != cor or
                        id_herdado_existente != id_herdado):
                        
                        cur.execute("""
                            UPDATE bling_situacoes
                            SET nome = %s,
                                cor = %s,
                                id_herdado = %s,
                                atualizado_em = NOW()
                            WHERE bling_situacao_id = %s
                        """, (nome, cor, id_herdado, bling_id))
                        
                        atualizadas += 1
                        current_app.logger.info(
                            f"🔄 Situação atualizada: {nome} (ID: {bling_id})"
                        )
                else:
                    # Inserir nova situação
                    cur.execute("""
                        INSERT INTO bling_situacoes 
                        (bling_situacao_id, nome, cor, id_herdado, ativo)
                        VALUES (%s, %s, %s, %s, TRUE)
                    """, (bling_id, nome, cor, id_herdado))
                    
                    sincronizadas += 1
                    current_app.logger.info(
                        f"➕ Situação adicionada: {nome} (ID: {bling_id})"
                    )
            
            conn.commit()
            
            return {
                'success': True,
                'total': len(situacoes_bling),
                'sincronizadas': sincronizadas,
                'atualizadas': atualizadas,
                'message': f'Sincronização concluída: {sincronizadas} novas, {atualizadas} atualizadas'
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao sincronizar situações do Bling: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_situacao_mapping(bling_situacao_id: int) -> Optional[Dict]:
    """
    Busca o mapeamento de uma situação do Bling para status do site
    
    Args:
        bling_situacao_id: ID da situação no Bling
    
    Returns:
        Dict com dados da situação e mapeamento ou None
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                bling_situacao_id,
                nome,
                cor,
                status_site,
                ativo
            FROM bling_situacoes
            WHERE bling_situacao_id = %s
        """, (bling_situacao_id,))
        
        situacao = cur.fetchone()
        
        if situacao:
            return dict(situacao)
        
        return None
        
    finally:
        cur.close()


def map_bling_situacao_id_to_status(bling_situacao_id: int) -> Optional[str]:
    """
    Mapeia ID da situação do Bling para status do site
    
    Args:
        bling_situacao_id: ID da situação no Bling
    
    Returns:
        Status do site correspondente ou None se não mapeado
    """
    mapping = get_situacao_mapping(bling_situacao_id)
    
    if mapping and mapping.get('status_site'):
        return mapping['status_site']
    
    # Se não houver mapeamento explícito, tentar mapear pelo nome
    if mapping:
        nome = mapping.get('nome', '').lower()
        
        # Mapeamento padrão baseado no nome
        nome_to_status = {
            'em aberto': 'sincronizado_bling',
            'em andamento': 'em_processamento',
            'atendido': 'entregue',
            'cancelado': 'cancelado_pelo_vendedor',
            'venda agenciada': 'em_processamento',
            'em digitação': 'pendente_pagamento',
            'verificado': 'em_processamento',
            'venda atendimento humano': 'em_processamento',
            'logística': 'pronto_envio'
        }
        
        for key, status in nome_to_status.items():
            if key in nome:
                return status
    
    return None


def update_situacao_mapping(bling_situacao_id: int, status_site: str) -> bool:
    """
    Atualiza o mapeamento de uma situação do Bling para status do site
    
    Args:
        bling_situacao_id: ID da situação no Bling
        status_site: Status correspondente no site
    
    Returns:
        True se atualizado com sucesso
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE bling_situacoes
            SET status_site = %s,
                atualizado_em = NOW()
            WHERE bling_situacao_id = %s
        """, (status_site, bling_situacao_id))
        
        conn.commit()
        
        updated = cur.rowcount > 0
        
        if updated:
            current_app.logger.info(
                f"✅ Mapeamento atualizado: Situação {bling_situacao_id} → {status_site}"
            )
        
        return updated
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"❌ Erro ao atualizar mapeamento: {e}")
        return False
    finally:
        cur.close()


def update_pedido_situacao(venda_id: int, bling_situacao_id: int, 
                           bling_situacao_nome: str = None) -> bool:
    """
    Atualiza a situação do Bling em um pedido local
    
    Args:
        venda_id: ID da venda local
        bling_situacao_id: ID da situação no Bling
        bling_situacao_nome: Nome da situação (opcional, será buscado se não fornecido)
    
    Returns:
        True se atualizado com sucesso
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Buscar nome da situação se não fornecido
        if not bling_situacao_nome:
            situacao = get_situacao_mapping(bling_situacao_id)
            if situacao:
                bling_situacao_nome = situacao.get('nome')
        
        # Mapear situação para status do site
        status_site = map_bling_situacao_id_to_status(bling_situacao_id)
        
        # Atualizar pedido
        if status_site:
            cur.execute("""
                UPDATE vendas
                SET status_pedido = %s,
                    bling_situacao_id = %s,
                    bling_situacao_nome = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (status_site, bling_situacao_id, bling_situacao_nome, venda_id))
        else:
            # Se não houver mapeamento, apenas atualizar situação do Bling
            cur.execute("""
                UPDATE vendas
                SET bling_situacao_id = %s,
                    bling_situacao_nome = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (bling_situacao_id, bling_situacao_nome, venda_id))
        
        conn.commit()
        
        updated = cur.rowcount > 0
        
        if updated:
            current_app.logger.info(
                f"✅ Pedido {venda_id} atualizado: Situação Bling {bling_situacao_id} "
                f"({bling_situacao_nome}) → Status site: {status_site or 'sem mapeamento'}"
            )
        
        return updated
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"❌ Erro ao atualizar situação do pedido {venda_id}: {e}")
        return False
    finally:
        cur.close()
