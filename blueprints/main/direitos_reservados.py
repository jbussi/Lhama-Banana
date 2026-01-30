from flask import render_template, session, current_app
from ..services import get_db
import psycopg2.extras
import json
from . import main_bp

def parse_json_field(field):
    """Helper para parsear campos JSON"""
    if not field:
        return []
    if isinstance(field, str):
        try:
            return json.loads(field)
        except:
            return []
    return field

@main_bp.route('/direitos-reservados')
@main_bp.route('/direitos')
def direitos_reservados():
    """Renderiza a página de direitos reservados com conteúdo dinâmico do banco de dados"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar conteúdo
        cur.execute("""
            SELECT 
                titulo,
                ultima_atualizacao,
                conteudo,
                secoes
            FROM site_direitos_reservados
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        
        conteudo = cur.fetchone()
        
        if conteudo:
            direitos_data = {
                'titulo': conteudo.get('titulo') or 'Todos os Direitos Reservados',
                'ultima_atualizacao': conteudo.get('ultima_atualizacao'),
                'conteudo': conteudo.get('conteudo') or '',
                'secoes': parse_json_field(conteudo.get('secoes'))
            }
            # Ordenar seções por ordem
            if direitos_data['secoes']:
                direitos_data['secoes'].sort(key=lambda x: x.get('ordem', 0))
        else:
            direitos_data = {
                'titulo': 'Todos os Direitos Reservados',
                'ultima_atualizacao': None,
                'conteudo': '',
                'secoes': []
            }
        
        return render_template(
            'direitos_reservados.html',
            user=session.get('uid'),
            direitos=direitos_data
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar direitos reservados: {e}", exc_info=True)
        return render_template(
            'direitos_reservados.html',
            user=session.get('uid'),
            direitos={
                'titulo': 'Todos os Direitos Reservados',
                'ultima_atualizacao': None,
                'conteudo': '',
                'secoes': []
            }
        )
    finally:
        cur.close()
