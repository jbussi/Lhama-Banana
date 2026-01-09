"""
Service para gerenciamento de clientes/contatos com Bling
==========================================================

Gerencia sincronização de clientes (contatos) entre LhamaBanana e Bling:
- Criação automática de clientes no Bling
- Reutilização de clientes existentes
- Suporte CPF e CNPJ
- Validação de endereços fiscais
"""
from flask import current_app
from typing import Dict, Optional, List
from .db import get_db
from .bling_api_service import make_bling_api_request, BlingAPIError, BlingErrorType
import psycopg2.extras
import re


def validate_cpf_cnpj(cpf_cnpj: str) -> tuple:
    """
    Valida CPF ou CNPJ
    
    Returns:
        Tuple (is_valid, tipo) onde tipo é 'CPF' ou 'CNPJ' ou None
    """
    # Remover formatação
    cpf_cnpj_clean = re.sub(r'[^0-9]', '', cpf_cnpj)
    
    if len(cpf_cnpj_clean) == 11:
        # CPF
        # Validação básica (dígitos verificadores)
        if cpf_cnpj_clean == cpf_cnpj_clean[0] * 11:
            return False, None
        
        # Calcular dígitos verificadores
        def calcular_digito(cpf, peso_inicial):
            soma = sum(int(digito) * (peso_inicial - i) for i, digito in enumerate(cpf))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)
        
        digito1 = calcular_digito(cpf_cnpj_clean[:9], 10)
        digito2 = calcular_digito(cpf_cnpj_clean[:10], 11)
        
        if cpf_cnpj_clean[9] == digito1 and cpf_cnpj_clean[10] == digito2:
            return True, 'CPF'
        return False, None
    
    elif len(cpf_cnpj_clean) == 14:
        # CNPJ
        # Validação básica
        if cpf_cnpj_clean == cpf_cnpj_clean[0] * 14:
            return False, None
        
        # Calcular dígitos verificadores
        def calcular_digito_cnpj(cnpj, peso_inicial):
            pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            soma = sum(int(cnpj[i]) * pesos[i] for i in range(len(cnpj)))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)
        
        digito1 = calcular_digito_cnpj(cpf_cnpj_clean[:12], 5)
        digito2 = calcular_digito_cnpj(cpf_cnpj_clean[:13], 6)
        
        if cpf_cnpj_clean[12] == digito1 and cpf_cnpj_clean[13] == digito2:
            return True, 'CNPJ'
        return False, None
    
    return False, None


def validate_fiscal_data(cliente_data: Dict) -> List[str]:
    """
    Valida dados fiscais do cliente antes de enviar para Bling
    
    Returns:
        Lista de erros (vazia se válido)
    """
    errors = []
    
    # CPF/CNPJ obrigatório
    cpf_cnpj = cliente_data.get('cpf_cnpj', '')
    if not cpf_cnpj:
        errors.append("CPF/CNPJ é obrigatório")
    else:
        cpf_cnpj_clean = re.sub(r'[^0-9]', '', cpf_cnpj)
        is_valid, tipo = validate_cpf_cnpj(cpf_cnpj_clean)
        if not is_valid:
            errors.append(f"CPF/CNPJ inválido: {cpf_cnpj}")
    
    # Nome/Razão Social obrigatório
    if not cliente_data.get('nome'):
        errors.append("Nome/Razão Social é obrigatório")
    
    # Endereço obrigatório
    if not cliente_data.get('endereco'):
        errors.append("Endereço é obrigatório")
    if not cliente_data.get('numero'):
        errors.append("Número do endereço é obrigatório")
    if not cliente_data.get('bairro'):
        errors.append("Bairro é obrigatório")
    if not cliente_data.get('cidade'):
        errors.append("Cidade é obrigatória")
    if not cliente_data.get('uf'):
        errors.append("Estado (UF) é obrigatório")
    
    # CEP obrigatório e válido (8 dígitos)
    cep = cliente_data.get('cep', '').replace('-', '').replace(' ', '')
    if not cep:
        errors.append("CEP é obrigatório")
    elif len(cep) != 8 or not cep.isdigit():
        errors.append("CEP deve ter 8 dígitos")
    
    # Inscrição Estadual obrigatória para CNPJ
    tipo_pessoa = cliente_data.get('tipoPessoa', '')
    if tipo_pessoa == 'J' and not cliente_data.get('ie'):
        errors.append("Inscrição Estadual é obrigatória para CNPJ")
    
    return errors


