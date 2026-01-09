"""
Service para sincronização de produtos com Bling
================================================

Este módulo implementa a sincronização de produtos do LhamaBanana para o Bling.
"""
from flask import current_app
from typing import Dict, Optional, List
import time
import json
import psycopg2.extras
from .db import get_db
from .bling_api_service import make_bling_api_request


def get_product_for_bling_sync(produto_id: int) -> Optional[Dict]:
    """
    Busca produto completo do banco com todas as informações necessárias para Bling
    
    Returns:
        Dict com dados do produto ou None se não encontrado
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                p.id,
                p.codigo_sku,
                p.ncm,
                p.preco_venda,
                p.preco_promocional,
                p.custo,
                p.estoque,
                p.estoque_minimo,
                p.ativo,
                p.codigo_barras,
                -- Dados do nome_produto
                np.nome,
                np.descricao,
                np.descricao_curta,
                np.peso_kg,
                np.dimensoes_largura,
                np.dimensoes_altura,
                np.dimensoes_comprimento,
                -- Dados da categoria
                c.nome as categoria_nome,
                -- Estampa e tamanho para nome completo
                e.nome as estampa_nome,
                t.nome as tamanho_nome
            FROM produtos p
            JOIN nome_produto np ON p.nome_produto_id = np.id
            LEFT JOIN categorias c ON np.categoria_id = c.id
            LEFT JOIN estampa e ON p.estampa_id = e.id
            LEFT JOIN tamanho t ON p.tamanho_id = t.id
            WHERE p.id = %s
        """, (produto_id,))
        
        produto = cur.fetchone()
        
        if not produto:
            return None
        
        return dict(produto)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar produto {produto_id}: {e}")
        return None
    finally:
        cur.close()


def validate_product_for_bling(produto: Dict) -> List[str]:
    """
    Valida produto antes de enviar para Bling
    
    Validações fiscais aplicadas:
    - NCM: obrigatório, 8 dígitos
    - SKU: obrigatório
    - Preço: obrigatório, > 0
    - Nome: obrigatório
    
    NOTA: CFOP não é validado aqui pois não é atributo do produto,
    mas sim do pedido/NF (depende da natureza da transação).
    
    Returns:
        Lista de erros (vazia se válido)
    """
    errors = []
    
    # NCM obrigatório (8 dígitos) - Campo fiscal essencial
    ncm = produto.get('ncm')
    if not ncm or len(str(ncm)) != 8:
        errors.append("NCM obrigatório e deve ter 8 dígitos")
    elif not str(ncm).isdigit():
        errors.append("NCM deve conter apenas dígitos")
    
    # SKU obrigatório
    if not produto.get('codigo_sku'):
        errors.append("SKU obrigatório")
    
    # Preço deve ser maior que zero
    preco = produto.get('preco_venda') or produto.get('preco_promocional')
    if not preco or float(preco) <= 0:
        errors.append("Preço de venda deve ser maior que zero")
    
    # Nome do produto obrigatório
    if not produto.get('nome'):
        errors.append("Nome do produto obrigatório")
    
    # CEST (opcional, mas se informado deve ter 7 dígitos)
    # CEST é obrigatório apenas para produtos sujeitos a ST
    # Se o banco tiver campo 'cest', adicionar validação:
    # cest = produto.get('cest')
    # if cest and (len(str(cest)) != 7 or not str(cest).isdigit()):
    #     errors.append("CEST deve ter 7 dígitos (se informado)")
    
    return errors


