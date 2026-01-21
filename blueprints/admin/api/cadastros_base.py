"""
Endpoints para gerenciar cadastros base (categorias, tecidos, estampas, tamanhos)
=====================================================
Esses dados são necessários ANTES de criar produtos
"""
from flask import Blueprint, jsonify, request, current_app
from ...services import get_db
import psycopg2.extras

from flask import Blueprint

cadastros_base_bp = Blueprint('cadastros_base', __name__, url_prefix='/cadastros')


# ==========================================
# CATEGORIAS
# ==========================================

@cadastros_base_bp.route('/categorias', methods=['GET'])
def listar_categorias():
    """Lista todas as categorias"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT id, nome, descricao, ordem_exibicao, ativo, imagem_url
            FROM categorias
            ORDER BY ordem_exibicao, nome
        """)
        
        categorias = [dict(row) for row in cur.fetchall()]
        return jsonify({"categorias": categorias}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar categorias: {e}")
        return jsonify({"erro": "Erro ao listar categorias"}), 500
    finally:
        cur.close()


@cadastros_base_bp.route('/categorias', methods=['POST'])
def criar_categoria():
    """Cria uma nova categoria"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Dados não fornecidos"}), 400
    
    nome = data.get('nome', '').strip()
    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            INSERT INTO categorias (nome, descricao, ordem_exibicao, ativo, imagem_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, nome, descricao, ordem_exibicao, ativo, imagem_url
        """, (
            nome,
            data.get('descricao'),
            data.get('ordem_exibicao', 0),
            data.get('ativo', True),
            data.get('imagem_url')
        ))
        
        categoria = dict(cur.fetchone())
        conn.commit()
        
        return jsonify({
            "mensagem": "Categoria criada com sucesso",
            "categoria": categoria
        }), 201
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'unique' in str(e).lower():
            return jsonify({"erro": "Já existe uma categoria com este nome"}), 400
        return jsonify({"erro": "Erro de integridade: " + str(e)}), 400
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar categoria: {e}")
        return jsonify({"erro": "Erro ao criar categoria"}), 500
    finally:
        cur.close()


# ==========================================
# TECIDOS
# ==========================================

@cadastros_base_bp.route('/tecidos', methods=['GET'])
def listar_tecidos():
    """Lista todos os tecidos"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT id, nome, descricao, ordem_exibicao, ativo
            FROM tecidos
            ORDER BY ordem_exibicao, nome
        """)
        
        tecidos = [dict(row) for row in cur.fetchall()]
        return jsonify({"tecidos": tecidos}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar tecidos: {e}")
        return jsonify({"erro": "Erro ao listar tecidos"}), 500
    finally:
        cur.close()


@cadastros_base_bp.route('/tecidos', methods=['POST'])
def criar_tecido():
    """Cria um novo tecido"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Dados não fornecidos"}), 400
    
    nome = data.get('nome', '').strip()
    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            INSERT INTO tecidos (nome, descricao, ordem_exibicao, ativo)
            VALUES (%s, %s, %s, %s)
            RETURNING id, nome, descricao, ordem_exibicao, ativo
        """, (
            nome,
            data.get('descricao'),
            data.get('ordem_exibicao', 0),
            data.get('ativo', True)
        ))
        
        tecido = dict(cur.fetchone())
        conn.commit()
        
        return jsonify({
            "mensagem": "Tecido criado com sucesso",
            "tecido": tecido
        }), 201
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'unique' in str(e).lower():
            return jsonify({"erro": "Já existe um tecido com este nome"}), 400
        return jsonify({"erro": "Erro de integridade: " + str(e)}), 400
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar tecido: {e}")
        return jsonify({"erro": "Erro ao criar tecido"}), 500
    finally:
        cur.close()


# ==========================================
# TAMANHOS
# ==========================================

