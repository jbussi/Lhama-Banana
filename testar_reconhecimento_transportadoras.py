"""
Script para testar se todas as transportadoras do Bling são reconhecidas corretamente
"""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_contact_service import find_contact_in_bling

def limpar_cnpj(cnpj):
    """Remove formatação do CNPJ"""
    if not cnpj:
        return ''
    return re.sub(r'[^0-9]', '', str(cnpj))

def testar_reconhecimento():
    """Testa se todas as transportadoras são encontradas pelo sistema"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🧪 TESTE: Reconhecimento de Transportadoras na Emissão de NF-e")
        print("="*60)
        
        # Carregar transportadoras encontradas
        try:
            with open('transportadoras_bling_encontradas.json', 'r', encoding='utf-8') as f:
                transportadoras = json.load(f)
        except FileNotFoundError:
            print("\n❌ Arquivo transportadoras_bling_encontradas.json não encontrado!")
            print("   Execute primeiro: python listar_transportadoras_bling.py")
            return
        
        print(f"\n📦 Testando {len(transportadoras)} transportadoras...\n")
        
        resultados = {
            'encontradas': [],
            'nao_encontradas': []
        }
        
        for idx, transp in enumerate(transportadoras, 1):
            nome = transp['nome']
            cnpj = transp['cnpj']
            cnpj_limpo = limpar_cnpj(cnpj)
            
            print(f"{idx}. Testando: {nome}")
            print(f"   CNPJ: {cnpj} (limpo: {cnpj_limpo})")
            
            # Testar busca (como acontece na emissão de NF-e)
            try:
                contato_encontrado = find_contact_in_bling(cnpj_limpo)
                
                if contato_encontrado:
                    encontrado_id = contato_encontrado.get('id')
                    encontrado_nome = contato_encontrado.get('nome')
                    encontrado_cnpj = limpar_cnpj(contato_encontrado.get('numeroDocumento'))
                    
                    # Verificar se é o mesmo contato
                    if encontrado_id == transp['id']:
                        print(f"   ✅ ENCONTRADO! (ID: {encontrado_id})")
                        print(f"   Nome: {encontrado_nome}")
                        
                        # Verificar dados completos
                        tem_endereco = bool(contato_encontrado.get('endereco', {}).get('geral', {}).get('endereco'))
                        tem_ie = bool(contato_encontrado.get('ie'))
                        
                        print(f"   Endereço completo: {'✅' if tem_endereco else '❌'}")
                        print(f"   IE: {'✅' if tem_ie else '❌'}")
                        
                        resultados['encontradas'].append({
                            'nome': nome,
                            'cnpj': cnpj_limpo,
                            'id': encontrado_id,
                            'dados_completos': tem_endereco and tem_ie
                        })
                    else:
                        print(f"   ⚠️  Encontrado contato diferente! (ID: {encontrado_id} vs esperado: {transp['id']})")
                        resultados['nao_encontradas'].append({
                            'nome': nome,
                            'cnpj': cnpj_limpo,
                            'motivo': 'CNPJ encontrado pertence a outro contato'
                        })
                else:
                    print(f"   ❌ NÃO ENCONTRADO!")
                    resultados['nao_encontradas'].append({
                        'nome': nome,
                        'cnpj': cnpj_limpo,
                        'motivo': 'Contato não encontrado no Bling'
                    })
            except Exception as e:
                print(f"   ❌ ERRO: {e}")
                resultados['nao_encontradas'].append({
                    'nome': nome,
                    'cnpj': cnpj_limpo,
                    'motivo': f'Erro na busca: {str(e)}'
                })
            
            print()
        
        # Resumo
        print("="*60)
        print("📊 RESUMO DOS TESTES")
        print("="*60)
        
        total = len(transportadoras)
        encontradas = len(resultados['encontradas'])
        nao_encontradas = len(resultados['nao_encontradas'])
        completas = len([r for r in resultados['encontradas'] if r['dados_completos']])
        
        print(f"\n✅ Encontradas: {encontradas}/{total}")
        print(f"✅ Com dados completos: {completas}/{encontradas}")
        print(f"❌ Não encontradas: {nao_encontradas}/{total}")
        
        if resultados['encontradas']:
            print(f"\n✅ Transportadoras que SERÃO reconhecidas na emissão de NF-e:")
            for r in resultados['encontradas']:
                status = "✅ Completa" if r['dados_completos'] else "⚠️  Incompleta"
                print(f"   - {r['nome']} (CNPJ: {r['cnpj']}) - {status}")
        
        if resultados['nao_encontradas']:
            print(f"\n❌ Transportadoras que NÃO serão reconhecidas:")
            for r in resultados['nao_encontradas']:
                print(f"   - {r['nome']} (CNPJ: {r['cnpj']})")
                print(f"     Motivo: {r['motivo']}")
        
        # Verificar se todas têm dados completos
        print("\n" + "="*60)
        if encontradas == total and completas == encontradas:
            print("✅ TODAS AS TRANSPORTADORAS ESTÃO PRONTAS!")
            print("   O sistema reconhecerá todas na emissão de NF-e.")
        elif encontradas == total:
            print("⚠️  ATENÇÃO!")
            print("   Todas foram encontradas, mas algumas têm dados incompletos.")
            print("   Verifique IE e endereço no Bling.")
        else:
            print("❌ PROBLEMA DETECTADO!")
            print("   Algumas transportadoras não estão sendo encontradas.")
            print("   Verifique os CNPJs cadastrados.")
        
        print("="*60)


if __name__ == '__main__':
    testar_reconhecimento()
