"""
Service para Analytics e Dashboards com Bling
==============================================

Extrai métricas e insights financeiros e de vendas do Bling:
- Faturamento bruto
- Ticket médio
- Vendas por período
- Produtos mais vendidos
- Contas a receber em aberto
- Impacto de frete e descontos
- Margem aproximada
"""
from flask import current_app
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .bling_api_service import make_bling_api_request
import json


def get_financial_dashboard(start_date: str = None, end_date: str = None) -> Dict:
    """
    Busca métricas financeiras do Bling para dashboard
    
    Args:
        start_date: Data inicial (YYYY-MM-DD)
        end_date: Data final (YYYY-MM-DD)
    
    Returns:
        Dict com métricas financeiras
    """
    try:
        # Se não especificado, usar último mês
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Buscar pedidos de venda no período
        params = {
            'dataInicial': start_date,
            'dataFinal': end_date
        }
        
        response = make_bling_api_request(
            'GET',
            '/pedidos/vendas',
            params=params
        )
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro ao buscar dados: HTTP {response.status_code}'
            }
        
        data = response.json()
        pedidos = data.get('data', [])
        
        # Calcular métricas
        total_pedidos = len(pedidos)
        faturamento_bruto = sum(
            float(pedido.get('total', 0)) for pedido in pedidos
            if pedido.get('situacao') not in ['C', 'X']  # Não cancelados
        )
        
        ticket_medio = faturamento_bruto / total_pedidos if total_pedidos > 0 else 0
        
        # Calcular frete total
        frete_total = sum(
            float(pedido.get('valores', {}).get('valorFrete', 0) or 0)
            for pedido in pedidos
        )
        
        # Calcular descontos total
        descontos_total = sum(
            float(pedido.get('valores', {}).get('desconto', 0) or 0)
            for pedido in pedidos
        )
        
        # Contas a receber em aberto
        contas_abertas = get_open_accounts_receivable()
        
        return {
            'success': True,
            'periodo': {
                'inicio': start_date,
                'fim': end_date
            },
            'faturamento': {
                'bruto': faturamento_bruto,
                'ticket_medio': ticket_medio,
                'total_pedidos': total_pedidos
            },
            'frete': {
                'total': frete_total,
                'percentual_faturamento': (frete_total / faturamento_bruto * 100) if faturamento_bruto > 0 else 0
            },
            'descontos': {
                'total': descontos_total,
                'percentual_faturamento': (descontos_total / faturamento_bruto * 100) if faturamento_bruto > 0 else 0
            },
            'contas_receber': contas_abertas
        }
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar dashboard financeiro: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_sales_by_period(start_date: str = None, end_date: str = None, group_by: str = 'day') -> Dict:
    """
    Busca vendas agrupadas por período
    
    Args:
        start_date: Data inicial
        end_date: Data final
        group_by: 'day', 'week', 'month'
    
    Returns:
        Dict com vendas agrupadas
    """
    try:
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = make_bling_api_request(
            'GET',
            '/pedidos/vendas',
            params={
                'dataInicial': start_date,
                'dataFinal': end_date
            }
        )
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro ao buscar vendas: HTTP {response.status_code}'
            }
        
        data = response.json()
        pedidos = data.get('data', [])
        
        # Agrupar por período
        vendas_por_periodo = {}
        
        for pedido in pedidos:
            if pedido.get('situacao') in ['C', 'X']:  # Ignorar cancelados
                continue
            
            data_pedido = pedido.get('data', '')
            if not data_pedido:
                continue
            
            # Parsear data
            try:
                dt = datetime.fromisoformat(data_pedido.replace('Z', '+00:00'))
            except:
                continue
            
            # Agrupar conforme group_by
            if group_by == 'day':
                key = dt.strftime('%Y-%m-%d')
            elif group_by == 'week':
                # Semana (ano-semana)
                year, week, _ = dt.isocalendar()
                key = f"{year}-W{week:02d}"
            elif group_by == 'month':
                key = dt.strftime('%Y-%m')
            else:
                key = dt.strftime('%Y-%m-%d')
            
            if key not in vendas_por_periodo:
                vendas_por_periodo[key] = {
                    'data': key,
                    'quantidade': 0,
                    'faturamento': 0.0
                }
            
            vendas_por_periodo[key]['quantidade'] += 1
            vendas_por_periodo[key]['faturamento'] += float(pedido.get('total', 0))
        
        # Ordenar por data
        vendas_lista = sorted(
            vendas_por_periodo.values(),
            key=lambda x: x['data']
        )
        
        return {
            'success': True,
            'periodo': {
                'inicio': start_date,
                'fim': end_date,
                'agrupamento': group_by
            },
            'vendas': vendas_lista,
            'total': len(vendas_lista)
        }
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar vendas por período: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_top_products(start_date: str = None, end_date: str = None, limit: int = 10) -> Dict:
    """
    Busca produtos mais vendidos no período
    
    Args:
        start_date: Data inicial
        end_date: Data final
        limit: Número de produtos a retornar
    
    Returns:
        Dict com produtos mais vendidos
    """
    try:
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = make_bling_api_request(
            'GET',
            '/pedidos/vendas',
            params={
                'dataInicial': start_date,
                'dataFinal': end_date
            }
        )
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Erro ao buscar pedidos: HTTP {response.status_code}'
            }
        
        data = response.json()
        pedidos = data.get('data', [])
        
        # Agregar produtos
        produtos_vendidos = {}
        
        for pedido in pedidos:
            if pedido.get('situacao') in ['C', 'X']:  # Ignorar cancelados
                continue
            
            itens = pedido.get('itens', [])
            
            for item in itens:
                produto_id = item.get('produto', {}).get('id')
                produto_nome = item.get('produto', {}).get('nome', 'Produto Desconhecido')
                quantidade = float(item.get('quantidade', 0))
                valor_total = float(item.get('valor', 0))
                
                if produto_id not in produtos_vendidos:
                    produtos_vendidos[produto_id] = {
                        'produto_id': produto_id,
                        'nome': produto_nome,
                        'quantidade_vendida': 0,
                        'faturamento': 0.0,
                        'pedidos': 0
                    }
                
                produtos_vendidos[produto_id]['quantidade_vendida'] += quantidade
                produtos_vendidos[produto_id]['faturamento'] += valor_total
                produtos_vendidos[produto_id]['pedidos'] += 1
        
        # Ordenar por faturamento e limitar
        produtos_ordenados = sorted(
            produtos_vendidos.values(),
            key=lambda x: x['faturamento'],
            reverse=True
        )[:limit]
        
        return {
            'success': True,
            'periodo': {
                'inicio': start_date,
                'fim': end_date
            },
            'produtos': produtos_ordenados,
            'total': len(produtos_ordenados)
        }
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar produtos mais vendidos: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_open_accounts_receivable() -> Dict:
    """
    Busca contas a receber em aberto no Bling
    
    Returns:
        Dict com informações de contas a receber em aberto
    """
    try:
        # Buscar contas a receber em aberto
        # Status: ABERTA, VENCIDA, VENCENDO
        response = make_bling_api_request(
            'GET',
            '/contas/receber',
            params={
                'situacao': 'A'  # Aberta
            }
        )
        
        if response.status_code != 200:
            return {
                'total_aberto': 0,
                'quantidade': 0,
                'error': f'Erro HTTP {response.status_code}'
            }
        
        data = response.json()
        contas = data.get('data', [])
        
        total_aberto = sum(
            float(conta.get('valor', 0)) - float(conta.get('valorRecebido', 0))
            for conta in contas
        )
        
        # Contas vencidas
        hoje = datetime.now().date()
        contas_vencidas = [
            conta for conta in contas
            if conta.get('vencimento') and 
            datetime.fromisoformat(conta['vencimento'].split('T')[0]).date() < hoje
        ]
        
        total_vencidas = sum(
            float(conta.get('valor', 0)) - float(conta.get('valorRecebido', 0))
            for conta in contas_vencidas
        )
        
        return {
            'total_aberto': total_aberto,
            'quantidade': len(contas),
            'total_vencidas': total_vencidas,
            'quantidade_vencidas': len(contas_vencidas)
        }
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar contas a receber: {e}", exc_info=True)
        return {
            'total_aberto': 0,
            'quantidade': 0,
            'error': str(e)
        }


