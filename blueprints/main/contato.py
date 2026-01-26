from flask import render_template, session, current_app, request, flash, redirect, url_for
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

@main_bp.route('/contato', methods=['GET', 'POST'])
def contato_page():
    """Renderiza a página de contato com conteúdo dinâmico do banco de dados"""
    if request.method == 'POST':
        # Processar formulário de contato (se necessário)
        flash('Mensagem enviada com sucesso! Entraremos em contato em breve.', 'success')
        return redirect(url_for('main.contato_page'))
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar conteúdo de contato
        cur.execute("""
            SELECT 
                titulo,
                texto_principal,
                informacoes,
                links
            FROM conteudo_contato
            WHERE ativo = TRUE
            ORDER BY id DESC
            LIMIT 1
        """)
        
        conteudo = cur.fetchone()
        
        if conteudo:
            contato_data = {
                'titulo': conteudo.get('titulo') or 'Entre em Contato',
                'texto_principal': conteudo.get('texto_principal') or '',
                'informacoes': parse_json_field(conteudo.get('informacoes')),
                'links': parse_json_field(conteudo.get('links'))
            }
        else:
            contato_data = {
                'titulo': 'Entre em Contato',
                'texto_principal': '',
                'informacoes': [],
                'links': {}
            }
        
        return render_template(
            'contato.html',
            user=session.get('username'),
            contato=contato_data
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar conteúdo de contato: {e}", exc_info=True)
        return render_template(
            'contato.html',
            user=session.get('username'),
            contato={
                'titulo': 'Entre em Contato',
                'texto_principal': '',
                'informacoes': [],
                'links': {}
            }
        )
    finally:
        cur.close()