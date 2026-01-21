"""
Teste final: Verificar se todas as transportadoras (incluindo as faltantes) são reconhecidas
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_contact_service import find_contact_in_bling
import re

def limpar_cnpj(cnpj):
    """Remove formatação do CNPJ"""
    if not cnpj:
        return ''
    return re.sub(r'[^0-9]', '', str(cnpj))

def testar_todas():
    """Testa todas as transportadoras"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🧪 TESTE FINAL: Reconhecimento de TODAS as Transportadoras")
        print("="*60)
        
        # Lista completa de todas as transportadoras
        todas_transportadoras = [
            {'nome': 'BUSLOG', 'cnpj': '10992167000130'},
            {'nome': 'Azul Cargo Express', 'cnpj': '09296295000160'},
            {'nome': 'JADLOG', 'cnpj': '04884082000135'},
            {'nome': 'Correios', 'cnpj': '34028316000103'},
            {'nome': 'Loggi', 'cnpj': '24217653000195'},
            {'nome': 'JeT Express', 'cnpj': '42584754007512'},
            {'nome': 'LATAM Cargo', 'cnpj': '00074635000133'},
        ]
        
        print(f"\n📦 Testando {len(todas_transportadoras)} transportadoras...\n")
        
        resultados = {
            'encontradas': [],
            'nao_encontradas': []
        }
        
        for idx, transp in enumerate(todas_transportadoras, 1):
            nome = transp['nome']
            cnpj = transp['cnpj']
            cnpj_limpo = limpar_cnpj(cnpj)
            
            print(f"{idx}. {nome}")
            print(f"   CNPJ: {cnpj_limpo}")
            
            try:
                contato = find_contact_in_bling(cnpj_limpo)
                
                if contato:
                    encontrado_id = contato.get('id')
                    encontrado_nome = contato.get('nome')
                    
                    # Verificar dados completos
                    endereco = contato.get('endereco', {}).get('geral', {})
                    tem_endereco = bool(endereco.get('endereco'))
                    tem_ie = bool(contato.get('ie'))
                    
                    print(f"   ✅ ENCONTRADO! (ID: {encontrado_id})")
                    print(f"   Nome no Bling: {encontrado_nome}")
                    print(f"   Endereço: {'✅' if tem_endereco else '❌'}")
                    print(f"   IE: {'✅' if tem_ie else '❌'}")
                    
                    if tem_endereco:
                        print(f"   Endereço completo: {endereco.get('endereco', '')}, {endereco.get('numero', '')}")
                        print(f"   {endereco.get('municipio', '')}/{endereco.get('uf', '')}")
                    
                    resultados['encontradas'].append({
                        'nome': nome,
                        'cnpj': cnpj_limpo,
                        'id': encontrado_id,
                        'nome_bling': encontrado_nome,
                        'dados_completos': tem_endereco and tem_ie
                    })
                else:
                    print(f"   ❌ NÃO ENCONTRADO")
                    resultados['nao_encontradas'].append({
                        'nome': nome,
                        'cnpj': cnpj_limpo
                    })
            except Exception as e:
                print(f"   ❌ ERRO: {e}")
                resultados['nao_encontradas'].append({
                    'nome': nome,
                    'cnpj': cnpj_limpo,
                    'erro': str(e)
                })
            
            print()
        
        # Resumo
        print("="*60)
        print("📊 RESUMO FINAL")
        print("="*60)
        
        total = len(todas_transportadoras)
        encontradas = len(resultados['encontradas'])
        nao_encontradas = len(resultados['nao_encontradas'])
        completas = len([r for r in resultados['encontradas'] if r['dados_completos']])
        
        print(f"\n✅ Total: {total} transportadoras")
        print(f"✅ Encontradas: {encontradas}/{total}")
        print(f"✅ Com dados completos: {completas}/{encontradas}")
        print(f"❌ Não encontradas: {nao_encontradas}/{total}")
        
        if encontradas == total and completas == encontradas:
            print(f"\n🎉 PERFEITO! TODAS AS TRANSPORTADORAS ESTÃO PRONTAS!")
            print(f"   O sistema reconhecerá todas as {total} transportadoras na emissão de NF-e.")
        elif encontradas == total:
            print(f"\n⚠️  Todas foram encontradas, mas algumas têm dados incompletos.")
        else:
            print(f"\n❌ Algumas transportadoras não foram encontradas.")
        
        print("\n✅ Transportadoras reconhecidas:")
        for r in resultados['encontradas']:
            status = "✅ Completa" if r['dados_completos'] else "⚠️  Incompleta"
            print(f"   {r['nome']:25} → {r['nome_bling']:40} ({status})")
        
        if resultados['nao_encontradas']:
            print("\n❌ Transportadoras NÃO encontradas:")
            for r in resultados['nao_encontradas']:
                print(f"   {r['nome']} (CNPJ: {r['cnpj']})")
        
        print("="*60)
        
        # Salvar lista completa atualizada
        output_file = 'transportadoras_completas.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resultados['encontradas'], f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Lista completa salva em: {output_file}")


if __name__ == '__main__':
    testar_todas()