def map_product_to_bling_format(produto: Dict) -> Dict:
    """
    Mapeia produto do formato LhamaBanana para formato Bling
    
    Args:
        produto: Dict com dados do produto do banco
    
    Returns:
        Dict formatado para API do Bling
    """
    # Preço promocional tem prioridade sobre preço de venda
    preco_final = float(produto.get('preco_promocional') or produto.get('preco_venda', 0))
    preco_custo = float(produto.get('custo', 0)) if produto.get('custo') else None
    
    # Montar nome completo do produto (nome + estampa + tamanho)
    nome_base = produto.get('nome', 'Produto sem nome')
    estampa = produto.get('estampa_nome', '')
    tamanho = produto.get('tamanho_nome', '')
    
    # Construir nome completo: "Nome - Estampa - Tamanho"
    partes_nome = [nome_base]
    if estampa:
        partes_nome.append(estampa)
    if tamanho:
        partes_nome.append(f"Tamanho {tamanho}")
    
    nome_completo = " - ".join(partes_nome)
    
    # Mapear situação (ativo/inativo)
    ativo = produto.get('ativo', True)
    situacao = "A" if ativo else "I"  # A=Ativo, I=Inativo
    
    bling_product = {
        "nome": nome_completo,
        "codigo": produto.get('codigo_sku'),
        "preco": preco_final,
        "tipo": "P",  # P=Produto, S=Serviço, K=Kit
        "formato": "S",  # S=Simples, V=Variável, C=Composto
        "unidade": "UN",  # Unidade padrão
        "ncm": produto.get('ncm'),
        "situacao": situacao,  # A=Ativo, I=Inativo (obrigatório)
    }
    
    # Preço de custo (opcional)
    if preco_custo and preco_custo > 0:
        bling_product["precoCusto"] = preco_custo
    
    # Estoque
    estoque_atual = produto.get('estoque', 0) or 0
    estoque_minimo = produto.get('estoque_minimo', 0) or 0
    
    bling_product["estoque"] = {
        "minimo": int(estoque_minimo),
        "maximo": 0,  # Não configurado
        "atual": int(estoque_atual)
    }
    
    # Peso e dimensões (se disponíveis)
    if produto.get('peso_kg'):
        bling_product["pesoLiq"] = float(produto['peso_kg'])
        bling_product["pesoBruto"] = float(produto['peso_kg'])  # Assumir igual se não tiver separado
    
    if produto.get('dimensoes_largura'):
        bling_product["largura"] = float(produto['dimensoes_largura'])
    if produto.get('dimensoes_altura'):
        bling_product["altura"] = float(produto['dimensoes_altura'])
    if produto.get('dimensoes_comprimento'):
        bling_product["profundidade"] = float(produto['dimensoes_comprimento'])
    
    # Descrições
    if produto.get('descricao_curta'):
        bling_product["descricaoCurta"] = produto['descricao_curta']
    if produto.get('descricao'):
        bling_product["descricaoComplementar"] = produto['descricao']
    
    # Código de barras (se disponível)
    if produto.get('codigo_barras'):
        bling_product["gtin"] = produto['codigo_barras']
    
    # CEST (opcional, para produtos com substituição tributária)
    # O CEST é obrigatório apenas para produtos sujeitos a ST (Substituição Tributária)
    # Se o banco tiver campo 'cest', descomentar a linha abaixo:
    # if produto.get('cest'):
    #     bling_product["cest"] = produto.get('cest')
    
    # NOTA IMPORTANTE:
    # CFOP (Código Fiscal de Operações e Prestações) NÃO é campo do produto,
    # mas sim do pedido/nota fiscal, pois depende da natureza da transação:
    # - Dentro do mesmo estado: CFOP 5102
    # - Interestadual: CFOP 6108
    # O CFOP será tratado na criação do pedido (ETAPA 6) e emissão de NF-e (ETAPA 7)
    
    return bling_product


