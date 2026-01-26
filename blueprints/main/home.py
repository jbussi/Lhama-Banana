from flask import render_template, session, redirect, url_for, current_app
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

@main_bp.route('/')
@main_bp.route('/home')
def home():
    """Renderiza a página home com conteúdo dinâmico do banco de dados"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar conteúdo da home
        cur.execute("""
            SELECT 
                hero_titulo,
                hero_subtitulo,
                hero_imagem_url,
                hero_texto_botao,
                carrosseis,
                depoimentos,
                estatisticas_clientes,
                estatisticas_pecas,
                estatisticas_anos
            FROM conteudo_home
            WHERE ativo = TRUE
            ORDER BY id DESC
            LIMIT 1
        """)
        
        conteudo = cur.fetchone()
        
        # Se não encontrar, usar valores padrão
        if conteudo:
            hero_data = {
                'titulo': conteudo.get('hero_titulo') or 'Noites tranquilas, sorrisos garantidos!',
                'subtitulo': conteudo.get('hero_subtitulo') or 'Somos uma marca feita por famílias, para famílias. Aqui você encontra qualidade, conforto e muito carinho em cada detalhe.',
                'imagem_url': conteudo.get('hero_imagem_url'),
                'texto_botao': conteudo.get('hero_texto_botao') or 'Comprar Agora'
            }
            
            # Parsear JSON dos carrosséis e depoimentos
            carrosseis = parse_json_field(conteudo.get('carrosseis'))
            depoimentos = parse_json_field(conteudo.get('depoimentos'))
            # Filtrar apenas depoimentos ativos e ordenar
            depoimentos = [d for d in depoimentos if d.get('ativo', True)]
            depoimentos.sort(key=lambda x: x.get('ordem', 0))
            
            # Estatísticas
            estatisticas = {
                'clientes': conteudo.get('estatisticas_clientes') or 5000,
                'pecas': conteudo.get('estatisticas_pecas') or 10000,
                'anos': conteudo.get('estatisticas_anos') or 5
            }
        else:
            # Valores padrão
            hero_data = {
                'titulo': 'Noites tranquilas, sorrisos garantidos!',
                'subtitulo': 'Somos uma marca feita por famílias, para famílias. Aqui você encontra qualidade, conforto e muito carinho em cada detalhe.',
                'imagem_url': None,
                'texto_botao': 'Comprar Agora'
            }
            carrosseis = []
            depoimentos = []
            estatisticas = {
                'clientes': 5000,
                'pecas': 10000,
                'anos': 5
            }
        
        # Buscar informações da empresa (contato, valores)
        cur.execute("""
            SELECT 
                email,
                telefone,
                whatsapp,
                horario_atendimento,
                valores,
                redes_sociais
            FROM informacoes_empresa
            WHERE ativo = TRUE
            ORDER BY id DESC
            LIMIT 1
        """)
        
        info_empresa = cur.fetchone()
        
        if info_empresa:
            empresa_data = {
                'email': info_empresa.get('email'),
                'telefone': info_empresa.get('telefone'),
                'whatsapp': info_empresa.get('whatsapp'),
                'horario_atendimento': info_empresa.get('horario_atendimento'),
                'valores': parse_json_field(info_empresa.get('valores')),
                'redes_sociais': parse_json_field(info_empresa.get('redes_sociais'))
            }
        else:
            empresa_data = {
                'email': None,
                'telefone': None,
                'whatsapp': None,
                'horario_atendimento': None,
                'valores': [],
                'redes_sociais': {}
            }
        
        return render_template(
            'home.html',
            user=session.get('uid'),
            hero=hero_data,
            carrosseis=carrosseis,
            depoimentos=depoimentos,
            empresa=empresa_data,
            estatisticas=estatisticas
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar conteúdo da home: {e}", exc_info=True)
        # Em caso de erro, usar valores padrão
        return render_template(
            'home.html',
            user=session.get('uid'),
            hero={
                'titulo': 'Noites tranquilas, sorrisos garantidos!',
                'subtitulo': 'Somos uma marca feita por famílias, para famílias. Aqui você encontra qualidade, conforto e muito carinho em cada detalhe.',
                'imagem_url': None,
                'texto_botao': 'Comprar Agora'
            },
            carrosseis=[],
            depoimentos=[],
            empresa={
                'email': None,
                'telefone': None,
                'whatsapp': None,
                'horario_atendimento': None,
                'valores': [],
                'redes_sociais': {}
            },
            estatisticas={
                'clientes': 5000,
                'pecas': 10000,
                'anos': 5
            }
        )
    finally:
        cur.close()

@main_bp.route('/loja')
def loja_page():
    return redirect(url_for('produtos.produtos_page'))