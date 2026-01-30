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
from .bling_api_service import make_bling_api_request, BlingAPIError


def get_product_for_bling_sync(produto_id: int) -> Optional[Dict]:
    """
    Busca produto completo do banco com todas as informações necessárias para Bling
    
    IMPORTANTE: Usa apenas preco_venda (NÃO preco_promocional) para o Bling
    Preço promocional é gerenciado localmente e não é enviado ao Bling
    
    Returns:
        Dict com dados do produto ou None se não encontrado
"""
    # #region agent log
    import os
    import json as json_module
    log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A,B,C,D,E",
                "location": "bling_product_service.py:get_product_for_bling_sync:entry",
                "message": "Function entry",
                "data": {"produto_id": produto_id},
                "timestamp": int(time.time() * 1000)
            }) + '\n')
    except Exception:
        pass
    # #endregion
    
    try:
        conn = get_db()
        # #region agent log
        import os
        import json
        log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "D",
                    "location": "bling_product_service.py:get_product_for_bling_sync:conn_ok",
                    "message": "Database connection obtained",
                    "data": {"conn_type": type(conn).__name__},
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        # Fazer rollback para garantir que a conexão está limpa
        try:
            conn.rollback()
        except Exception:
            pass
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar primeiro se produto existe na tabela produtos (hipótese C)
        # #region agent log
        try:
            # Não tentar acessar colunas que não existem diretamente em produtos
            cur.execute("SELECT id, codigo_sku, ncm FROM produtos WHERE id = %s", (produto_id,))
            produto_raw = cur.fetchone()
            import os
            import json as json_module
            log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    import json
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "C",
                        "location": "bling_product_service.py:get_product_for_bling_sync:check_exists",
                        "message": "Direct produto check",
                        "data": {
                            "produto_id": produto_id,
                            "found": produto_raw is not None,
                            "produto_data": dict(produto_raw) if produto_raw else None
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
        except Exception as check_err:
            import os
            import json as json_module
            log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json_module.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A,C",
                        "location": "bling_product_service.py:get_product_for_bling_sync:check_exists_error",
                        "message": "Error checking produto existence",
                        "data": {"produto_id": produto_id, "error": str(check_err), "error_type": type(check_err).__name__},
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
        # #endregion
        
        # Query base - campos que sempre existem
        # IMPORTANTE: peso_kg e dimensões estão na tabela produtos, não em nome_produto
        query_base = """
            SELECT 
                p.id,
                p.codigo_sku,
                p.ncm,
                p.cest,
                p.preco_venda,
                p.preco_promocional,
                p.custo,
                p.estoque,
                p.codigo_barras,
                p.peso_kg,
                p.dimensoes_largura,
                p.dimensoes_altura,
                p.dimensoes_comprimento,
                np.nome,
                np.descricao,
                np.descricao_curta,
                c.nome as categoria_nome,
                e.nome as estampa_nome,
                t.nome as tamanho_nome
            FROM produtos p
            JOIN produtos_nome_produto_lnk pnp ON p.id = pnp.produto_id
            JOIN nome_produto np ON pnp.nome_produto_id = np.id
            LEFT JOIN nome_produto_categoria_lnk npc ON np.id = npc.nome_produto_id
            LEFT JOIN categorias c ON npc.categoria_id = c.id
            LEFT JOIN produtos_estampa_lnk pe ON p.id = pe.produto_id
            LEFT JOIN estampa e ON pe.estampa_id = e.id
            LEFT JOIN produtos_tamanho_lnk pt ON p.id = pt.produto_id
            LEFT JOIN tamanho t ON pt.tamanho_id = t.id
            WHERE p.id = %s
        """
        
        # Verificar se coluna 'ativo' existe e adicionar se necessário
        # #region agent log
        ativo_column_exists = False
        ativo_check_error = None
        # #endregion
        
        # Fazer rollback antes de verificar coluna ativo
        try:
            conn.rollback()
        except Exception:
            pass
        
        try:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'produtos' AND column_name = 'ativo'
            """)
            ativo_column_exists = cur.fetchone() is not None
            # #region agent log
            import os
            import json as json_module
            log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    import json
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "E",
                        "location": "bling_product_service.py:get_product_for_bling_sync:ativo_check",
                        "message": "Ativo column check",
                        "data": {"exists": ativo_column_exists},
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            
            if ativo_column_exists:
                query_base_before = query_base
                query_base = query_base.replace(
                    'p.codigo_barras,',
                    'p.codigo_barras, p.ativo,'
                )
                # #region agent log
                import os
                import json as json_module
                log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
                try:
                    with open(log_path, 'a', encoding='utf-8') as f:
                        import json
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "E",
                            "location": "bling_product_service.py:get_product_for_bling_sync:ativo_added",
                            "message": "Ativo field added to query",
                            "data": {"query_changed": query_base != query_base_before},
                            "timestamp": int(time.time() * 1000)
                        }) + '\n')
                except Exception:
                    pass
                # #endregion
        except Exception as ativo_err:
            # #region agent log
            ativo_check_error = str(ativo_err)
            import os
            import json as json_module
            log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    import json
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A,E",
                        "location": "bling_product_service.py:get_product_for_bling_sync:ativo_check_error",
                        "message": "Error checking ativo column",
                        "data": {"error": str(ativo_err), "error_type": type(ativo_err).__name__},
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
        
        # #region agent log
        import os
        import json
        log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "location": "bling_product_service.py:get_product_for_bling_sync:before_execute",
                    "message": "About to execute main query",
                    "data": {"produto_id": produto_id, "query_length": len(query_base)},
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        # Fazer rollback antes de executar a query principal para garantir conexão limpa
        try:
            conn.rollback()
        except Exception:
            pass
        
        cur.execute(query_base, (produto_id,))
        
        # #region agent log
        import os
        import json
        log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                "hypothesisId": "A,B",
                "location": "bling_product_service.py:get_product_for_bling_sync:after_execute",
                "message": "Query executed successfully",
                "data": {"produto_id": produto_id},
                "timestamp": int(time.time() * 1000)
            }) + '\n')
        except Exception:
            pass
        # #endregion
        
        produto = cur.fetchone()
        
        # #region agent log
        import os
        import json
        log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                "hypothesisId": "B,C",
                "location": "bling_product_service.py:get_product_for_bling_sync:fetch_result",
                "message": "Fetch result",
                "data": {
                    "produto_id": produto_id,
                    "found": produto is not None,
                    "row_count": 1 if produto else 0
                },
                "timestamp": int(time.time() * 1000)
            }) + '\n')
        except Exception:
            pass
        # #endregion
        
        if not produto:
            current_app.logger.warning(f"Produto {produto_id} não encontrado na query SQL")
            # #region agent log
            import os
            import json as json_module
            log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    import json
                    f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B,C",
                    "location": "bling_product_service.py:get_product_for_bling_sync:not_found",
                    "message": "Produto not found in query result",
                    "data": {"produto_id": produto_id},
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
            except Exception:
                pass
            # #endregion
            return None
        
        produto_dict = dict(produto)
        current_app.logger.debug(f"Produto {produto_id} encontrado: SKU={produto_dict.get('codigo_sku')}, NCM={produto_dict.get('ncm')}, CEST={produto_dict.get('cest')}")
        
        # #region agent log
        import os
        import json
        log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                "hypothesisId": "B",
                "location": "bling_product_service.py:get_product_for_bling_sync:success",
                "message": "Produto found and converted to dict",
                "data": {
                    "produto_id": produto_id,
                    "sku": produto_dict.get('codigo_sku'),
                    "ncm": produto_dict.get('ncm'),
                    "nome": produto_dict.get('nome'),
                    "has_all_fields": all(k in produto_dict for k in ['id', 'codigo_sku', 'ncm', 'nome'])
                },
                "timestamp": int(time.time() * 1000)
            }) + '\n')
        except Exception:
            pass
        # #endregion
        
        return produto_dict
        
    except Exception as e:
        # #region agent log
        import os
        log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
        try:
            import json
            import traceback
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "bling_product_service.py:get_product_for_bling_sync:exception",
                "message": "Exception caught",
                "data": {
                    "produto_id": produto_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                },
                "timestamp": int(time.time() * 1000)
            }) + '\n')
        except Exception:
            pass
        # #endregion
        
        current_app.logger.error(f"Erro ao buscar produto {produto_id}: {e}", exc_info=True)
        if 'conn' in locals() and conn:
            try:
                conn.rollback()
            except:
                pass
        return None
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        # #region agent log
        import os
        log_path = r'c:\Users\joaobussi\Documents\lhama_banana\LhamaBanana_visual_estatica_corrigida\.cursor\debug.log'
        try:
            import json
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A,B,C,D,E",
                    "location": "bling_product_service.py:get_product_for_bling_sync:finally",
                "message": "Function exit (finally block)",
                "data": {"produto_id": produto_id},
                "timestamp": int(time.time() * 1000)
            }) + '\n')
        except Exception:
            pass
        # #endregion


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
    preco = produto.get('preco_venda')
    if not preco or float(preco) <= 0:
        errors.append("Preço de venda deve ser maior que zero")
    
    # Nome do produto obrigatório
    if not produto.get('nome'):
        errors.append("Nome do produto obrigatório")
    
    # CEST (opcional, mas se informado deve ter 7 dígitos)
    # CEST é obrigatório apenas para produtos sujeitos a ST
    cest = produto.get('cest')
    if cest and (len(str(cest)) != 7 or not str(cest).isdigit()):
        errors.append("CEST deve ter 7 dígitos (se informado)")
    
    return errors


def map_product_to_bling_format(produto: Dict) -> Dict:
    """
    Mapeia produto do formato LhamaBanana para formato Bling
    
    Envia apenas informações essenciais:
    - SKU (codigo)
    - Nome
    - Descrição básica (opcional)
    - Preço
    - Estoque
    - NCM (necessário para NF-e)
    
    Args:
        produto: Dict com dados do produto do banco
    
    Returns:
        Dict formatado para API do Bling (apenas campos essenciais)
    """
    # SEMPRE usar preço de venda normal (não promocional)
    # Promoções serão tratadas como desconto no item do pedido
    preco_final = float(produto.get('preco_venda', 0))
    
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
    
    # Produto básico com apenas campos essenciais
    bling_product = {
        "nome": nome_completo,
        "codigo": produto.get('codigo_sku'),  # SKU
        "preco": preco_final,  # Preço de venda
        "tipo": "P",  # P=Produto, S=Serviço, K=Kit
        "formato": "S",  # S=Simples, V=Variável, C=Composto
        "unidade": "UN",  # Unidade padrão
        "situacao": situacao,  # A=Ativo, I=Inativo (obrigatório)
    }
    
    # Tributação - NCM e CEST devem estar dentro do objeto tributacao
    tributacao = {
        "origem": 0,  # 0 = Nacional (padrão)
    }
    
    # NCM (obrigatório para NF-e) - sempre incluir se disponível
    ncm = produto.get('ncm')
    if ncm:
        # Garantir que NCM seja string e tenha 8 dígitos
        ncm_str = str(ncm).strip()
        if len(ncm_str) == 8 and ncm_str.isdigit():
            tributacao["ncm"] = ncm_str
            current_app.logger.info(f"[map_product_to_bling_format] NCM incluído para produto {produto.get('codigo_sku')}: {ncm_str}")
        else:
            current_app.logger.warning(f"[map_product_to_bling_format] NCM inválido para produto {produto.get('codigo_sku')}: '{ncm_str}' (deve ter 8 dígitos)")
    else:
        current_app.logger.warning(f"[map_product_to_bling_format] NCM não informado para produto {produto.get('codigo_sku')} (obrigatório para NF-e)")
    
    # CEST (opcional, mas importante para produtos sujeitos a ST)
    cest = produto.get('cest')
    if cest:
        # Garantir que CEST seja string e tenha 7 dígitos
        cest_str = str(cest).strip()
        if len(cest_str) == 7 and cest_str.isdigit():
            tributacao["cest"] = cest_str
            current_app.logger.info(f"[map_product_to_bling_format] CEST incluído para produto {produto.get('codigo_sku')}: {cest_str}")
        else:
            current_app.logger.warning(f"[map_product_to_bling_format] CEST inválido para produto {produto.get('codigo_sku')}: '{cest_str}' (deve ter 7 dígitos)")
    else:
        current_app.logger.debug(f"[map_product_to_bling_format] CEST não informado para produto {produto.get('codigo_sku')} (opcional)")
    
    # Incluir objeto tributacao no produto
    bling_product["tributacao"] = tributacao
    
    # Estoque (essencial)
    # Garantir que estoque seja um número válido (None vira 0, mas 0 real permanece 0)
    estoque_atual_raw = produto.get('estoque')
    estoque_atual = int(estoque_atual_raw) if estoque_atual_raw is not None else 0
    
    current_app.logger.debug(f"[map_product_to_bling_format] Estoque: atual={estoque_atual} (raw: {estoque_atual_raw})")
    
    # IMPORTANTE: Bling usa 'saldoVirtualTotal' para estoque atual, não 'atual'
    bling_product["estoque"] = {
        "minimo": 0,  # Não configurado (removido do sistema)
        "maximo": 0,  # Não configurado
        "saldoVirtualTotal": estoque_atual  # Usar saldoVirtualTotal em vez de atual
    }
    
    # Peso e dimensões (para cálculo de frete e fiscal)
    peso_kg = float(produto.get('peso_kg') or 0)
    if peso_kg > 0:
        bling_product["pesoLiq"] = peso_kg
        bling_product["pesoBruto"] = peso_kg * 1.1  # Peso bruto = líquido + 10% (embalagem)
        current_app.logger.debug(f"[map_product_to_bling_format] Peso: {peso_kg} kg")
    
    # Dimensões (largura, altura, comprimento/profundidade)
    # IMPORTANTE: Incluir dimensões mesmo que não estejam todas preenchidas
    dimensoes_largura = float(produto.get('dimensoes_largura') or 0)
    dimensoes_altura = float(produto.get('dimensoes_altura') or 0)
    dimensoes_comprimento = float(produto.get('dimensoes_comprimento') or 0)
    
    # Bling aceita dimensões tanto no nível raiz quanto em objeto "dimensoes"
    # Vamos incluir em ambos os formatos para garantir compatibilidade
    dimensoes_dict = {}
    
    if dimensoes_largura > 0:
        bling_product["largura"] = dimensoes_largura
        dimensoes_dict["largura"] = dimensoes_largura
        current_app.logger.debug(f"[map_product_to_bling_format] Largura: {dimensoes_largura} cm")
    
    if dimensoes_altura > 0:
        bling_product["altura"] = dimensoes_altura
        dimensoes_dict["altura"] = dimensoes_altura
        current_app.logger.debug(f"[map_product_to_bling_format] Altura: {dimensoes_altura} cm")
    
    if dimensoes_comprimento > 0:
        # Bling usa "profundidade" para comprimento (confirmado na resposta da API)
        bling_product["profundidade"] = dimensoes_comprimento
        dimensoes_dict["profundidade"] = dimensoes_comprimento
        current_app.logger.debug(f"[map_product_to_bling_format] Comprimento (profundidade): {dimensoes_comprimento} cm")
    
    # Incluir também em objeto "dimensoes" (formato que o Bling retorna)
    if dimensoes_dict:
        bling_product["dimensoes"] = dimensoes_dict
        current_app.logger.debug(f"[map_product_to_bling_format] Dimensões em objeto: {dimensoes_dict}")
    
    # Log informativo se todas as dimensões estiverem preenchidas
    if dimensoes_largura > 0 and dimensoes_altura > 0 and dimensoes_comprimento > 0:
        current_app.logger.info(
            f"[map_product_to_bling_format] Dimensões completas: "
            f"L={dimensoes_largura}cm x A={dimensoes_altura}cm x C={dimensoes_comprimento}cm"
        )
    
    # CEST já foi adicionado acima no bling_product, não precisa adicionar novamente
    
    # Descrição básica (opcional, apenas se disponível)
    if produto.get('descricao_curta'):
        bling_product["descricaoCurta"] = produto['descricao_curta']
    
    # NOTA IMPORTANTE:
    # CFOP (Código Fiscal de Operações e Prestações) NÃO é campo do produto,
    # mas sim do pedido/nota fiscal, pois depende da natureza da transação:
    # - Dentro do mesmo estado: CFOP 5102
    # - Interestadual: CFOP 6108
    # O CFOP será tratado na criação do pedido e emissão de NF-e
    
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
    try:
        current_app.logger.info(f"[sync_product_to_bling] Iniciando sincronização do produto {produto_id}")
        
        # 1. Buscar produto do banco
        produto = get_product_for_bling_sync(produto_id)
        
        if not produto:
            error_msg = f'Produto {produto_id} não encontrado'
            current_app.logger.error(f"[sync_product_to_bling] {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
        
        current_app.logger.info(f"[sync_product_to_bling] Produto encontrado: SKU={produto.get('codigo_sku')}, NCM={produto.get('ncm')}, CEST={produto.get('cest')}, Nome={produto.get('nome')}")
        
        # 2. Validar produto
        validation_errors = validate_product_for_bling(produto)
        if validation_errors:
            error_msg = 'Validação falhou'
            current_app.logger.error(f"[sync_product_to_bling] {error_msg}: {validation_errors}")
            log_sync('produto', produto_id, 'error', {
                'error': error_msg,
                'errors': validation_errors
            })
            return {
                'success': False,
                'error': error_msg,
                'details': validation_errors
            }
        
        current_app.logger.info(f"[sync_product_to_bling] Validação OK, prosseguindo com sincronização")
        
        # 3. Verificar se já está sincronizado
        bling_produto = get_bling_product_by_local_id(produto_id)
        current_app.logger.info(f"[sync_product_to_bling] Produto já sincronizado: {bling_produto is not None}")
        
        # 4. Preparar dados para Bling
        current_app.logger.info(f"[sync_product_to_bling] Preparando dados para Bling...")
        bling_product_data = map_product_to_bling_format(produto)
        current_app.logger.debug(f"[sync_product_to_bling] Dados preparados: {json.dumps(bling_product_data, ensure_ascii=False, indent=2)}")
        
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
                
                # Log da resposta do Bling para debug do estoque
                estoque_enviado = bling_product_data.get('estoque', {}).get('atual', 'N/A')
                estoque_bling_response = bling_product_response.get('estoque', {})
                
                # A resposta do Bling pode ter estoque em diferentes formatos
                if isinstance(estoque_bling_response, dict):
                    estoque_atual_bling = estoque_bling_response.get('atual', estoque_bling_response.get('quantidade', 'N/A'))
                elif isinstance(estoque_bling_response, (int, float)):
                    estoque_atual_bling = estoque_bling_response
                else:
                    estoque_atual_bling = 'N/A'
                
                current_app.logger.info(
                    f"[sync_product_to_bling] Estoque - Enviado: {estoque_enviado}, "
                    f"Retornado pelo Bling: {estoque_atual_bling} (formato: {type(estoque_bling_response).__name__})"
                )
                
                # Log completo da resposta para debug (especialmente o estoque)
                estoque_info = json.dumps(bling_product_response.get('estoque', {}), ensure_ascii=False) if bling_product_response.get('estoque') else 'Não encontrado'
                current_app.logger.info(
                    f"[sync_product_to_bling] Estoque na resposta Bling (raw): {estoque_info}"
                )
                current_app.logger.debug(
                    f"[sync_product_to_bling] Resposta completa do Bling: {json.dumps(bling_product_response, ensure_ascii=False, indent=2)[:1000]}"
                )
                
                # 7. Salvar referência no banco
                save_bling_product_reference(
                    produto_id=produto_id,
                    bling_id=bling_id,
                    bling_codigo=produto.get('codigo_sku'),
                    status='sync'
                )
                
                # 7.5. Atualizar estoque separadamente após criar/atualizar produto
                # O Bling pode não atualizar o estoque corretamente no PUT/POST inicial
                # Então fazemos uma atualização específica de estoque
                try:
                    stock_sync_result = sync_stock_to_bling(produto_id)
                    if stock_sync_result.get('success'):
                        current_app.logger.info(
                            f"[sync_product_to_bling] Estoque atualizado separadamente após {action}: "
                            f"estoque={produto.get('estoque', 0)}"
                        )
                    else:
                        current_app.logger.warning(
                            f"[sync_product_to_bling] Falha ao atualizar estoque separadamente: "
                            f"{stock_sync_result.get('error', 'Erro desconhecido')}"
                        )
                except Exception as stock_err:
                    current_app.logger.warning(
                        f"[sync_product_to_bling] Erro ao atualizar estoque separadamente: {stock_err}",
                        exc_info=True
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
                
        except BlingAPIError as e:
            # Erro específico da API do Bling
            error_msg = e.message
            current_app.logger.error(f"[sync_product_to_bling] Erro BlingAPI: {error_msg}", exc_info=True)
            
            log_sync('produto', produto_id, 'sync', {
                'status': 'error',
                'error': error_msg,
                'bling_error_type': str(e.error_type)
            })
            
            if 'bling_produto' in locals() and bling_produto:
                update_bling_product_status(produto_id, 'error', error_msg)
            
            return {
                'success': False,
                'error': 'Erro ao sincronizar com Bling',
                'details': error_msg,
                'bling_error_type': str(e.error_type)
            }
            
        except Exception as e:
            # Outras exceções no bloco interno
            error_msg = str(e)
            current_app.logger.error(f"[sync_product_to_bling] Exceção ao chamar API Bling: {error_msg}", exc_info=True)
            
            log_sync('produto', produto_id, 'sync', {
                'status': 'error',
                'error': error_msg,
                'exception_type': type(e).__name__
            })
            
            if 'bling_produto' in locals() and bling_produto:
                update_bling_product_status(produto_id, 'error', error_msg)
            
            return {
                'success': False,
                'error': 'Erro ao sincronizar produto',
                'details': error_msg,
                'exception_type': type(e).__name__
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
# SINCRONIZAÇÃO DE CATEGORIAS DO BLING
# =====================================================

def fetch_categories_from_bling() -> Dict:
    """
    Busca categorias de produtos do Bling
    
    Nota: O Bling retorna categorias de produtos no próprio produto (campo categoria).
    Não há endpoint específico para listar categorias de produtos, apenas para categorias de receitas.
    
    Returns:
        Dict com lista de categorias extraídas dos produtos
    """
    try:
        # Buscar alguns produtos para extrair categorias únicas
        response = make_bling_api_request('GET', '/produtos', params={'limite': 100})
        
        if response.status_code != 200:
            current_app.logger.warning(
                f"Não foi possível buscar produtos do Bling para extrair categorias: {response.status_code}"
            )
            return {
                'success': False,
                'error': f"Erro HTTP {response.status_code}",
                'categories': []
            }
        
        data = response.json()
        products = data.get('data', [])
        
        # Extrair categorias únicas dos produtos
        categorias_unicas = {}
        for product in products:
            categoria_data = extract_category_from_bling_product(product)
            if categoria_data:
                nome_categoria = categoria_data.get('nome') or categoria_data.get('descricao')
                if nome_categoria:
                    categorias_unicas[nome_categoria] = categoria_data
        
        categories = list(categorias_unicas.values())
        
        return {
            'success': True,
            'categories': categories,
            'total': len(categories)
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar categorias do Bling: {e}")
        return {
            'success': False,
            'error': str(e),
            'categories': []
        }


def sync_categories_from_bling() -> Dict:
    """
    Sincroniza categorias do Bling para o banco local
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        # Buscar categorias do Bling
        result = fetch_categories_from_bling()
        
        if not result.get('success'):
            return result
        
        categories = result.get('categories', [])
        results = []
        
        for bling_category in categories:
            try:
                categoria_id = get_or_create_local_category_from_bling(bling_category)
                
                if categoria_id:
                    results.append({
                        'success': True,
                        'bling_category': bling_category.get('nome') or bling_category.get('descricao'),
                        'local_categoria_id': categoria_id
                    })
                else:
                    results.append({
                        'success': False,
                        'bling_category': bling_category.get('nome') or bling_category.get('descricao'),
                        'error': 'Não foi possível criar categoria local'
                    })
                
                # Rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                current_app.logger.error(f"Erro ao sincronizar categoria do Bling: {e}")
                results.append({
                    'success': False,
                    'bling_category': bling_category.get('nome') or bling_category.get('descricao'),
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r.get('success'))
        
        return {
            'success': True,
            'total': len(categories),
            'success_count': success_count,
            'results': results
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao sincronizar categorias do Bling: {e}")
        return {
            'success': False,
            'error': str(e),
            'results': []
        }


# =====================================================
# ⚠️ FUNÇÕES DESABILITADAS - SINCRONIZAÇÃO REVERSA
# =====================================================
# Estas funções foram desabilitadas conforme a nova arquitetura:
# - Strapi é a fonte da verdade do catálogo
# - Produtos são criados APENAS localmente
# - Bling apenas recebe produtos já criados
# - Não sincronizamos categorias/valores do Bling
# =====================================================

def clear_local_categories_and_values():
    """
    ⚠️ DESABILITADA - Não usar na nova arquitetura
    
    Remove todas as categorias, tecidos, estampas e tamanhos do banco local
    Também remove produtos e suas dependências (carrinhos, itens_venda, etc)
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Ordem: remover dependentes primeiro, depois principais
        # Seguindo a cadeia de dependências de chaves estrangeiras
        
        # 1. Limpar dependências de produtos (com tratamento de erros se tabela não existir)
        tabelas_dependentes = [
            ('carrinho_itens', 'Itens de carrinho'),
            ('carrinhos', 'Carrinhos'),
            ('itens_venda', 'Itens de venda'),
            ('imagens_produto', 'Imagens de produto')
        ]
        
        for tabela, descricao in tabelas_dependentes:
            try:
                cur.execute(f"DELETE FROM {tabela}")
                current_app.logger.info(f"{descricao} removidos: {cur.rowcount}")
            except Exception as e:
                # Tabela pode não existir, apenas logar e continuar
                current_app.logger.debug(f"Tabela {tabela} não encontrada ou erro: {e}")
                pass
        
        # 4. Limpar produtos (dependem de nome_produto, estampa, tamanho)
        cur.execute("DELETE FROM produtos")
        current_app.logger.info(f"Produtos removidos: {cur.rowcount}")
        
        # 5. Limpar nome_produto (depende de categoria)
        cur.execute("DELETE FROM nome_produto")
        current_app.logger.info(f"Nome produtos removidos: {cur.rowcount}")
        
        # 6. Limpar estampas (depende de categoria e tecido)
        cur.execute("DELETE FROM estampa")
        current_app.logger.info(f"Estampas removidas: {cur.rowcount}")
        
        # 7. Limpar tamanhos (não tem dependências)
        cur.execute("DELETE FROM tamanho")
        current_app.logger.info(f"Tamanhos removidos: {cur.rowcount}")
        
        # 8. Limpar tecidos (não tem dependências relevantes)
        cur.execute("DELETE FROM tecidos")
        current_app.logger.info(f"Tecidos removidos: {cur.rowcount}")
        
        # 9. Limpar categorias (por último, pois outros dependem dela)
        cur.execute("DELETE FROM categorias")
        current_app.logger.info(f"Categorias removidas: {cur.rowcount}")
        
        conn.commit()
        
        return {
            'success': True,
            'message': 'Categorias e valores removidos com sucesso'
        }
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao limpar categorias e valores: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        cur.close()


def extract_unique_values_from_bling_products(limit: int = 500) -> Dict:
    """
    ⚠️ DESABILITADA - Não usar na nova arquitetura
    
    Busca produtos do Bling e extrai valores únicos de campos customizados
    Retorna todas as categorias, tecidos, estampas e tamanhos encontrados
    
    Busca detalhes individuais de cada produto para garantir que campos customizados sejam encontrados
    
    Args:
        limit: Quantidade máxima de produtos para buscar (para extrair valores únicos)
    
    Returns:
        Dict com valores únicos:
        {
            'categorias': ['Camisetas', 'Regatas', ...],
            'tecidos': ['Algodão', 'UltraSoft', ...],
            'estampas': ['Lhama Feliz', 'Dinossauro', ...],
            'tamanhos': ['P', 'M', 'G', ...]
        }
    """
    valores_unicos = {
        'categorias': set(),
        'tecidos': set(),
        'estampas': set(),
        'tamanhos': set()
    }
    
    try:
        # Primeiro, buscar lista de produtos
        result_list = fetch_products_from_bling(limit=limit, include_details=False)
        
        if not result_list.get('success'):
            return {
                'success': False,
                'error': result_list.get('error', 'Erro ao buscar produtos'),
                'valores': {
                    'categorias': [],
                    'tecidos': [],
                    'estampas': [],
                    'tamanhos': []
                }
            }
        
        products_list = result_list.get('products', [])
        current_app.logger.info(f"Processando {len(products_list)} produtos para extrair valores únicos (buscando detalhes individuais)...")
        
        # Para cada produto, buscar detalhes individuais (onde campos customizados podem estar)
        for idx, product in enumerate(products_list):
            product_id = product.get('id')
            
            if not product_id:
                continue
            
            try:
                # Buscar detalhes individuais do produto (pode incluir campos customizados)
                detailed_product = fetch_product_detail_from_bling(product_id)
                
                if detailed_product:
                    # Mesclar dados detalhados com dados da listagem
                    detailed_product.update(product)
                    product = detailed_product
                
                # 1. Extrair campos customizados (com busca detalhada)
                campos_customizados = extract_custom_fields_from_bling_product(product)
                
                # Categorias
                if campos_customizados.get('categoria'):
                    valores_unicos['categorias'].add(campos_customizados['categoria'])
                
                # Tecidos
                if campos_customizados.get('tecido'):
                    valores_unicos['tecidos'].add(campos_customizados['tecido'])
                
                # Estampas
                if campos_customizados.get('estampa'):
                    valores_unicos['estampas'].add(campos_customizados['estampa'])
                
                # Tamanhos
                if campos_customizados.get('tamanho'):
                    valores_unicos['tamanhos'].add(campos_customizados['tamanho'])
                
                # 2. Fallback: extrair do campo categoria tradicional
                categoria_tradicional = extract_category_from_bling_product(product)
                if categoria_tradicional:
                    nome_categoria = categoria_tradicional.get('nome') or categoria_tradicional.get('descricao')
                    if nome_categoria and nome_categoria.lower() not in ['true', 'false', '']:
                        valores_unicos['categorias'].add(nome_categoria)
                
                # 3. Fallback: extrair do nome do produto (SEMPRE fazer isso)
                nome_produto = product.get('nome', '')
                if nome_produto:
                    # Extrair categoria do nome (primeira parte antes de " - ")
                    if ' - ' in nome_produto:
                        partes = nome_produto.split(' - ')
                        primeira_parte = partes[0].strip()
                        if primeira_parte and len(primeira_parte) > 2:
                            # Pode ser categoria
                            valores_unicos['categorias'].add(primeira_parte)
                    
                    atributos = extract_attributes_from_product_name(nome_produto)
                    
                    if atributos.get('estampa'):
                        valores_unicos['estampas'].add(atributos['estampa'])
                    
                    if atributos.get('tamanho'):
                        # Limpar "Tamanho " se presente
                        tamanho_limpo = atributos['tamanho'].replace('Tamanho ', '').strip()
                        if tamanho_limpo:
                            valores_unicos['tamanhos'].add(tamanho_limpo)
                    
                    # Extrair nome base (pode ser categoria)
                    nome_base = atributos.get('nome_base', '')
                    if nome_base and ' - ' not in nome_base and len(nome_base) > 2:
                        valores_unicos['categorias'].add(nome_base)
                
                # Rate limiting entre requisições individuais
                if idx < len(products_list) - 1:
                    time.sleep(0.3)
                
            except Exception as e:
                current_app.logger.warning(f"Erro ao processar produto {product_id}: {e}")
                continue
        
        # Converter sets para listas ordenadas
        valores_finais = {
            'categorias': sorted(list(valores_unicos['categorias'])),
            'tecidos': sorted(list(valores_unicos['tecidos'])),
            'estampas': sorted(list(valores_unicos['estampas'])),
            'tamanhos': sorted(list(valores_unicos['tamanhos']))
        }
        
        current_app.logger.info(f"Valores extraídos: {len(valores_finais['categorias'])} categorias, "
                              f"{len(valores_finais['tecidos'])} tecidos, "
                              f"{len(valores_finais['estampas'])} estampas, "
                              f"{len(valores_finais['tamanhos'])} tamanhos")
        
        return {
            'success': True,
            'valores': valores_finais,
            'total_produtos_processados': len(products_list)
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro ao extrair valores únicos: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'valores': {
                'categorias': [],
                'tecidos': [],
                'estampas': [],
                'tamanhos': []
            }
        }


def sync_categories_and_values_from_bling(limit_products: int = 500, clear_first: bool = True) -> Dict:
    """
    ⚠️ DESABILITADA - Não usar na nova arquitetura
    
    Sincroniza categorias e valores únicos do Bling para o banco local
    
    Processo:
    1. Limpa categorias, tecidos, estampas e tamanhos existentes (se clear_first=True)
    2. Busca produtos do Bling
    3. Extrai valores únicos de campos customizados
    4. Cria categorias, tecidos, estampas e tamanhos no banco
    5. Sincroniza produtos novamente
    
    Args:
        limit_products: Quantidade máxima de produtos para buscar
        clear_first: Se True, limpa dados existentes antes de sincronizar
    
    Returns:
        Dict com resultado da sincronização
    """
    try:
        resultados = {
            'limpeza': None,
            'valores_extraidos': None,
            'categorias_criadas': 0,
            'tecidos_criados': 0,
            'estampas_criadas': 0,
            'tamanhos_criados': 0,
            'produtos_sincronizados': 0
        }
        
        # 1. Limpar dados existentes (se solicitado)
        if clear_first:
            current_app.logger.info("Limpando categorias e valores existentes...")
            limpeza = clear_local_categories_and_values()
            resultados['limpeza'] = limpeza
            
            if not limpeza.get('success'):
                return {
                    'success': False,
                    'error': f"Erro ao limpar dados: {limpeza.get('error')}",
                    **resultados
                }
        
        # 2. Extrair valores únicos do Bling
        current_app.logger.info("Extraindo valores únicos dos produtos do Bling...")
        valores = extract_unique_values_from_bling_products(limit=limit_products)
        resultados['valores_extraidos'] = valores
        
        if not valores.get('success'):
            return {
                'success': False,
                'error': f"Erro ao extrair valores: {valores.get('error')}",
                **resultados
            }
        
        valores_dict = valores.get('valores', {})
        
        # 3. Criar categorias
        current_app.logger.info(f"Criando {len(valores_dict.get('categorias', []))} categorias...")
        categoria_ids = {}
        for categoria_nome in valores_dict.get('categorias', []):
            if categoria_nome:
                categoria_id = get_or_create_local_category_from_bling({'nome': categoria_nome})
                if categoria_id:
                    categoria_ids[categoria_nome] = categoria_id
                    resultados['categorias_criadas'] += 1
        
        # 4. Criar tecidos
        current_app.logger.info(f"Criando {len(valores_dict.get('tecidos', []))} tecidos...")
        for tecido_nome in valores_dict.get('tecidos', []):
            if tecido_nome:
                tecido_id = get_or_create_local_tecido(tecido_nome)
                if tecido_id:
                    resultados['tecidos_criados'] += 1
        
        
        # 6. Garantir categoria padrão
        if not categoria_ids:
            # Criar categoria padrão se não houver nenhuma
            categoria_padrao_id = get_or_create_local_category_from_bling({'nome': 'Geral'})
            if categoria_padrao_id:
                categoria_ids['Geral'] = categoria_padrao_id
                resultados['categorias_criadas'] += 1
        
        categoria_padrao_id = list(categoria_ids.values())[0] if categoria_ids else None
        
        # 7. Criar estampas (precisa de categoria)
        estampas_lista = valores_dict.get('estampas', [])
        if not estampas_lista:
            estampas_lista = ['Sem Estampa']
            current_app.logger.info("Nenhuma estampa encontrada, criando estampa padrão 'Sem Estampa'")
        
        current_app.logger.info(f"Criando {len(estampas_lista)} estampas...")
        for estampa_nome in estampas_lista:
            if estampa_nome and categoria_padrao_id:
                estampa_id = get_or_create_local_estampa(estampa_nome, categoria_padrao_id)
                if estampa_id:
                    resultados['estampas_criadas'] += 1
        
        # 8. Sincronizar produtos
        current_app.logger.info("Sincronizando produtos do Bling...")
        produtos_result = sync_products_from_bling(limit=limit_products, include_details=True)
        if produtos_result.get('success'):
            resultados['produtos_sincronizados'] = produtos_result.get('success_count', 0)
        
        return {
            'success': True,
            'message': 'Sincronização completa concluída',
            **resultados,
            'resumo': {
                'categorias': resultados['categorias_criadas'],
                'tecidos': resultados['tecidos_criados'],
                'estampas': resultados['estampas_criadas'],
                'tamanhos': resultados['tamanhos_criados'],
                'produtos': resultados['produtos_sincronizados']
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"Erro na sincronização completa: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            **resultados
        }


# =====================================================
# SINCRONIZAÇÃO BIDIRECIONAL: BLING → BANCO LOCAL
# =====================================================

def fetch_product_detail_from_bling(bling_product_id: int) -> Optional[Dict]:
    """
    Busca detalhes completos de um produto específico do Bling
    (pode incluir campos customizados que não vêm na listagem)
    
    Args:
        bling_product_id: ID do produto no Bling
    
    Returns:
        Dict com dados completos do produto ou None
    """
    try:
        response = make_bling_api_request(
            'GET',
            f'/produtos/{bling_product_id}'
        )
        
        if response.status_code != 200:
            current_app.logger.warning(f"Erro ao buscar detalhes do produto {bling_product_id}: {response.status_code}")
            return None
        
        data = response.json()
        # O Bling pode retornar em diferentes formatos
        if 'data' in data:
            return data['data'][0] if isinstance(data['data'], list) and len(data['data']) > 0 else data['data']
        return data
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar detalhes do produto {bling_product_id}: {e}")
        return None


def fetch_products_from_bling(limit: int = 100, offset: int = 0, include_details: bool = False) -> Dict:
    """
    Busca produtos do Bling (apenas para sincronização de estoque/preço)
    
    ⚠️ NÃO cria produtos no banco local - produtos devem ser criados localmente primeiro
    
    Args:
        limit: Quantidade de produtos por página
        offset: Offset para paginação
        include_details: Se True, busca detalhes completos de cada produto (para estoque/preço)
    
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
        
        # Se solicitado, buscar detalhes completos de cada produto (para obter campos customizados)
        if include_details and products:
            products_with_details = []
            for product in products:
                product_id = product.get('id')
                if product_id:
                    detailed_product = fetch_product_detail_from_bling(product_id)
                    if detailed_product:
                        # Mesclar dados detalhados com dados da listagem
                        detailed_product.update(product)
                        products_with_details.append(detailed_product)
                    else:
                        products_with_details.append(product)
                else:
                    products_with_details.append(product)
            products = products_with_details
        
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


def get_or_create_local_category_from_bling(bling_categoria: Dict) -> Optional[int]:
    """
    ⚠️ DESABILITADA - Não usar na nova arquitetura
    
    Categorias devem ser criadas APENAS localmente (Strapi/admin)
    Não criar categorias baseadas no Bling
    
    Busca ou cria categoria local baseada na categoria do Bling
    
    Args:
        bling_categoria: Dict com dados da categoria do Bling (pode ter id, descricao, nome)
                      Ou pode ser uma string com o nome da categoria
    
    Returns:
        ID da categoria local ou None se erro
    """
    if not bling_categoria:
        return None
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Se for string, converter para dict
        if isinstance(bling_categoria, str):
            bling_categoria = {'nome': bling_categoria}
        
        # Extrair nome da categoria
        categoria_nome = bling_categoria.get('nome') or bling_categoria.get('descricao') or ''
        
        # Se ainda não tem nome, tentar outros campos
        if not categoria_nome:
            # Pode ser que venha em outros formatos
            for key in ['id', 'valor', 'label', 'text']:
                if key in bling_categoria and bling_categoria[key]:
                    categoria_nome = str(bling_categoria[key])
                    break
        
        if not categoria_nome:
            return None
        
        # Limpar e normalizar nome
        categoria_nome = str(categoria_nome).strip()
        
        # Ignorar valores booleanos ou vazios
        if categoria_nome.lower() in ['true', 'false', '']:
            return None
        
        # Verificar se categoria já existe
        cur.execute("""
            SELECT id FROM categorias WHERE nome = %s LIMIT 1
        """, (categoria_nome,))
        existing = cur.fetchone()
        
        if existing:
            return existing['id']
        
        # Criar nova categoria
        cur.execute("""
            INSERT INTO categorias (nome, ativo, ordem_exibicao)
            VALUES (%s, TRUE, 0)
            RETURNING id
        """, (categoria_nome,))
        
        categoria_id = cur.fetchone()['id']
        conn.commit()
        
        current_app.logger.info(f"Categoria '{categoria_nome}' criada localmente (ID: {categoria_id})")
        return categoria_id
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar categoria local: {e}", exc_info=True)
        return None
    finally:
        cur.close()


def extract_custom_fields_from_bling_product(bling_product: Dict) -> Dict:
    """
    Extrai campos customizados do produto do Bling
    
    Campos customizados no Bling vêm em diferentes formatos:
    - camposCustomizados (array de objetos)
    - campos_customizados (alternativo)
    - Cada campo tem: id, nome, valor, tipo
    
    Args:
        bling_product: Dict com dados do produto do Bling
    
    Returns:
        Dict com campos customizados mapeados por nome:
        {
            'categoria': 'Camisetas',
            'tecido': 'Algodão',
            'estampa': 'Lhama Feliz',
            'tamanho': 'M',
            'sexo': 'U'
        }
    """
    campos = {}
    
    # Buscar campos customizados em diferentes formatos possíveis
    # O Bling pode retornar em diferentes estruturas
    campos_customizados = (
        bling_product.get('camposCustomizados') or
        bling_product.get('campos_customizados') or
        bling_product.get('customFields') or
        bling_product.get('camposCustomizadosProdutos') or
        bling_product.get('campos') or
        []
    )
    
    # Se não encontrou como lista, pode estar dentro de uma estrutura aninhada
    if not campos_customizados or (not isinstance(campos_customizados, list) and not isinstance(campos_customizados, dict)):
        # Tentar buscar em estruturas aninhadas comuns
        if 'camposCustomizados' in str(bling_product):
            # Procurar recursivamente
            for key, value in bling_product.items():
                if 'campo' in key.lower() and isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        campos_customizados = value
                        break
                    elif isinstance(value, dict):
                        # Pode ser um dict com listas dentro
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, list):
                                campos_customizados = sub_value
                                break
    
    if not isinstance(campos_customizados, list):
        # Se não é lista, não há campos customizados estruturados
        return campos
    
    # Mapear campos customizados por nome (case-insensitive)
    nomes_normalizados = {
        'categoria': ['categoria', 'categorias', 'tipo', 'tipoproduto'],
        'tecido': ['tecido', 'tecidos', 'material', 'materiaprima'],
        'estampa': ['estampa', 'estampas', 'design', 'imagem'],
        'tamanho': ['tamanho', 'tamanhos', 'size'],
        'sexo': ['sexo', 'genero', 'gender']
    }
    
    for campo in campos_customizados:
        if isinstance(campo, dict):
            nome_campo = campo.get('nome') or campo.get('name') or ''
            valor_campo = campo.get('valor') or campo.get('value') or ''
            id_campo = campo.get('id')
            
            if not nome_campo or not valor_campo:
                continue
            
            nome_campo_lower = nome_campo.lower().strip()
            
            # Tentar mapear para campos conhecidos
            for campo_local, variacoes in nomes_normalizados.items():
                if nome_campo_lower in variacoes or nome_campo_lower == campo_local:
                    # Normalizar valor
                    valor_str = str(valor_campo).strip()
                    
                    # Se o campo customizado tem opções, pode vir como objeto
                    if isinstance(valor_campo, dict):
                        valor_str = valor_campo.get('valor') or valor_campo.get('nome') or valor_campo.get('descricao') or ''
                        valor_str = str(valor_str).strip()
                    
                    if valor_str and valor_str.lower() not in ['null', 'none', '']:
                        campos[campo_local] = valor_str
                    break
    
    return campos


def get_or_create_local_tecido(nome_tecido: str) -> Optional[int]:
    """
    Busca ou cria tecido local
    
    Args:
        nome_tecido: Nome do tecido
    
    Returns:
        ID do tecido local ou None
    """
    if not nome_tecido:
        return None
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Verificar se tecido existe
        cur.execute("""
            SELECT id FROM tecidos WHERE nome = %s LIMIT 1
        """, (nome_tecido,))
        existing = cur.fetchone()
        
        if existing:
            return existing['id']
        
        # Criar tecido
        cur.execute("""
            INSERT INTO tecidos (nome, ativo)
            VALUES (%s, TRUE)
            RETURNING id
        """, (nome_tecido,))
        
        tecido_id = cur.fetchone()['id']
        conn.commit()
        
        current_app.logger.info(f"Tecido '{nome_tecido}' criado localmente (ID: {tecido_id})")
        return tecido_id
        
    except Exception as e:
        conn.rollback()
        # Se a tabela tecidos não existir, retornar None silenciosamente
        error_str = str(e).lower()
        if 'does not exist' in error_str or 'relation "tecidos" does not exist' in error_str:
            current_app.logger.warning(f"Tabela tecidos não encontrada. Tecido será ignorado.")
        else:
            current_app.logger.error(f"Erro ao criar tecido local: {e}")
        return None
    finally:
        cur.close()


def extract_category_from_bling_product(bling_product: Dict) -> Optional[Dict]:
    """
    Extrai informação de categoria do produto do Bling
    
    O Bling pode retornar categoria em diferentes formatos:
    - categoria.id / categoria.descricao (objeto categoria)
    - categoria (string)
    
    Args:
        bling_product: Dict com dados do produto do Bling
    
    Returns:
        Dict com dados da categoria ou None
    """
    # Tentar campo categoria (pode ser objeto ou string)
    categoria_data = bling_product.get('categoria')
    
    if isinstance(categoria_data, dict):
        # Categoria é um objeto: {id: X, descricao: "Nome"}
        return categoria_data
    elif isinstance(categoria_data, str):
        # Categoria é uma string
        return {'nome': categoria_data}
    elif categoria_data:
        # Outro formato
        return {'nome': str(categoria_data)}
    
    # Se não tem categoria explícita, tentar extrair do nome
    # (seguindo padrão: "Categoria - Nome - Estampa - Tamanho")
    nome = bling_product.get('nome', '')
    if ' - ' in nome:
        partes = nome.split(' - ')
        # Primeira parte pode ser categoria
        primeira_parte = partes[0].strip()
        return {'nome': primeira_parte}
    
    return None


def extract_attributes_from_product_name(nome: str) -> Dict:
    """
    Extrai atributos do nome do produto (estampa, tamanho, etc)
    
    Padrão esperado: "Nome - Estampa - Tamanho" ou "Categoria - Nome - Estampa - Tamanho"
    
    Returns:
        Dict com estampa, tamanho extraídos
    """
    resultado = {
        'estampa': None,
        'tamanho': None,
        'nome_base': nome
    }
    
    if ' - ' in nome:
        partes = [p.strip() for p in nome.split(' - ')]
        
        # Se tem 2 partes: "Nome - Tamanho" ou "Nome - Estampa"
        # Se tem 3+ partes: "Nome - Estampa - Tamanho" ou "Categoria - Nome - Estampa - Tamanho"
        if len(partes) >= 2:
            # Última parte é geralmente tamanho
            ultima_parte = partes[-1]
            # Verificar se parece com tamanho (curto, pode ter números)
            if len(ultima_parte) <= 5 or any(char.isdigit() for char in ultima_parte):
                resultado['tamanho'] = ultima_parte.replace('Tamanho ', '')
                resultado['estampa'] = partes[-2] if len(partes) >= 3 else None
                resultado['nome_base'] = ' - '.join(partes[:-2]) if len(partes) >= 3 else partes[0]
            else:
                # Última parte pode ser estampa
                resultado['estampa'] = ultima_parte
                resultado['nome_base'] = ' - '.join(partes[:-1])
        else:
            resultado['nome_base'] = partes[0]
    
    return resultado


def get_or_create_local_estampa(nome_estampa: str, categoria_id: int) -> Optional[int]:
    """
    Busca ou cria estampa local
    
    Args:
        nome_estampa: Nome da estampa
        categoria_id: ID da categoria
    
    Returns:
        ID da estampa local ou None
    """
    if not nome_estampa:
        return None
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Verificar se estampa existe
        cur.execute("""
            SELECT id FROM estampa WHERE nome = %s LIMIT 1
        """, (nome_estampa,))
        existing = cur.fetchone()
        
        if existing:
            return existing['id']
        
        # Criar estampa básica (precisa de imagem_url obrigatório)
        # Usar placeholder se não tiver
        imagem_url = f"https://via.placeholder.com/300?text={nome_estampa.replace(' ', '+')}"
        
        cur.execute("""
            INSERT INTO estampa (nome, categoria_id, imagem_url, custo_por_metro, ativo)
            VALUES (%s, %s, %s, 0.00, TRUE)
            RETURNING id
        """, (nome_estampa, categoria_id, imagem_url))
        
        estampa_id = cur.fetchone()['id']
        conn.commit()
        
        current_app.logger.info(f"Estampa '{nome_estampa}' criada localmente (ID: {estampa_id})")
        return estampa_id
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar estampa local: {e}")
        return None
    finally:
        cur.close()


def get_or_create_local_tamanho(nome_tamanho: str) -> Optional[int]:
    """
    Busca ou cria tamanho local
    
    Args:
        nome_tamanho: Nome do tamanho
    
    Returns:
        ID do tamanho local ou None
    """
    if not nome_tamanho:
        return None
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Verificar se tamanho existe
        cur.execute("""
            SELECT id FROM tamanho WHERE nome = %s LIMIT 1
        """, (nome_tamanho,))
        existing = cur.fetchone()
        
        if existing:
            return existing['id']
        
        # Criar tamanho
        cur.execute("""
            INSERT INTO tamanho (nome, ativo)
            VALUES (%s, TRUE)
            RETURNING id
        """, (nome_tamanho,))
        
        tamanho_id = cur.fetchone()['id']
        conn.commit()
        
        current_app.logger.info(f"Tamanho '{nome_tamanho}' criado localmente (ID: {tamanho_id})")
        return tamanho_id
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar tamanho local: {e}")
        return None
    finally:
        cur.close()


def create_local_product_from_bling(bling_product: Dict) -> Dict:
    """
    ⚠️ DESABILITADA - Não usar na nova arquitetura
    
    Produtos devem ser criados APENAS localmente (Strapi/admin)
    O Bling apenas recebe produtos já criados
    
    Cria produto no banco local a partir de produto do Bling
    
    Agora sincroniza categorias, estampas e tamanhos do Bling automaticamente
    
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
        nome_completo = bling_product.get('nome', 'Produto sem nome')
        preco = float(bling_product.get('preco', 0))
        ncm = bling_product.get('ncm', '')
        estoque = bling_product.get('estoque', {}).get('atual', 0) if isinstance(bling_product.get('estoque'), dict) else 0
        preco_custo = float(bling_product.get('precoCusto', 0)) if bling_product.get('precoCusto') else 0
        
        # 1. Extrair campos customizados do Bling (prioridade)
        campos_customizados = extract_custom_fields_from_bling_product(bling_product)
        
        # 2. Extrair categoria (primeiro de campos customizados, depois do campo categoria tradicional)
        categoria_nome = campos_customizados.get('categoria')
        categoria_id = None
        
        if categoria_nome:
            categoria_id = get_or_create_local_category_from_bling({'nome': categoria_nome})
        else:
            # Fallback: tentar campo categoria tradicional
            bling_categoria = extract_category_from_bling_product(bling_product)
            if bling_categoria:
                categoria_id = get_or_create_local_category_from_bling(bling_categoria)
        
        # 3. Extrair tecido (de campos customizados)
        tecido_nome = campos_customizados.get('tecido')
        tecido_id = None
        if tecido_nome:
            tecido_id = get_or_create_local_tecido(tecido_nome)
        
        # 4. Extrair estampa (primeiro de campos customizados, depois do nome)
        nome_estampa = campos_customizados.get('estampa')
        if not nome_estampa:
            # Fallback: extrair do nome do produto
            atributos = extract_attributes_from_product_name(nome_completo)
            nome_estampa = atributos.get('estampa')
        
        # 5. Extrair tamanho (primeiro de campos customizados, depois do nome)
        nome_tamanho = campos_customizados.get('tamanho')
        if not nome_tamanho:
            # Fallback: extrair do nome do produto
            if 'atributos' not in locals():
                atributos = extract_attributes_from_product_name(nome_completo)
            nome_tamanho = atributos.get('tamanho')
        
        # 6. Extrair nome base
        # Se campos customizados foram usados, usar o nome completo como base
        # (já que estampa/tamanho vêm dos campos customizados, não do nome)
        if campos_customizados.get('estampa') or campos_customizados.get('tamanho'):
            # Campos customizados foram usados - nome base é o nome completo
            # (a menos que o nome contenha estampa/tamanho que precisam ser removidos)
            nome_base = nome_completo
            
            # Tentar remover estampa e tamanho do nome se estiverem presentes
            if nome_estampa and nome_estampa in nome_base:
                nome_base = nome_base.replace(nome_estampa, '').strip(' -')
            if nome_tamanho and nome_tamanho in nome_base:
                nome_base = nome_base.replace(nome_tamanho, '').strip(' -')
            if 'Tamanho' in nome_base:
                nome_base = nome_base.replace('Tamanho', '').strip(' -')
            
            # Limpar múltiplos espaços e hífens
            nome_base = ' '.join(nome_base.split())
            nome_base = nome_base.replace(' - ', ' ').replace(' -', ' ').replace('- ', ' ')
        else:
            # Fallback: extrair do nome do produto
            if 'atributos' not in locals():
                atributos = extract_attributes_from_product_name(nome_completo)
            nome_base = atributos.get('nome_base', nome_completo)
        
        # 7. Buscar ou criar estampa e tamanho
        estampa_id = None
        tamanho_id = None
        
        if nome_estampa and categoria_id:
            estampa_id = get_or_create_local_estampa(nome_estampa, categoria_id)
        
        if nome_tamanho:
            tamanho_id = get_or_create_local_tamanho(nome_tamanho)
        
        # 4. Se não conseguiu extrair estampa/tamanho, usar padrões
        if not estampa_id:
            cur.execute("SELECT id FROM estampa LIMIT 1")
            estampa_row = cur.fetchone()
            estampa_id = estampa_row['id'] if estampa_row else None
        
        if not tamanho_id:
            cur.execute("SELECT id FROM tamanho LIMIT 1")
            tamanho_row = cur.fetchone()
            tamanho_id = tamanho_row['id'] if tamanho_row else None
        
        # 5. Se não tem categoria, tentar usar categoria da estampa ou criar padrão
        if not categoria_id:
            if estampa_id:
                cur.execute("SELECT categoria_id FROM estampa WHERE id = %s", (estampa_id,))
                estampa_row = cur.fetchone()
                if estampa_row:
                    categoria_id = estampa_row['categoria_id']
            
            # Se ainda não tem, criar categoria padrão
            if not categoria_id:
                categoria_id = get_or_create_local_category_from_bling({'nome': 'Geral'})
        
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
                    custo = %s,
                    atualizado_em = NOW()
                WHERE id = %s
            """, (preco, estoque, ncm, preco_custo, produto_id))
            
            # Atualizar referência Bling
            save_bling_product_reference(produto_id, bling_id, codigo_sku, 'sync')
            
            action = 'update'
        else:
            # Criar novo produto
            # Primeiro, criar ou buscar nome_produto
            cur.execute("""
                SELECT id FROM nome_produto WHERE nome = %s LIMIT 1
            """, (nome_base,))
            nome_produto_row = cur.fetchone()
            
            if not nome_produto_row:
                # Criar nome_produto sem categoria (categoria será linkada depois)
                cur.execute("""
                    INSERT INTO nome_produto (nome, ativo)
                    VALUES (%s, TRUE)
                    RETURNING id
                """, (nome_base,))
                nome_produto_id = cur.fetchone()['id']
                # Criar link com categoria se fornecida
                if categoria_id:
                    cur.execute("""
                        INSERT INTO nome_produto_categoria_lnk (nome_produto_id, categoria_id)
                        VALUES (%s, %s)
                        ON CONFLICT (nome_produto_id, categoria_id) DO NOTHING
                    """, (nome_produto_id, categoria_id))
            else:
                nome_produto_id = nome_produto_row['id']
                # Atualizar categoria se necessário (usando tabela de link)
                if categoria_id:
                    # Verificar se já existe link
                    cur.execute("""
                        SELECT id FROM nome_produto_categoria_lnk 
                        WHERE nome_produto_id = %s AND categoria_id = %s
                    """, (nome_produto_id, categoria_id))
                    if not cur.fetchone():
                        # Remover links antigos e criar novo
                        cur.execute("""
                            DELETE FROM nome_produto_categoria_lnk 
                            WHERE nome_produto_id = %s
                        """, (nome_produto_id,))
                        cur.execute("""
                            INSERT INTO nome_produto_categoria_lnk (nome_produto_id, categoria_id)
                            VALUES (%s, %s)
                        """, (nome_produto_id, categoria_id))
            
            # Verificar se tem estampa e tamanho
            if not estampa_id or not tamanho_id:
                current_app.logger.warning(
                    f"Estampa (ID: {estampa_id}) ou tamanho (ID: {tamanho_id}) não encontrado. "
                    f"Produto não pode ser criado."
                )
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
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                RETURNING id
            """, (nome_produto_id, estampa_id, tamanho_id, codigo_sku, preco, estoque, ncm, preco_custo))
            
            produto_id = cur.fetchone()['id']
            
            # Salvar referência Bling
            save_bling_product_reference(produto_id, bling_id, codigo_sku, 'sync')
            
            action = 'create'
        
        conn.commit()
        
        log_sync('produto', produto_id, action, {
            'status': 'success',
            'bling_id': bling_id,
            'action': action,
            'categoria_id': categoria_id,
            'tecido_id': tecido_id,
            'estampa_id': estampa_id,
            'tamanho_id': tamanho_id,
            'campos_customizados': campos_customizados
        })
        
        return {
            'success': True,
            'produto_id': produto_id,
            'action': action,
            'bling_id': bling_id,
            'categoria_id': categoria_id,
            'tecido_id': tecido_id,
            'estampa_id': estampa_id,
            'tamanho_id': tamanho_id,
            'campos_customizados_usados': campos_customizados
        }
        
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar produto do Bling: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        cur.close()


def sync_products_from_bling(limit: int = 50, include_details: bool = True) -> Dict:
    """
    ⚠️ DESABILITADA - Não usar para criar produtos
    
    Produtos devem ser criados APENAS localmente (Strapi/admin)
    O Bling apenas recebe produtos já criados
    
    Esta função foi desabilitada conforme a nova arquitetura.
    Use apenas funções de sincronização de estoque/preço.
    
    Args:
        limit: Quantidade de produtos para sincronizar
    
    Returns:
        Dict com erro indicando que a funcionalidade foi desabilitada
    """
    return {
        'success': False,
        'error': 'Importação de produtos do Bling foi desabilitada. Produtos devem ser criados localmente (Strapi/admin) e enviados para o Bling.',
        'total': 0,
        'results': []
    }


# =====================================================
# SINCRONIZAÇÃO DE ESTOQUE
# =====================================================

def sync_price_from_bling(produto_id: int = None) -> Dict:
    """
    Sincroniza preço de venda do Bling para o banco local
    
    ⚠️ IMPORTANTE: Atualiza apenas `preco_venda`, NUNCA `preco_promocional`
    Preço promocional é gerenciado localmente e não é sincronizado com o Bling
    
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
                SELECT p.id, bp.bling_id, p.codigo_sku
                FROM produtos p
                JOIN bling_produtos bp ON p.id = bp.produto_id
                WHERE p.id = %s
            """, (produto_id,))
            products = cur.fetchall()
        else:
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
                preco_bling = float(bling_product.get('preco', 0))
                
                # Atualizar apenas preco_venda (NUNCA preco_promocional)
                cur.execute("""
                    UPDATE produtos
                    SET preco_venda = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (preco_bling, produto_id_local))
                
                conn.commit()
                
                log_sync('produto', produto_id_local, 'sync', {
                    'status': 'success',
                    'action': 'price_update',
                    'preco_novo': preco_bling
                })
                
                results.append({
                    'produto_id': produto_id_local,
                    'success': True,
                    'preco_novo': preco_bling
                })
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                current_app.logger.error(f"Erro ao sincronizar preço do produto {product_row['id']}: {e}")
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
        current_app.logger.error(f"Erro ao sincronizar preço: {e}")
        return {
            'success': False,
            'error': str(e),
            'total': 0,
            'results': []
        }
    finally:
        cur.close()


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
                
                # Extrair estoque do Bling (pode estar em diferentes formatos)
                # IMPORTANTE: Bling usa 'saldoVirtualTotal' para estoque atual, não 'atual'
                estoque_bling = 0
                estoque_dict = bling_product.get('estoque', {})
                if isinstance(estoque_dict, dict):
                    # Tentar diferentes chaves (Bling usa 'saldoVirtualTotal')
                    estoque_bling = (
                        estoque_dict.get('saldoVirtualTotal') or  # Chave correta do Bling
                        estoque_dict.get('atual') or 
                        estoque_dict.get('quantidade') or
                        0
                    )
                elif 'estoque' in bling_product:
                    estoque_bling = bling_product.get('estoque', 0)
                
                # Buscar estoque atual do banco para comparar (ANTES de atualizar)
                cur.execute("SELECT estoque FROM produtos WHERE id = %s", (produto_id_local,))
                estoque_row = cur.fetchone()
                estoque_local_atual = estoque_row['estoque'] if estoque_row else None
                
                current_app.logger.info(
                    f"[sync_stock_from_bling] Produto {produto_id_local}: "
                    f"Estoque Bling={estoque_bling}, Estoque local atual={estoque_local_atual}"
                )
                
                # Atualizar estoque no banco local
                cur.execute("""
                    UPDATE produtos
                    SET estoque = %s,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (int(estoque_bling) if estoque_bling is not None else 0, produto_id_local))
                
                if cur.rowcount > 0:
                    conn.commit()
                    current_app.logger.info(
                        f"[sync_stock_from_bling] Produto {produto_id_local}: "
                        f"Estoque atualizado no banco de {estoque_local_atual} para {estoque_bling}"
                    )
                else:
                    current_app.logger.warning(
                        f"[sync_stock_from_bling] Produto {produto_id_local}: "
                        f"Nenhuma linha atualizada (produto pode não existir)"
                    )
                
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
                
                # Log do estoque local antes de sincronizar
                current_app.logger.info(
                    f"[sync_stock_to_bling] Produto {produto_id_local}: "
                    f"Estoque local={estoque_local}, Bling ID={bling_id}"
                )
                
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
                
                # Estratégia: Manter todos os campos do produto do Bling e apenas atualizar estoque
                # Isso é necessário porque produtos criados manualmente no Bling podem ter
                # campos obrigatórios que não temos no sistema local
                update_data = dict(bling_product)  # Copiar todos os campos
                
                # Atualizar apenas o estoque mantendo estrutura original
                # IMPORTANTE: Garantir que o estoque seja um número inteiro válido
                # IMPORTANTE: Bling usa 'saldoVirtualTotal' para estoque atual, não 'atual'
                estoque_local_int = int(estoque_local) if estoque_local is not None else 0
                
                if 'estoque' in bling_product and isinstance(bling_product['estoque'], dict):
                    estoque_dict_bling = bling_product['estoque']
                    # Obter estoque atual do Bling (pode estar em 'saldoVirtualTotal' ou 'atual')
                    estoque_bling_atual = (
                        estoque_dict_bling.get('saldoVirtualTotal') or 
                        estoque_dict_bling.get('atual') or 
                        0
                    )
                    
                    update_data['estoque'] = dict(estoque_dict_bling)
                    # Atualizar usando 'saldoVirtualTotal' (campo correto do Bling)
                    update_data['estoque']['saldoVirtualTotal'] = estoque_local_int
                    # Remover 'atual' se existir (não é usado pelo Bling)
                    update_data['estoque'].pop('atual', None)
                    
                    # Garantir que minimo e maximo também sejam inteiros
                    if 'minimo' in update_data['estoque']:
                        update_data['estoque']['minimo'] = int(update_data['estoque']['minimo']) if update_data['estoque']['minimo'] is not None else 0
                    if 'maximo' in update_data['estoque']:
                        update_data['estoque']['maximo'] = int(update_data['estoque']['maximo']) if update_data['estoque']['maximo'] is not None else 0
                else:
                    estoque_bling_atual = 0
                    update_data['estoque'] = {
                        'minimo': int(bling_product.get('estoque', {}).get('minimo', 0)) if isinstance(bling_product.get('estoque'), dict) else 0,
                        'maximo': int(bling_product.get('estoque', {}).get('maximo', 0)) if isinstance(bling_product.get('estoque'), dict) else 0,
                        'saldoVirtualTotal': estoque_local_int  # Usar saldoVirtualTotal em vez de atual
                    }
                
                current_app.logger.debug(
                    f"[sync_stock_to_bling] Dados de estoque a serem enviados: {json.dumps(update_data['estoque'], ensure_ascii=False)}"
                )
                current_app.logger.info(
                    f"[sync_stock_to_bling] Produto {produto_id_local}: "
                    f"Estoque Bling atual={estoque_bling_atual}, "
                    f"Estoque local={estoque_local_int}, "
                    f"Enviando saldoVirtualTotal={update_data['estoque'].get('saldoVirtualTotal')}"
                )
                
                # IMPORTANTE: O Bling não atualiza estoque via PUT no produto
                # O campo 'saldoVirtualTotal' é calculado (read-only)
                # Vamos manter o estoque no update_data, mas não esperar que seja atualizado
                # O estoque será atualizado via endpoint específico de estoque (se disponível)
                saldo_virtual_total = update_data.get('estoque', {}).get('saldoVirtualTotal', estoque_local_int)
                
                # Remover campos que não devem ser enviados no PUT (apenas leitura)
                campos_readonly = ['id', 'dataCriacao', 'dataAlteracao', 'usuario']
                for campo in campos_readonly:
                    update_data.pop(campo, None)
                
                try:
                    # 1. Atualizar produto (o Bling pode ignorar o estoque, mas vamos tentar)
                    response = make_bling_api_request('PUT', f'/produtos/{bling_id}', json=update_data)
                    
                    # 2. Tentar atualizar estoque via endpoint específico de estoque
                    # O Bling não atualiza estoque via PUT no produto (saldoVirtualTotal é read-only)
                    # Precisamos criar um lançamento de estoque
                    try:
                        depositos_response = make_bling_api_request('GET', '/depositos')
                        deposito_id = None
                        if depositos_response.status_code == 200:
                            depositos_data = depositos_response.json().get('data', [])
                            if depositos_data and len(depositos_data) > 0:
                                deposito_id = depositos_data[0].get('id')
                        
                        if deposito_id:
                            # Calcular diferença entre estoque atual do Bling e estoque local
                            diferenca = saldo_virtual_total - estoque_bling_atual
                            
                            if abs(diferenca) > 0:
                                # Criar lançamento de estoque para ajustar o saldo
                                tipo_lancamento = "E" if diferenca > 0 else "S"
                                quantidade_absoluta = abs(diferenca)
                                
                                # Estrutura do payload para lançamento de estoque
                                # tipoOperacao é obrigatório e deve ser string: "E"=Entrada, "S"=Saída, "B"=Balanço
                                # O campo "tipo" também deve ser "E" ou "S"
                                estoque_payload = {
                                    "produto": {
                                        "id": bling_id
                                    },
                                    "deposito": {
                                        "id": deposito_id
                                    },
                                    "tipo": tipo_lancamento,  # E=Entrada, S=Saída
                                    "tipoOperacao": tipo_lancamento,  # "E"=Entrada, "S"=Saída (obrigatório, deve ser string)
                                    "quantidade": quantidade_absoluta
                                }
                                
                                current_app.logger.info(
                                    f"[sync_stock_to_bling] Tentando atualizar estoque via /estoques: "
                                    f"tipo={tipo_lancamento}, quantidade={quantidade_absoluta}, "
                                    f"diferenca={diferenca:+d}"
                                )
                                
                                try:
                                    estoque_response = make_bling_api_request('POST', '/estoques', json=estoque_payload)
                                    if estoque_response.status_code in [200, 201]:
                                        current_app.logger.info(
                                            f"[sync_stock_to_bling] ✅ Estoque atualizado via /estoques: "
                                            f"{estoque_bling_atual} -> {saldo_virtual_total}"
                                        )
                                    else:
                                        error_text = getattr(estoque_response, 'text', '')
                                        current_app.logger.warning(
                                            f"[sync_stock_to_bling] ⚠️ Falha ao atualizar estoque via /estoques: "
                                            f"{estoque_response.status_code} - {error_text[:300]}"
                                        )
                                        # Não falhar a sincronização por causa do estoque
                                except BlingAPIError as estoque_err:
                                    # Logar mas não falhar - estoque pode precisar ser atualizado manualmente
                                    current_app.logger.warning(
                                        f"[sync_stock_to_bling] ⚠️ Não foi possível atualizar estoque via /estoques: "
                                        f"{estoque_err.message}. Estoque local={saldo_virtual_total}, "
                                        f"Estoque Bling={estoque_bling_atual}. "
                                        f"Atualize manualmente no Bling se necessário."
                                    )
                                except Exception as estoque_err:
                                    current_app.logger.warning(
                                        f"[sync_stock_to_bling] ⚠️ Erro ao atualizar estoque via /estoques: {estoque_err}"
                                    )
                        else:
                            current_app.logger.warning(
                                f"[sync_stock_to_bling] ⚠️ Depósito não encontrado. "
                                f"Estoque não pode ser atualizado automaticamente. "
                                f"Estoque local={saldo_virtual_total}, Estoque Bling={estoque_bling_atual}"
                            )
                    except Exception as e:
                        current_app.logger.debug(f"[sync_stock_to_bling] Erro ao buscar depósitos: {e}")
                    
                    # Verificar resposta do Bling para confirmar que o estoque foi atualizado
                    if response.status_code in [200, 201]:
                        response_data = response.json()
                        bling_product_updated = response_data.get('data', {})
                        estoque_atualizado = None
                        if isinstance(bling_product_updated.get('estoque'), dict):
                            estoque_atualizado = bling_product_updated['estoque'].get('atual')
                        elif 'estoque' in bling_product_updated:
                            estoque_atualizado = bling_product_updated.get('estoque')
                        
                        estoque_esperado = update_data['estoque'].get('saldoVirtualTotal') or update_data['estoque'].get('atual', 'N/A')
                        current_app.logger.info(
                            f"[sync_stock_to_bling] Produto {produto_id_local}: "
                            f"Resposta do Bling - Estoque atualizado={estoque_atualizado}, "
                            f"Esperado={estoque_esperado}"
                        )
                        
                        # Se a resposta não contém estoque, fazer uma nova busca para confirmar
                        if estoque_atualizado is None:
                            current_app.logger.debug(
                                f"[sync_stock_to_bling] Resposta não contém estoque, fazendo GET para confirmar..."
                            )
                            verify_response = make_bling_api_request('GET', f'/produtos/{bling_id}')
                            if verify_response.status_code == 200:
                                verify_data = verify_response.json().get('data', {})
                                # Tentar diferentes formatos de estoque
                                estoque_verificado = None
                                estoque_dict = verify_data.get('estoque', {})
                                
                                # Log completo da resposta para debug
                                current_app.logger.debug(
                                    f"[sync_stock_to_bling] Resposta completa do GET (produto completo): "
                                    f"{json.dumps(verify_data, ensure_ascii=False, indent=2)[:1000]}"
                                )
                                
                                if isinstance(estoque_dict, dict):
                                    # Bling usa 'saldoVirtualTotal' para estoque atual
                                    estoque_verificado = (
                                        estoque_dict.get('saldoVirtualTotal') or  # Chave correta do Bling
                                        estoque_dict.get('atual') or 
                                        estoque_dict.get('quantidade') or 
                                        0
                                    )
                                    current_app.logger.debug(
                                        f"[sync_stock_to_bling] Estrutura do estoque: {type(estoque_dict).__name__}, "
                                        f"Chaves: {list(estoque_dict.keys())}, "
                                        f"Valores: {estoque_dict}"
                                    )
                                elif 'estoque' in verify_data:
                                    estoque_verificado = verify_data.get('estoque')
                                
                                estoque_esperado = update_data['estoque'].get('saldoVirtualTotal') or update_data['estoque'].get('atual', 'N/A')
                                current_app.logger.info(
                                    f"[sync_stock_to_bling] Produto {produto_id_local}: "
                                    f"Estoque verificado via GET={estoque_verificado}, "
                                    f"Esperado={estoque_esperado}"
                                )
                    
                    # Se chegou aqui, a requisição foi bem-sucedida
                    # (make_bling_api_request lança exceção em caso de erro)
                    # NOTA: O estoque pode não ter sido atualizado (saldoVirtualTotal é read-only)
                    # Mas a sincronização do produto foi bem-sucedida
                    
                except BlingAPIError as e:
                    # Capturar erro específico da API do Bling
                    error_message = e.message
                except (KeyError, Exception) as e:
                    # Capturar outros erros (incluindo KeyError)
                    error_message = str(e)
                    # Se houver detalhes, incluí-los (apenas para BlingAPIError)
                    if hasattr(e, 'error_details') and e.error_details:
                        if isinstance(e.error_details, dict):
                            # Tentar extrair mensagem mais específica
                            error_desc = e.error_details.get('description') or e.error_details.get('message')
                            if error_desc:
                                error_message = error_desc
                            # Log detalhado para debug
                            current_app.logger.error(
                                f"❌ Detalhes do erro de validação Bling: {json.dumps(e.error_details, indent=2, ensure_ascii=False)}"
                            )
                    
                    current_app.logger.error(
                        f"❌ Erro ao atualizar estoque no Bling para produto {produto_id_local} "
                        f"(Bling ID: {bling_id}): {error_message}"
                    )
                    results.append({
                        'produto_id': produto_id_local,
                        'success': False,
                        'error': error_message
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
                import traceback
                current_app.logger.error(
                    f"Erro ao sincronizar estoque para Bling do produto {product_row['id']}: {e}",
                    exc_info=True
                )
                current_app.logger.error(f"Traceback completo: {traceback.format_exc()}")
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