@cadastros_base_bp.route('/tamanhos', methods=['GET'])
def listar_tamanhos():
    """Lista todos os tamanhos"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT id, nome, ordem_exibicao, ativo
            FROM tamanho
            ORDER BY ordem_exibicao, nome
        """)
        
        tamanhos = [dict(row) for row in cur.fetchall()]
        return jsonify({"tamanhos": tamanhos}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar tamanhos: {e}")
        return jsonify({"erro": "Erro ao listar tamanhos"}), 500
    finally:
        cur.close()


@cadastros_base_bp.route('/tamanhos', methods=['POST'])
def criar_tamanho():
    """Cria um novo tamanho"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Dados não fornecidos"}), 400
    
    nome = data.get('nome', '').strip()
    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            INSERT INTO tamanho (nome, ordem_exibicao, ativo)
            VALUES (%s, %s, %s)
            RETURNING id, nome, ordem_exibicao, ativo
        """, (
            nome,
            data.get('ordem_exibicao', 0),
            data.get('ativo', True)
        ))
        
        tamanho = dict(cur.fetchone())
        conn.commit()
        
        return jsonify({
            "mensagem": "Tamanho criado com sucesso",
            "tamanho": tamanho
        }), 201
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'unique' in str(e).lower():
            return jsonify({"erro": "Já existe um tamanho com este nome"}), 400
        return jsonify({"erro": "Erro de integridade: " + str(e)}), 400
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar tamanho: {e}")
        return jsonify({"erro": "Erro ao criar tamanho"}), 500
    finally:
        cur.close()


# ==========================================
# ESTAMPAS
# ==========================================

@cadastros_base_bp.route('/estampas', methods=['GET'])
def listar_estampas():
    """Lista todas as estampas"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                e.id, e.nome, e.descricao, e.imagem_url,
                e.sexo, e.custo_por_metro, e.ordem_exibicao, e.ativo,
                c.id as categoria_id, c.nome as categoria_nome,
                t.id as tecido_id, t.nome as tecido_nome
            FROM estampa e
            JOIN categorias c ON e.categoria_id = c.id
            LEFT JOIN tecidos t ON e.tecido_id = t.id
            ORDER BY e.ordem_exibicao, e.nome
        """)
        
        estampas = []
        for row in cur.fetchall():
            estampa = dict(row)
            estampas.append(estampa)
        
        return jsonify({"estampas": estampas}), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar estampas: {e}")
        return jsonify({"erro": "Erro ao listar estampas"}), 500
    finally:
        cur.close()


@cadastros_base_bp.route('/estampas', methods=['POST'])
def criar_estampa():
    """Cria uma nova estampa"""
    conn = get_db()
    if not conn:
        return jsonify({"erro": "Erro de conexão com o banco de dados."}), 500
    
    data = request.get_json()
    if not data:
        return jsonify({"erro": "Dados não fornecidos"}), 400
    
    nome = data.get('nome', '').strip()
    categoria_id = data.get('categoria_id')
    imagem_url = data.get('imagem_url', '').strip()
    custo_por_metro = data.get('custo_por_metro')
    
    # Validações
    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if not categoria_id:
        return jsonify({"erro": "Categoria é obrigatória"}), 400
    if not imagem_url:
        return jsonify({"erro": "URL da imagem é obrigatória"}), 400
    if custo_por_metro is None or float(custo_por_metro) < 0:
        return jsonify({"erro": "Custo por metro deve ser maior ou igual a zero"}), 400
    
    sexo = data.get('sexo', 'u').lower()
    if sexo not in ['m', 'f', 'u']:
        sexo = 'u'
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            INSERT INTO estampa (
                nome, descricao, imagem_url, categoria_id, tecido_id,
                sexo, custo_por_metro, ordem_exibicao, ativo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, nome, descricao, imagem_url, categoria_id, tecido_id,
                      sexo, custo_por_metro, ordem_exibicao, ativo
        """, (
            nome,
            data.get('descricao'),
            imagem_url,
            categoria_id,
            data.get('tecido_id'),  # Opcional
            sexo,
            float(custo_por_metro),
            data.get('ordem_exibicao', 0),
            data.get('ativo', True)
        ))
        
        estampa = dict(cur.fetchone())
        conn.commit()
        
        return jsonify({
            "mensagem": "Estampa criada com sucesso",
            "estampa": estampa
        }), 201
        
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'unique' in str(e).lower():
            return jsonify({"erro": "Já existe uma estampa com este nome"}), 400
        if 'foreign key' in str(e).lower():
            return jsonify({"erro": "Categoria ou tecido não encontrado"}), 400
        return jsonify({"erro": "Erro de integridade: " + str(e)}), 400
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Erro ao criar estampa: {e}")
        return jsonify({"erro": "Erro ao criar estampa"}), 500
    finally:
        cur.close()