def get_local_vs_bling_comparison(start_date: str = None, end_date: str = None) -> Dict:
    """
    Compara dados locais com dados do Bling
    
    Útil para verificar se há divergências entre sistemas
    
    Args:
        start_date: Data inicial
        end_date: Data final
    
    Returns:
        Dict com comparação de métricas
    """
    try:
        from .db import get_db
        import psycopg2.extras
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Buscar dados locais
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_pedidos,
                    COALESCE(SUM(valor_total), 0) as faturamento,
                    COALESCE(SUM(valor_frete), 0) as frete_total,
                    COALESCE(SUM(valor_desconto), 0) as desconto_total
                FROM vendas
                WHERE data_venda >= %s
                  AND data_venda <= %s
                  AND status_pedido NOT IN ('cancelado_pelo_cliente', 'cancelado_pelo_vendedor', 'reembolsado')
            """, (start_date, end_date))
            
            local_data = cur.fetchone()
            
        finally:
            cur.close()
        
        # Buscar dados do Bling
        bling_data = get_financial_dashboard(start_date, end_date)
        
        if not bling_data.get('success'):
            return {
                'success': False,
                'error': 'Erro ao buscar dados do Bling',
                'local': {
                    'total_pedidos': local_data['total_pedidos'] if local_data else 0,
                    'faturamento': float(local_data['faturamento']) if local_data else 0.0
                }
            }
        
        # Comparar
        local_faturamento = float(local_data['faturamento']) if local_data else 0.0
        bling_faturamento = bling_data.get('faturamento', {}).get('bruto', 0.0)
        
        divergencia = local_faturamento - bling_faturamento
        percentual_divergencia = (divergencia / local_faturamento * 100) if local_faturamento > 0 else 0
        
        return {
            'success': True,
            'periodo': {
                'inicio': start_date,
                'fim': end_date
            },
            'local': {
                'total_pedidos': local_data['total_pedidos'] if local_data else 0,
                'faturamento': local_faturamento,
                'frete_total': float(local_data['frete_total']) if local_data else 0.0,
                'desconto_total': float(local_data['desconto_total']) if local_data else 0.0
            },
            'bling': {
                'total_pedidos': bling_data.get('faturamento', {}).get('total_pedidos', 0),
                'faturamento': bling_faturamento,
                'frete_total': bling_data.get('frete', {}).get('total', 0.0),
                'desconto_total': bling_data.get('descontos', {}).get('total', 0.0)
            },
            'divergencia': {
                'faturamento': divergencia,
                'percentual': percentual_divergencia,
                'total_pedidos': (local_data['total_pedidos'] if local_data else 0) - bling_data.get('faturamento', {}).get('total_pedidos', 0)
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao comparar dados locais vs Bling: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

