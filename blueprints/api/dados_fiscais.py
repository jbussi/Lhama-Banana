from . import api_bp
from flask import jsonify, request
from ..services.auth_service import verify_firebase_token
from ..services.user_service import get_user_by_firebase_uid
from ..services import get_db
import re

def validate_cpf(cpf):
    """Valida CPF (formato e dígitos verificadores)"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False
    
    # Validar dígitos verificadores
    def calc_digit(cpf, weight):
        total = sum(int(cpf[i]) * weight[i] for i in range(len(weight)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    if int(cpf[9]) != calc_digit(cpf, list(range(10, 1, -1))):
        return False
    if int(cpf[10]) != calc_digit(cpf, list(range(11, 1, -1))):
        return False
    return True

def validate_cnpj(cnpj):
    """Valida CNPJ (formato e dígitos verificadores)"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False
    
    # Validar dígitos verificadores
    def calc_digit(cnpj, weight):
        total = sum(int(cnpj[i]) * weight[i] for i in range(len(weight)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    weight1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weight2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    if int(cnpj[12]) != calc_digit(cnpj, weight1):
        return False
    if int(cnpj[13]) != calc_digit(cnpj, weight2):
        return False
    return True

@api_bp.route('/fiscal-data', methods=['GET'])
def get_fiscal_data():
    """Retorna os dados fiscais do usuário logado."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    id_token = auth_header.split(' ')[1]
    
    try:
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token['uid']
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        conn = get_db()
        cur = None
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    id, tipo, cpf_cnpj, nome_razao_social,
                    inscricao_estadual, inscricao_municipal,
                    rua, numero, complemento, bairro, cidade, estado, cep,
                    ativo, criado_em, atualizado_em
                FROM dados_fiscais
                WHERE usuario_id = %s AND ativo = TRUE
            """, (user_data['id'],))
            
            fiscal_data = cur.fetchone()
        finally:
            if cur:
                cur.close()
        
        if not fiscal_data:
            return jsonify({"fiscal_data": None}), 200
        
        return jsonify({
            "fiscal_data": {
                "id": fiscal_data[0],
                "tipo": fiscal_data[1],
                "cpf_cnpj": fiscal_data[2],
                "nome_razao_social": fiscal_data[3],
                "inscricao_estadual": fiscal_data[4],
                "inscricao_municipal": fiscal_data[5],
                "endereco": {
                    "rua": fiscal_data[6],
                    "numero": fiscal_data[7],
                    "complemento": fiscal_data[8] or '',
                    "bairro": fiscal_data[9],
                    "cidade": fiscal_data[10],
                    "estado": fiscal_data[11],
                    "cep": fiscal_data[12]
                },
                "ativo": fiscal_data[13],
                "criado_em": str(fiscal_data[14]) if fiscal_data[14] else None,
                "atualizado_em": str(fiscal_data[15]) if fiscal_data[15] else None
            }
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar dados fiscais: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor"}), 500

@api_bp.route('/fiscal-data', methods=['POST'])
def create_fiscal_data():
    """Cria ou atualiza os dados fiscais do usuário."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    id_token = auth_header.split(' ')[1]
    
    try:
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token['uid']
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Dados não fornecidos"}), 400
        
        # Validar campos obrigatórios
        tipo = data.get('tipo', '').upper()
        if tipo not in ['CPF', 'CNPJ']:
            return jsonify({"erro": "Tipo deve ser CPF ou CNPJ"}), 400
        
        cpf_cnpj = re.sub(r'[^0-9]', '', data.get('cpf_cnpj', ''))
        nome_razao_social = data.get('nome_razao_social', '').strip()
        
        if not cpf_cnpj:
            return jsonify({"erro": "CPF/CNPJ é obrigatório"}), 400
        if not nome_razao_social:
            return jsonify({"erro": "Nome/Razão Social é obrigatório"}), 400
        
        # Validar CPF/CNPJ
        if tipo == 'CPF':
            if not validate_cpf(cpf_cnpj):
                return jsonify({"erro": "CPF inválido"}), 400
        else:
            if not validate_cnpj(cpf_cnpj):
                return jsonify({"erro": "CNPJ inválido"}), 400
        
        # Validar endereço
        endereco = data.get('endereco', {})
        if not all([endereco.get('rua'), endereco.get('numero'), 
                   endereco.get('bairro'), endereco.get('cidade'), 
                   endereco.get('estado'), endereco.get('cep')]):
            return jsonify({"erro": "Endereço fiscal incompleto"}), 400
        
        cep = re.sub(r'[^0-9]', '', endereco.get('cep', ''))
        if len(cep) != 8:
            return jsonify({"erro": "CEP inválido"}), 400
        
        conn = get_db()
        cur = None
        try:
            cur = conn.cursor()
            
            # Verificar se já existe (ativo ou inativo)
            cur.execute("SELECT id, ativo FROM dados_fiscais WHERE usuario_id = %s", (user_data['id'],))
            existing = cur.fetchone()
            
            if existing:
                # Atualizar existente (reativar se estiver inativo)
                cur.execute("""
                    UPDATE dados_fiscais SET
                        tipo = %s,
                        cpf_cnpj = %s,
                        nome_razao_social = %s,
                        inscricao_estadual = %s,
                        inscricao_municipal = %s,
                        rua = %s,
                        numero = %s,
                        complemento = %s,
                        bairro = %s,
                        cidade = %s,
                        estado = %s,
                        cep = %s,
                        ativo = TRUE,
                        atualizado_em = NOW()
                    WHERE id = %s
                """, (
                    tipo, cpf_cnpj, nome_razao_social,
                    data.get('inscricao_estadual') or None,
                    data.get('inscricao_municipal') or None,
                    endereco['rua'], endereco['numero'], endereco.get('complemento') or None,
                    endereco['bairro'], endereco['cidade'], endereco['estado'], cep,
                    existing[0]
                ))
                fiscal_id = existing[0]
            else:
                # Criar novo
                cur.execute("""
                    INSERT INTO dados_fiscais (
                        usuario_id, tipo, cpf_cnpj, nome_razao_social,
                        inscricao_estadual, inscricao_municipal,
                        rua, numero, complemento, bairro, cidade, estado, cep
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    user_data['id'], tipo, cpf_cnpj, nome_razao_social,
                    data.get('inscricao_estadual') or None,
                    data.get('inscricao_municipal') or None,
                    endereco['rua'], endereco['numero'], endereco.get('complemento') or None,
                    endereco['bairro'], endereco['cidade'], endereco['estado'], cep
                ))
                fiscal_id = cur.fetchone()[0]
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            if cur:
                cur.close()
        
        return jsonify({
            "success": True,
            "message": "Dados fiscais salvos com sucesso",
            "fiscal_data_id": fiscal_id
        }), 200
        
    except Exception as e:
        print(f"Erro ao salvar dados fiscais: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor"}), 500

@api_bp.route('/fiscal-data', methods=['DELETE'])
def delete_fiscal_data():
    """Desativa os dados fiscais do usuário."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"erro": "Token de autenticação é obrigatório"}), 401
    
    id_token = auth_header.split(' ')[1]
    
    try:
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({"erro": "Token inválido ou expirado"}), 401
        
        firebase_uid = decoded_token['uid']
        user_data = get_user_by_firebase_uid(firebase_uid)
        if not user_data:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        
        conn = get_db()
        cur = None
        try:
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE dados_fiscais 
                SET ativo = FALSE, atualizado_em = NOW()
                WHERE usuario_id = %s AND ativo = TRUE
            """, (user_data['id'],))
            
            if cur.rowcount == 0:
                return jsonify({"erro": "Dados fiscais não encontrados"}), 404
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            if cur:
                cur.close()
        
        return jsonify({
            "success": True,
            "message": "Dados fiscais removidos com sucesso"
        }), 200
        
    except Exception as e:
        print(f"Erro ao remover dados fiscais: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": "Erro interno do servidor"}), 500