def find_client_in_bling(cpf_cnpj: str) -> Optional[Dict]:
    """
    Busca cliente no Bling por CPF/CNPJ
    
    Args:
        cpf_cnpj: CPF ou CNPJ (com ou sem formatação)
    
    Returns:
        Dict com dados do cliente se encontrado, None caso contrário
    """
    # Limpar formatação
    cpf_cnpj_clean = re.sub(r'[^0-9]', '', cpf_cnpj)
    
    try:
        # Buscar contatos no Bling filtrando por CPF/CNPJ
        # O Bling permite buscar por vários campos, incluindo documento
        response = make_bling_api_request(
            'GET',
            '/contatos',
            params={
                'cpf_cnpj': cpf_cnpj_clean,
                'tipo': 'C',  # C = Cliente
                'limite': 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            contatos = data.get('data', [])
            
            # Procurar exatamente o CPF/CNPJ (pode haver múltiplos resultados)
            for contato in contatos:
                contato_cpf_cnpj = re.sub(r'[^0-9]', '', contato.get('cpf_cnpj', ''))
                if contato_cpf_cnpj == cpf_cnpj_clean:
                    current_app.logger.info(f"✅ Cliente encontrado no Bling: {cpf_cnpj_clean} (ID: {contato.get('id')})")
                    return contato
            
            current_app.logger.debug(f"ℹ️ Cliente não encontrado no Bling: {cpf_cnpj_clean}")
            return None
        
        elif response.status_code == 404:
            # Nenhum contato encontrado
            return None
        else:
            current_app.logger.warning(f"⚠️ Erro ao buscar cliente no Bling: {response.status_code}")
            return None
            
    except BlingAPIError as e:
        if e.error_type == BlingErrorType.NOT_FOUND_ERROR:
            return None
        current_app.logger.error(f"❌ Erro ao buscar cliente no Bling: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"❌ Erro inesperado ao buscar cliente no Bling: {e}", exc_info=True)
        return None


def map_client_to_bling_format(cliente_data: Dict) -> Dict:
    """
    Mapeia dados do cliente do formato LhamaBanana para formato Bling
    
    Args:
        cliente_data: Dict com dados do cliente (pode vir de venda ou dados_fiscais)
    
    Returns:
        Dict formatado para API do Bling
    """
    # Limpar CPF/CNPJ
    cpf_cnpj = re.sub(r'[^0-9]', '', cliente_data.get('cpf_cnpj', ''))
    
    # Determinar tipo de pessoa
    if len(cpf_cnpj) == 14:
        tipo_pessoa = 'J'  # Pessoa Jurídica (CNPJ)
    else:
        tipo_pessoa = 'F'  # Pessoa Física (CPF)
    
    # Limpar CEP
    cep = re.sub(r'[^0-9]', '', cliente_data.get('cep', ''))
    
    bling_client = {
        "nome": cliente_data.get('nome', 'Cliente'),
        "tipoPessoa": tipo_pessoa,
        "cpf_cnpj": cpf_cnpj,
        "ie": cliente_data.get('ie') or cliente_data.get('inscricao_estadual') or "",
        "contribuinte": 1 if tipo_pessoa == 'J' else 9,  # 1=Contribuinte ICMS, 9=Não contribuinte
        "endereco": cliente_data.get('endereco') or cliente_data.get('rua', ''),
        "numero": cliente_data.get('numero', ''),
        "complemento": cliente_data.get('complemento') or "",
        "bairro": cliente_data.get('bairro', ''),
        "cidade": cliente_data.get('cidade', ''),
        "uf": cliente_data.get('uf') or cliente_data.get('estado', ''),
        "cep": cep,
        "email": cliente_data.get('email') or cliente_data.get('email_entrega', ''),
        "celular": cliente_data.get('celular') or cliente_data.get('telefone') or cliente_data.get('telefone_entrega', ''),
        "tipo": "C"  # C = Cliente
    }
    
    # Telefone fixo (se disponível)
    if cliente_data.get('telefone_fixo'):
        bling_client["fone"] = cliente_data['telefone_fixo']
    
    return bling_client


def create_or_update_client_in_bling(cliente_data: Dict) -> Dict:
    """
    Cria ou atualiza cliente no Bling
    
    Primeiro verifica se cliente já existe (por CPF/CNPJ).
    Se existir, atualiza. Se não existir, cria.
    
    Args:
        cliente_data: Dict com dados do cliente
    
    Returns:
        Dict com resultado da operação:
        {
            'success': bool,
            'bling_client_id': int (se sucesso),
            'created': bool (True = criado, False = atualizado),
            'error': str (se erro)
        }
    """
    # Validar dados
    validation_errors = validate_fiscal_data(cliente_data)
    if validation_errors:
        return {
            'success': False,
            'error': 'Validação falhou',
            'details': validation_errors
        }
    
    cpf_cnpj_clean = re.sub(r'[^0-9]', '', cliente_data.get('cpf_cnpj', ''))
    
    try:
        # 1. Buscar cliente existente
        existing_client = find_client_in_bling(cpf_cnpj_clean)
        
        # 2. Mapear dados para formato Bling
        bling_client_data = map_client_to_bling_format(cliente_data)
        
        if existing_client:
            # 3a. Atualizar cliente existente
            bling_client_id = existing_client.get('id')
            
            current_app.logger.info(f"🔄 Atualizando cliente existente no Bling: {cpf_cnpj_clean} (ID: {bling_client_id})")
            
            response = make_bling_api_request(
                'PUT',
                f'/contatos/{bling_client_id}',
                json=bling_client_data
            )
            
            if response.status_code in [200, 201]:
                current_app.logger.info(f"✅ Cliente atualizado no Bling: {cpf_cnpj_clean} (ID: {bling_client_id})")
                return {
                    'success': True,
                    'bling_client_id': bling_client_id,
                    'created': False,
                    'cpf_cnpj': cpf_cnpj_clean
                }
            else:
                error_text = response.text
                current_app.logger.error(f"❌ Erro ao atualizar cliente no Bling: {response.status_code} - {error_text}")
                return {
                    'success': False,
                    'error': f"Erro HTTP {response.status_code}",
                    'details': error_text
                }
        else:
            # 3b. Criar novo cliente
            current_app.logger.info(f"➕ Criando novo cliente no Bling: {cpf_cnpj_clean}")
            
            response = make_bling_api_request(
                'POST',
                '/contatos',
                json=bling_client_data
            )
            
            if response.status_code in [200, 201]:
                response_data = response.json()
                bling_client_id = response_data.get('data', {}).get('id')
                
                if not bling_client_id:
                    # Tentar extrair ID da resposta
                    if 'data' in response_data and isinstance(response_data['data'], dict):
                        bling_client_id = response_data['data'].get('id')
                    elif 'id' in response_data:
                        bling_client_id = response_data['id']
                
                current_app.logger.info(f"✅ Cliente criado no Bling: {cpf_cnpj_clean} (ID: {bling_client_id})")
                return {
                    'success': True,
                    'bling_client_id': bling_client_id,
                    'created': True,
                    'cpf_cnpj': cpf_cnpj_clean
                }
            else:
                error_text = response.text
                current_app.logger.error(f"❌ Erro ao criar cliente no Bling: {response.status_code} - {error_text}")
                return {
                    'success': False,
                    'error': f"Erro HTTP {response.status_code}",
                    'details': error_text
                }
                
    except BlingAPIError as e:
        current_app.logger.error(f"❌ Erro da API Bling ao criar/atualizar cliente: {e}")
        return {
            'success': False,
            'error': str(e),
            'error_type': e.error_type.value
        }
    except Exception as e:
        current_app.logger.error(f"❌ Erro inesperado ao criar/atualizar cliente no Bling: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def get_client_data_from_order(venda_id: int) -> Optional[Dict]:
    """
    Extrai dados do cliente de uma venda para criar/atualizar no Bling
    
    Args:
        venda_id: ID da venda
    
    Returns:
        Dict com dados do cliente ou None se não encontrado/dados incompletos
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar dados da venda com informações fiscais
        cur.execute("""
            SELECT 
                v.fiscal_tipo,
                v.fiscal_cpf_cnpj,
                v.fiscal_nome_razao_social,
                v.fiscal_inscricao_estadual,
                v.nome_recebedor,
                v.email_entrega,
                v.telefone_entrega,
                v.rua_entrega,
                v.numero_entrega,
                v.complemento_entrega,
                v.bairro_entrega,
                v.cidade_entrega,
                v.estado_entrega,
                v.cep_entrega,
                u.email as usuario_email,
                u.nome as usuario_nome
            FROM vendas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.id = %s
        """, (venda_id,))
        
        venda = cur.fetchone()
        
        if not venda:
            return None
        
        # Verificar se tem dados fiscais obrigatórios
        if not venda.get('fiscal_cpf_cnpj') or not venda.get('fiscal_nome_razao_social'):
            current_app.logger.warning(f"⚠️ Venda {venda_id} não possui dados fiscais completos")
            return None
        
        # Montar dados do cliente
        cliente_data = {
            'nome': venda.get('fiscal_nome_razao_social') or venda.get('nome_recebedor') or venda.get('usuario_nome'),
            'cpf_cnpj': venda.get('fiscal_cpf_cnpj'),
            'ie': venda.get('fiscal_inscricao_estadual'),
            'email': venda.get('email_entrega') or venda.get('usuario_email'),
            'celular': venda.get('telefone_entrega'),
            'endereco': venda.get('rua_entrega'),
            'numero': venda.get('numero_entrega'),
            'complemento': venda.get('complemento_entrega'),
            'bairro': venda.get('bairro_entrega'),
            'cidade': venda.get('cidade_entrega'),
            'uf': venda.get('estado_entrega'),
            'cep': venda.get('cep_entrega')
        }
        
        return cliente_data
        
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao buscar dados do cliente da venda {venda_id}: {e}", exc_info=True)
        return None
    finally:
        cur.close()


def sync_client_for_order(venda_id: int) -> Dict:
    """
    Sincroniza cliente no Bling quando um pedido é criado
    
    Args:
        venda_id: ID da venda
    
    Returns:
        Dict com resultado da sincronização
    """
    # Buscar dados do cliente da venda
    cliente_data = get_client_data_from_order(venda_id)
    
    if not cliente_data:
        return {
            'success': False,
            'error': 'Dados do cliente não encontrados ou incompletos na venda',
            'venda_id': venda_id
        }
    
    # Criar/atualizar cliente no Bling
    result = create_or_update_client_in_bling(cliente_data)
    
    if result.get('success'):
        current_app.logger.info(
            f"✅ Cliente sincronizado no Bling para venda {venda_id}: "
            f"ID Bling: {result.get('bling_client_id')}, "
            f"CPF/CNPJ: {result.get('cpf_cnpj')}"
        )
    
    return {
        **result,
        'venda_id': venda_id
    }