def sync_product_to_bling(produto_id: int, force_update: bool = False) -> Dict:
    """
    Sincroniza produto do LhamaBanana para Bling
    
    Args:
        produto_id: ID do produto no banco local
        force_update: Se True, força atualização mesmo se já sincronizado
    
    Returns:
        Dict com resultado da sincronização
    """
    # 1. Buscar produto do banco
    produto = get_product_for_bling_sync(produto_id)
    
    if not produto:
        return {
            'success': False,
            'error': f'Produto {produto_id} não encontrado'
        }
    
    # 2. Validar produto
    validation_errors = validate_product_for_bling(produto)
    if validation_errors:
        log_sync('produto', produto_id, 'error', {
            'error': 'Validação falhou',
            'errors': validation_errors
        })
        return {
            'success': False,
            'error': 'Validação falhou',
            'details': validation_errors
        }
    
    # 3. Verificar se já está sincronizado
    bling_produto = get_bling_product_by_local_id(produto_id)
    
    # 4. Preparar dados para Bling
    bling_product_data = map_product_to_bling_format(produto)
    
    try:
        # 5. Criar ou atualizar no Bling
        if bling_produto and not force_update:
            # Atualizar produto existente
            bling_id = bling_produto['bling_id']
            response = make_bling_api_request(
                'PUT',
                f'/produtos/{bling_id}',
                json=bling_product_data
            )
            action = 'update'
        else:
            # Criar novo produto
            response = make_bling_api_request(
                'POST',
                '/produtos',
                json=bling_product_data
            )
            action = 'create'
        
        # 6. Verificar resposta
        if response.status_code in [200, 201]:
            response_data = response.json()
            bling_product_response = response_data.get('data', {})
            bling_id = bling_product_response.get('id')
            
            # 7. Salvar referência no banco
            save_bling_product_reference(
                produto_id=produto_id,
                bling_id=bling_id,
                bling_codigo=produto.get('codigo_sku'),
                status='sync'
            )
            
            # 8. Log de sucesso
            log_sync('produto', produto_id, action, {
                'status': 'success',
                'bling_id': bling_id,
                'response': bling_product_response
            })
            
            return {
                'success': True,
                'action': action,
                'bling_id': bling_id,
                'message': f'Produto sincronizado com sucesso ({action})'
            }
        else:
            error_text = response.text
            current_app.logger.error(f"Erro ao sincronizar produto {produto_id}: {response.status_code} - {error_text}")
            
            # Log de erro
            log_sync('produto', produto_id, action, {
                'status': 'error',
                'error': error_text,
                'status_code': response.status_code
            })
            
            # Atualizar status de erro
            if bling_produto:
                update_bling_product_status(produto_id, 'error', error_text)
            
            return {
                'success': False,
                'error': f'Erro ao sincronizar com Bling',
                'details': error_text,
                'status_code': response.status_code
            }
            
    except Exception as e:
        current_app.logger.error(f"Exceção ao sincronizar produto {produto_id}: {e}", exc_info=True)
        
        log_sync('produto', produto_id, 'sync', {
            'status': 'error',
            'error': str(e)
        })
        
        if bling_produto:
            update_bling_product_status(produto_id, 'error', str(e))
        
        return {
            'success': False,
            'error': 'Erro ao sincronizar produto',
            'details': str(e)
        }


def get_bling_product_by_local_id(produto_id: int) -> Optional[Dict]:
    """
    Busca referência de produto sincronizado no Bling
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT id, produto_id, bling_id, bling_codigo, status_sincronizacao, erro_ultima_sync
            FROM bling_produtos
            WHERE produto_id = %s
        """, (produto_id,))
        
        result = cur.fetchone()
        return dict(result) if result else None
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar produto Bling: {e}")
        return None
    finally:
        cur.close()


def save_bling_product_reference(produto_id: int, bling_id: int, 
                                 bling_codigo: str, status: str = 'sync', 
                                 error: str = None):
    """
    Salva ou atualiza referência de produto sincronizado
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO bling_produtos (produto_id, bling_id, bling_codigo, status_sincronizacao, erro_ultima_sync, ultima_sincronizacao)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (produto_id) DO UPDATE
            SET bling_id = EXCLUDED.bling_id,
                bling_codigo = EXCLUDED.bling_codigo,
                status_sincronizacao = EXCLUDED.status_sincronizacao,
                erro_ultima_sync = EXCLUDED.erro_ultima_sync,
                ultima_sincronizacao = NOW(),
                updated_at = NOW()
        """, (produto_id, bling_id, bling_codigo, status, error))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao salvar referência Bling: {e}")
    finally:
        cur.close()


def update_bling_product_status(produto_id: int, status: str, error: str = None):
    """
    Atualiza status de sincronização de produto
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE bling_produtos
            SET status_sincronizacao = %s,
                erro_ultima_sync = %s,
                updated_at = NOW()
            WHERE produto_id = %s
        """, (status, error, produto_id))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao atualizar status: {e}")
    finally:
        cur.close()


def log_sync(entity_type: str, entity_id: int, action: str, details: Dict):
    """
    Registra log de sincronização
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        status = 'success' if details.get('status') == 'success' else 'error' if 'error' in details else 'pending'
        error_message = details.get('error') if status == 'error' else None
        
        cur.execute("""
            INSERT INTO bling_sync_logs (entity_type, entity_id, action, status, response_data, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (entity_type, entity_id, action, status, json.dumps(details), error_message))
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao registrar log: {e}")
    finally:
        cur.close()


