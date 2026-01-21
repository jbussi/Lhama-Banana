"""
Script para listar todas as transportadoras cadastradas nos contatos do Bling
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_api_service import make_bling_api_request

def listar_todas_transportadoras():
    """Lista todas as transportadoras nos contatos do Bling"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🔍 Buscando todas as transportadoras nos contatos do Bling")
        print("="*60)
        
        transportadoras_encontradas = []
        pagina = 1
        limite = 100
        
        try:
            while True:
                # Buscar contatos paginados
                response = make_bling_api_request(
                    'GET',
                    '/contatos',
                    params={
                        'pagina': pagina,
                        'limite': limite
                    }
                )
                
                if response.status_code != 200:
                    print(f"\n❌ Erro ao buscar contatos: {response.status_code}")
                    print(response.text)
                    break
                
                data = response.json()
                contatos = data.get('data', [])
                
                if not contatos:
                    break
                
                # Filtrar transportadoras
                for contato in contatos:
                    nome = contato.get('nome', '').upper()
                    tipos_contato = contato.get('tiposContato', [])
                    tipo_pessoa = contato.get('tipo', '')
                    cnpj = contato.get('numeroDocumento', '')
                    
                    # Verificar se é transportadora por tipo de contato ou nome
                    is_transportadora = False
                    
                    # Verificar tipo de contato
                    for tipo in tipos_contato:
                        descricao = tipo.get('descricao', '').upper()
                        if 'TRANSPORT' in descricao or 'FRETE' in descricao:
                            is_transportadora = True
                            break
                    
                    # Verificar por palavras-chave no nome
                    keywords = ['CORREIOS', 'JADLOG', 'LOGGI', 'AZUL', 'LATAM', 'BUSLOG', 'JET', 
                               'TRANSPORTADORA', 'LOGISTICA', 'FRETE', 'ENTREGA']
                    
                    if not is_transportadora:
                        for keyword in keywords:
                            if keyword in nome:
                                is_transportadora = True
                                break
                    
                    # Se é PJ e tem CNPJ, considerar como possível transportadora
                    if tipo_pessoa == 'J' and cnpj and len(cnpj) == 14:
                        # Verificar se é uma das conhecidas ou se o usuário quer incluir
                        if is_transportadora or any(kw in nome for kw in keywords):
                            pass  # Já considerado acima
                    
                    if is_transportadora or (tipo_pessoa == 'J' and cnpj and any(kw in nome for kw in keywords)):
                        # Buscar detalhes completos
                        contato_id = contato.get('id')
                        if contato_id:
                            try:
                                detail_response = make_bling_api_request(
                                    'GET',
                                    f'/contatos/{contato_id}'
                                )
                                if detail_response.status_code == 200:
                                    detail_data = detail_response.json()
                                    contato_completo = detail_data.get('data', {})
                                    if contato_completo:
                                        contato = contato_completo
                            except Exception as e:
                                print(f"⚠️ Erro ao buscar detalhes do contato {contato_id}: {e}")
                        
                        transportadoras_encontradas.append({
                            'id': contato.get('id'),
                            'nome': contato.get('nome'),
                            'fantasia': contato.get('fantasia'),
                            'cnpj': contato.get('numeroDocumento'),
                            'ie': contato.get('ie'),
                            'tipo_pessoa': tipo_pessoa,
                            'tipos_contato': [t.get('descricao') for t in tipos_contato],
                            'telefone': contato.get('telefone'),
                            'email': contato.get('email'),
                            'endereco': contato.get('endereco', {}).get('geral', {})
                        })
                
                # Verificar se há mais páginas
                if len(contatos) < limite:
                    break
                
                pagina += 1
                print(f"📄 Página {pagina-1} processada...")
            
            print(f"\n✅ Total de transportadoras encontradas: {len(transportadoras_encontradas)}\n")
            
            if transportadoras_encontradas:
                print("="*60)
                print("📋 TRANSPORTADORAS CADASTRADAS")
                print("="*60)
                
                for idx, transp in enumerate(transportadoras_encontradas, 1):
                    print(f"\n{idx}. {transp['nome']}")
                    if transp['fantasia']:
                        print(f"   Fantasia: {transp['fantasia']}")
                    print(f"   ID Bling: {transp['id']}")
                    print(f"   CNPJ: {transp['cnpj']}")
                    print(f"   IE: {transp['ie'] or 'Não informado'}")
                    print(f"   Tipos: {', '.join(transp['tipos_contato']) if transp['tipos_contato'] else 'N/A'}")
                    
                    endereco = transp['endereco']
                    if endereco and endereco.get('endereco'):
                        print(f"   Endereço: {endereco.get('endereco', '')}, {endereco.get('numero', '')}")
                        print(f"   {endereco.get('municipio', '')}/{endereco.get('uf', '')}")
                        print(f"   CEP: {endereco.get('cep', 'N/A')}")
                
                # Salvar em JSON para referência
                output_file = 'transportadoras_bling_encontradas.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(transportadoras_encontradas, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"\n💾 Dados salvos em: {output_file}")
            else:
                print("\n⚠️ Nenhuma transportadora encontrada nos contatos do Bling")
            
        except Exception as e:
            print(f"\n❌ Erro ao buscar transportadoras: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    listar_todas_transportadoras()
