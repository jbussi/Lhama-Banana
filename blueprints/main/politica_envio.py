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

@main_bp.route('/politica-envio')
@main_bp.route('/envio')
def politica_envio():
    """Renderiza a página de política de envio com conteúdo dinâmico do banco de dados"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar conteúdo da política
        cur.execute("""
            SELECT 
                titulo,
                ultima_atualizacao,
                conteudo,
                secoes
            FROM site_politica_envio
            ORDER BY updated_at DESC
            LIMIT 1
        """)
        
        conteudo = cur.fetchone()
        
        if conteudo:
            politica_data = {
                'titulo': conteudo.get('titulo') or 'Política de Envio',
                'ultima_atualizacao': conteudo.get('ultima_atualizacao'),
                'conteudo': conteudo.get('conteudo') or '',
                'secoes': parse_json_field(conteudo.get('secoes'))
            }
            # Ordenar seções por ordem
            if politica_data['secoes']:
                politica_data['secoes'].sort(key=lambda x: x.get('ordem', 0))
        else:
            politica_data = {
                'titulo': 'Política de Envio',
                'ultima_atualizacao': None,
                'conteudo': '',
                'secoes': []
            }
        
        return render_template(
            'politica_envio.html',
            user=session.get('uid'),
            politica=politica_data
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar política de envio: {e}", exc_info=True)
        return render_template(
            'politica_envio.html',
            user=session.get('uid'),
            politica={
                'titulo': 'Política de Envio',
                'ultima_atualizacao': None,
                'conteudo': '',
                'secoes': []
            }
        )
    finally:
        cur.close()
