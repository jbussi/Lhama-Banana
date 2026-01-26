from flask import render_template, session, current_app
from ..services import get_db
import psycopg2.extras
import json
from . import main_bp

def parse_json_field(field):
    """Helper para parsear campos JSON"""
    if not field:
        return [] if isinstance(field, list) else {}
    if isinstance(field, str):
        try:
            return json.loads(field)
        except:
            return [] if '[' in field else {}
    return field

@main_bp.route('/sobre-nos')
@main_bp.route('/sobre')
def sobre_nos():
    """Renderiza a página sobre nós com conteúdo dinâmico do banco de dados"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar conteúdo sobre
        cur.execute("""
            SELECT 
                historia_titulo,
                historia_conteudo,
                valores_titulo,
                valores_conteudo,
                equipe_titulo,
                equipe_conteudo
            FROM conteudo_sobre
            WHERE ativo = TRUE
            ORDER BY id DESC
            LIMIT 1
        """)
        
        conteudo = cur.fetchone()
        
        if conteudo:
            sobre_data = {
                'historia_titulo': conteudo.get('historia_titulo') or 'Nossa História',
                'historia_conteudo': conteudo.get('historia_conteudo') or '',
                'valores_titulo': conteudo.get('valores_titulo') or 'Nossos Valores',
                'valores': parse_json_field(conteudo.get('valores_conteudo')),
                'equipe_titulo': conteudo.get('equipe_titulo') or 'Nossa Equipe',
                'equipe': parse_json_field(conteudo.get('equipe_conteudo'))
            }
        else:
            sobre_data = {
                'historia_titulo': 'Nossa História',
                'historia_conteudo': '',
                'valores_titulo': 'Nossos Valores',
                'valores': [],
                'equipe_titulo': 'Nossa Equipe',
                'equipe': []
            }
        
        return render_template(
            'sobre_nos.html',
            user=session.get('uid'),
            sobre=sobre_data
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar conteúdo sobre: {e}", exc_info=True)
        return render_template(
            'sobre_nos.html',
            user=session.get('uid'),
            sobre={
                'historia_titulo': 'Nossa História',
                'historia_conteudo': '',
                'valores_titulo': 'Nossos Valores',
                'valores': [],
                'equipe_titulo': 'Nossa Equipe',
                'equipe': []
            }
        )
    finally:
        cur.close()