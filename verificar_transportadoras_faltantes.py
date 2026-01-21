"""
Script para verificar se as transportadoras faltantes estão nos contatos do Bling
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_contact_service import find_contact_in_bling
from blueprints.services.bling_api_service import make_bling_api_request

def limpar_cnpj(cnpj):
    """Remove formatação do CNPJ"""
    if not cnpj:
        return ''
    return re.sub(r'[^0-9]', '', str(cnpj))

def buscar_por_cnpj_e_nome():
    """Busca as transportadoras faltantes por CNPJ e também por nome"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🔍 Buscando Transportadoras Faltantes no Bling")
        print("="*60)
        
        transportadoras_faltantes = [
            {
                'nome': 'Loggi',
                'cnpj_formatado': '24.217.653/0001-95',
                'cnpj_limpo': limpar_cnpj('24.217.653/0001-95'),
                'keywords': ['LOGGI', 'LOGGI']
            },
            {
                'nome': 'JeT Express',
                'cnpj_formatado': '42.584.754/0075-12',
                'cnpj_limpo': limpar_cnpj('42.584.754/0075-12'),
                'keywords': ['JET', 'JET EXPRESS']
            },
            {
                'nome': 'LATAM Cargo',
                'cnpj_formatado': '00.074.635/0001-33',
                'cnpj_limpo': limpar_cnpj('00.074.635/0001-33'),
                'keywords': ['LATAM', 'LATAM CARGO', 'LATAM CARGO EXPRESS']
            }
        ]
        
        resultados = []
        
        for transp in transportadoras_faltantes:
            print(f"\n📦 Buscando: {transp['nome']}")
            print(f"   CNPJ formatado: {transp['cnpj_formatado']}")
            print(f"   CNPJ limpo: {transp['cnpj_limpo']}")
            
            resultado = {
                'nome': transp['nome'],
                'cnpj_formatado': transp['cnpj_formatado'],
                'cnpj_limpo': transp['cnpj_limpo'],
                'encontrado_por_cnpj': False,
                'contato_encontrado': None,
                'encontrado_por_nome': False,
                'contatos_similares': []
            }
            
            # 1. Buscar por CNPJ exato
            print(f"\n   1️⃣  Buscando por CNPJ...")
            try:
                contato = find_contact_in_bling(transp['cnpj_limpo'])
                if contato:
                    resultado['encontrado_por_cnpj'] = True
                    resultado['contato_encontrado'] = contato
                    print(f"      ✅ ENCONTRADO por CNPJ!")
                    print(f"         ID Bling: {contato.get('id')}")
                    print(f"         Nome: {contato.get('nome')}")
                    print(f"         CNPJ: {contato.get('numeroDocumento')}")
                else:
                    print(f"      ❌ Não encontrado por CNPJ")
            except Exception as e:
                print(f"      ⚠️  Erro ao buscar por CNPJ: {e}")
            
            # 2. Buscar por nome/palavras-chave (caso CNPJ seja diferente)
            if not resultado['encontrado_por_cnpj']:
                print(f"\n   2️⃣  Buscando por nome/palavras-chave...")
                try:
                    # Buscar todos os contatos e filtrar por nome
                    pagina = 1
                    limite = 100
                    
                    while pagina <= 5:  # Buscar até 5 páginas
                        response = make_bling_api_request(
                            'GET',
                            '/contatos',
                            params={
                                'pagina': pagina,
                                'limite': limite
                            }
                        )
                        
                        if response.status_code != 200:
                            break
                        
                        data = response.json()
                        contatos = data.get('data', [])
                        
                        if not contatos:
                            break
                        
                        for contato in contatos:
                            nome_contato = contato.get('nome', '').upper()
                            fantasia = contato.get('fantasia', '').upper()
                            cnpj_contato = limpar_cnpj(contato.get('numeroDocumento', ''))
                            
                            # Verificar se contém alguma keyword
                            for keyword in transp['keywords']:
                                if keyword.upper() in nome_contato or keyword.upper() in fantasia:
                                    resultado['contatos_similares'].append({
                                        'id': contato.get('id'),
                                        'nome': contato.get('nome'),
                                        'fantasia': contato.get('fantasia'),
                                        'cnpj': contato.get('numeroDocumento'),
                                        'match': keyword
                                    })
                                    
                                    # Se o CNPJ também corresponder (mesmo com formatação diferente)
                                    if cnpj_contato == transp['cnpj_limpo']:
                                        resultado['encontrado_por_cnpj'] = True
                                        # Buscar detalhes completos
                                        try:
                                            detail_response = make_bling_api_request(
                                                'GET',
                                                f"/contatos/{contato.get('id')}"
                                            )
                                            if detail_response.status_code == 200:
                                                detail_data = detail_response.json()
                                                resultado['contato_encontrado'] = detail_data.get('data', {})
                                        except:
                                            pass
                        
                        if len(contatos) < limite:
                            break
                        
                        pagina += 1
                    
                    if resultado['contatos_similares']:
                        print(f"      ⚠️  Encontrados {len(resultado['contatos_similares'])} contato(s) similar(es):")
                        for similar in resultado['contatos_similares']:
                            print(f"         - {similar['nome']} (Fantasia: {similar['fantasia']})")
                            print(f"           ID: {similar['id']}, CNPJ: {similar['cnpj']}")
                            print(f"           Match: {similar['match']}")
                    else:
                        print(f"      ❌ Nenhum contato similar encontrado")
                        
                except Exception as e:
                    print(f"      ⚠️  Erro ao buscar por nome: {e}")
            
            # Verificar dados completos se encontrado
            if resultado['contato_encontrado']:
                contato = resultado['contato_encontrado']
                endereco = contato.get('endereco', {}).get('geral', {})
                tem_endereco = bool(endereco.get('endereco'))
                tem_ie = bool(contato.get('ie'))
                
                print(f"\n   📋 Dados do contato:")
                print(f"      Endereço completo: {'✅' if tem_endereco else '❌'}")
                print(f"      IE: {'✅' if tem_ie else '❌'}")
                
                if tem_endereco:
                    print(f"      Endereço: {endereco.get('endereco', '')}, {endereco.get('numero', '')}")
                    print(f"      {endereco.get('municipio', '')}/{endereco.get('uf', '')}")
            
            resultados.append(resultado)
        
        # Resumo final
        print("\n" + "="*60)
        print("📊 RESUMO")
        print("="*60)
        
        encontradas = [r for r in resultados if r['encontrado_por_cnpj']]
        nao_encontradas = [r for r in resultados if not r['encontrado_por_cnpj']]
        
        print(f"\n✅ Encontradas por CNPJ: {len(encontradas)}/3")
        print(f"❌ Não encontradas: {len(nao_encontradas)}/3")
        
        if encontradas:
            print(f"\n✅ Transportadoras encontradas:")
            for r in encontradas:
                print(f"   - {r['nome']} (CNPJ: {r['cnpj_formatado']})")
        
        if nao_encontradas:
            print(f"\n❌ Transportadoras NÃO encontradas:")
            for r in nao_encontradas:
                print(f"   - {r['nome']} (CNPJ: {r['cnpj_formatado']})")
                if r['contatos_similares']:
                    print(f"     ⚠️  Mas encontramos contatos similares:")
                    for similar in r['contatos_similares']:
                        print(f"        → {similar['nome']} (CNPJ: {similar['cnpj']})")
                        print(f"          ID Bling: {similar['id']} - Verifique se é a mesma transportadora")
                else:
                    print(f"     💡 Essa transportadora precisa ser cadastrada no Bling")
        
        print("\n" + "="*60)


if __name__ == '__main__':
    buscar_por_cnpj_e_nome()