def sync_all_products(limit: int = None, only_active: bool = True):
    """
    Sincroniza todos os produtos (worker periódico)
    
    Args:
        limit: Limite de produtos para sincronizar (None = todos)
        only_active: Sincronizar apenas produtos ativos
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT id FROM produtos
            WHERE ativo = %s
            ORDER BY id
        """
        params = [only_active]
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        
        cur.execute(query, params)
        produto_ids = [row[0] for row in cur.fetchall()]
        
        results = []
        for produto_id in produto_ids:
            try:
                result = sync_product_to_bling(produto_id)
                results.append({
                    'produto_id': produto_id,
                    'success': result.get('success', False),
                    'error': result.get('error')
                })
                
                # Rate limiting (Bling tem limites)
                time.sleep(0.5)  # 500ms entre requisições
                
            except Exception as e:
                current_app.logger.error(f"Erro ao sincronizar produto {produto_id}: {e}")
                results.append({
                    'produto_id': produto_id,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(produto_ids),
            'success': sum(1 for r in results if r['success']),
            'errors': sum(1 for r in results if not r['success']),
            'results': results
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar produtos: {e}")
        return {
            'total': 0,
            'success': 0,
            'errors': 0,
            'error': str(e)
        }
    finally:
        cur.close()


# =====================================================
# SINCRONIZAÇÃO BIDIRECIONAL: BLING → BANCO LOCAL
# =====================================================

def fetch_products_from_bling(limit: int = 100, offset: int = 0) -> Dict:
    """
    Busca produtos do Bling e cria/atualiza no banco local
    
    Args:
        limit: Quantidade de produtos por página
        offset: Offset para paginação
    
    Returns:
        Dict com lista de produtos do Bling
    """
    try:
        response = make_bling_api_request(
            'GET',
            '/produtos',
            params={
                'limite': limit,
                'pagina': (offset // limit) + 1
            }
        )
        
        if response.status_code != 200:
            current_app.logger.error(f"Erro ao buscar produtos do Bling: {response.status_code} - {response.text}")
            return {
                'success': False,
                'error': f"Erro HTTP {response.status_code}",
                'products': []
            }
        
        data = response.json()
        products = data.get('data', [])
        
        return {
            'success': True,
            'products': products,
            'total': len(products)
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar produtos do Bling: {e}")
        return {
            'success': False,
            'error': str(e),
            'products': []
        }


def create_local_product_from_bling(bling_product: Dict) -> Dict:
    """
    Cria produto no banco local a partir de produto do Bling
    
    Args:
        bling_product: Dict com dados do produto do Bling
    
    Returns:
        Dict com resultado da criação
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        bling_id = bling_product.get('id')
        codigo_sku = bling_product.get('codigo') or f"BLING-{bling_id}"
        nome = bling_product.get('nome', 'Produto sem nome')
        preco = float(bling_product.get('preco', 0))
        ncm = bling_product.get('ncm', '')
        estoque = bling_product.get('estoque', {}).get('atual', 0) if isinstance(bling_product.get('estoque'), dict) else 0
        
        # Verificar se produto já existe pelo SKU
        cur.execute("""
            SELECT id FROM produtos WHERE codigo_sku = %s
        """, (codigo_sku,))
        existing = cur.fetchone()
        
        if existing:
            produto_id = existing['id']
            # Atualizar produto existente
            cur.execute("""
                UPDATE produtos
                SET preco_venda = %s,
                    estoque = %s,
                    ncm = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (preco, estoque, ncm, produto_id))
            
            # Atualizar referência Bling
            save_bling_product_reference(produto_id, bling_id, codigo_sku, 'sync')
            
            action = 'update'
        else:
            # Criar novo produto
            # Primeiro, criar nome_produto se necessário
            cur.execute("""
                SELECT id FROM nome_produto WHERE nome = %s LIMIT 1
            """, (nome,))
            nome_produto_row = cur.fetchone()
            
            if not nome_produto_row:
                # Criar nome_produto básico
                cur.execute("""
                    INSERT INTO nome_produto (nome, ativo)
                    VALUES (%s, true)
                    RETURNING id
                """, (nome,))
                nome_produto_id = cur.fetchone()['id']
            else:
                nome_produto_id = nome_produto_row['id']
            
            # Buscar estampa e tamanho padrão (ou criar)
            cur.execute("SELECT id FROM estampa LIMIT 1")
            estampa_row = cur.fetchone()
            estampa_id = estampa_row['id'] if estampa_row else None
            
            cur.execute("SELECT id FROM tamanho LIMIT 1")
            tamanho_row = cur.fetchone()
            tamanho_id = tamanho_row['id'] if tamanho_row else None
            
            if not estampa_id or not tamanho_id:
                current_app.logger.warning("Estampa ou tamanho padrão não encontrado. Produto não pode ser criado.")
                return {
                    'success': False,
                    'error': 'Estampa ou tamanho padrão não configurado'
                }
            
            # Criar produto
            cur.execute("""
                INSERT INTO produtos (
                    nome_produto_id, estampa_id, tamanho_id,
                    codigo_sku, preco_venda, estoque, ncm, ativo, custo
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, true, %s)
                RETURNING id
            """, (nome_produto_id, estampa_id, tamanho_id, codigo_sku, preco, estoque, ncm, 0))
            
            produto_id = cur.fetchone()['id']
            
            # Salvar referência Bling
            save_bling_product_reference(produto_id, bling_id, codigo_sku, 'sync')
            
            action = 'create'
        
        conn.commit()
        
        log_sync('produto', produto_id, action, {
            'status': 'success',
            'bling_id': bling_id,
            'action': action
        })
        
        return {
            'success': True,
            'produto_id': produto_id,
            'action': action,
            'bling_id': bling_id
        }
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar produto do Bling: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        cur.close()


def sync_products_from_bling(limit: int = 50) -> Dict:
    """
    Sincroniza produtos do Bling para o banco local
    
    Args:
        limit: Quantidade de produtos para sincronizar
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        # Buscar produtos do Bling
        result = fetch_products_from_bling(limit=limit)
        
        if not result.get('success'):
            return result
        
        products = result.get('products', [])
        results = []
        
        for bling_product in products:
            try:
                result = create_local_product_from_bling(bling_product)
                results.append(result)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                current_app.logger.error(f"Erro ao criar produto do Bling: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'bling_id': bling_product.get('id')
                })
        
        return {
            'total': len(products),
            'success': sum(1 for r in results if r.get('success')),
            'errors': sum(1 for r in results if not r.get('success')),
            'results': results
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar produtos do Bling: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'results': []
        }


# =====================================================
# SINCRONIZAÇÃO DE ESTOQUE
# =====================================================

def sync_stock_from_bling(produto_id: int = None) -> Dict:
    """
    Sincroniza estoque do Bling para o banco local
    
    Se produto_id for None, sincroniza todos os produtos sincronizados
    
    Args:
        produto_id: ID do produto local (None = todos)
    
    Returns:
        Dict com resultado da sincronização
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        if produto_id:
            # Buscar apenas um produto
            cur.execute("""
                SELECT p.id, bp.bling_id, p.codigo_sku
                FROM produtos p
                JOIN bling_produtos bp ON p.id = bp.produto_id
                WHERE p.id = %s
            """, (produto_id,))
            products = cur.fetchall()
        else:
            # Buscar todos os produtos sincronizados
            cur.execute("""
                SELECT p.id, bp.bling_id, p.codigo_sku
                FROM produtos p
                JOIN bling_produtos bp ON p.id = bp.produto_id
                WHERE bp.status_sincronizacao = 'sync'
            """)
            products = cur.fetchall()
        
        results = []
        
        for product_row in products:
            try:
                produto_id_local = product_row['id']
                bling_id = product_row['bling_id']
                
                # Buscar produto no Bling
                response = make_bling_api_request('GET', f'/produtos/{bling_id}')
                
                if response.status_code != 200:
                    current_app.logger.error(f"Erro ao buscar produto {bling_id} no Bling: {response.status_code}")
                    results.append({
                        'produto_id': produto_id_local,
                        'success': False,
                        'error': f"Erro HTTP {response.status_code}"
                    })
                    continue
                
                bling_product = response.json().get('data', {})
                estoque_bling = bling_product.get('estoque', {}).get('atual', 0) if isinstance(bling_product.get('estoque'), dict) else 0
                
                # Atualizar estoque no banco local
                cur.execute("""
                    UPDATE produtos
                    SET estoque = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (estoque_bling, produto_id_local))
                
                conn.commit()
                
                log_sync('produto', produto_id_local, 'sync', {
                    'status': 'success',
                    'action': 'stock_update',
                    'estoque_novo': estoque_bling
                })
                
                results.append({
                    'produto_id': produto_id_local,
                    'success': True,
                    'estoque_novo': estoque_bling
                })
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                current_app.logger.error(f"Erro ao sincronizar estoque do produto {product_row['id']}: {e}")
                results.append({
                    'produto_id': product_row['id'],
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(products),
            'success': sum(1 for r in results if r.get('success')),
            'errors': sum(1 for r in results if not r.get('success')),
            'results': results
        }
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao sincronizar estoque: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'results': []
        }
    finally:
        cur.close()


def sync_stock_to_bling(produto_id: int = None) -> Dict:
    """
    Sincroniza estoque do banco local para o Bling
    
    Se produto_id for None, sincroniza todos os produtos sincronizados
    
    Args:
        produto_id: ID do produto local (None = todos)
    
    Returns:
        Dict com resultado da sincronização
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        if produto_id:
            cur.execute("""
                SELECT p.id, p.estoque, bp.bling_id
                FROM produtos p
                JOIN bling_produtos bp ON p.id = bp.produto_id
                WHERE p.id = %s AND bp.status_sincronizacao = 'sync'
            """, (produto_id,))
            products = cur.fetchall()
        else:
            cur.execute("""
                SELECT p.id, p.estoque, bp.bling_id
                FROM produtos p
                JOIN bling_produtos bp ON p.id = bp.produto_id
                WHERE bp.status_sincronizacao = 'sync'
            """)
            products = cur.fetchall()
        
        results = []
        
        for product_row in products:
            try:
                produto_id_local = product_row['id']
                estoque_local = product_row['estoque']
                bling_id = product_row['bling_id']
                
                # Buscar produto atual no Bling para manter outros campos
                response = make_bling_api_request('GET', f'/produtos/{bling_id}')
                
                if response.status_code != 200:
                    current_app.logger.error(f"Erro ao buscar produto {bling_id} no Bling: {response.status_code}")
                    results.append({
                        'produto_id': produto_id_local,
                        'success': False,
                        'error': f"Erro HTTP {response.status_code}"
                    })
                    continue
                
                bling_product = response.json().get('data', {})
                
                # Atualizar apenas o estoque
                update_data = {
                    'estoque': {
                        'minimo': bling_product.get('estoque', {}).get('minimo', 0) if isinstance(bling_product.get('estoque'), dict) else 0,
                        'maximo': bling_product.get('estoque', {}).get('maximo', 0) if isinstance(bling_product.get('estoque'), dict) else 0,
                        'atual': estoque_local
                    }
                }
                
                response = make_bling_api_request('PUT', f'/produtos/{bling_id}', json=update_data)
                
                if response.status_code not in [200, 201]:
                    current_app.logger.error(f"Erro ao atualizar estoque no Bling: {response.status_code} - {response.text}")
                    results.append({
                        'produto_id': produto_id_local,
                        'success': False,
                        'error': f"Erro HTTP {response.status_code}"
                    })
                    continue
                
                log_sync('produto', produto_id_local, 'sync', {
                    'status': 'success',
                    'action': 'stock_update_to_bling',
                    'estoque_enviado': estoque_local
                })
                
                results.append({
                    'produto_id': produto_id_local,
                    'success': True,
                    'estoque_enviado': estoque_local
                })
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                current_app.logger.error(f"Erro ao sincronizar estoque para Bling do produto {product_row['id']}: {e}")
                results.append({
                    'produto_id': product_row['id'],
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'total': len(products),
            'success': sum(1 for r in results if r.get('success')),
            'errors': sum(1 for r in results if not r.get('success')),
            'results': results
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar estoque para Bling: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'results': []
        }
    finally:
        cur.close()

