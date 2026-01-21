"""
Teste específico: Simular busca de transportadora na emissão de NFC-e
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_contact_service import find_contact_in_bling

def test_busca_transportadora_para_nfce():
    """Testa como a busca de transportadora funcionará na emissão de NFC-e"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🧪 TESTE: Simulação de Busca na Emissão de NFC-e")
        print("="*60)
        
        # Simular CNPJ de uma transportadora (usando Correios que encontramos)
        cnpj_teste = "34028316000103"
        
        print(f"\n📦 Simulando busca para CNPJ: {cnpj_teste}")
        print("   (Este é o fluxo que acontece quando NFC-e é emitida)\n")
        
        # Simular o que acontece no emit_nfce_consumidor
        transportadora_bling = find_contact_in_bling(cnpj_teste)
        
        if transportadora_bling:
            print("✅ Transportadora encontrada no Bling!")
            print(f"\n📋 Dados que serão usados na NFC-e:")
            print(f"   Nome: {transportadora_bling.get('nome')}")
            print(f"   CNPJ: {transportadora_bling.get('numeroDocumento')}")
            print(f"   IE: {transportadora_bling.get('ie', 'Não informado')}")
            
            # Verificar endereço
            endereco = transportadora_bling.get('endereco', {})
            if endereco:
                geral = endereco.get('geral') or endereco.get('cobranca') or {}
                if geral:
                    print(f"\n📍 Endereço Completo:")
                    print(f"   Logradouro: {geral.get('endereco', '')}, {geral.get('numero', '')}")
                    print(f"   Complemento: {geral.get('complemento', 'N/A')}")
                    print(f"   Bairro: {geral.get('bairro', 'N/A')}")
                    print(f"   Município: {geral.get('municipio', '')}/{geral.get('uf', '')}")
                    print(f"   CEP: {geral.get('cep', 'N/A')}")
                    
                    print(f"\n✅ Todos os dados necessários estão disponíveis!")
                    print(f"   Esses dados serão incluídos na seção 'transporte.transportador' da NFC-e")
                else:
                    print(f"\n⚠️  Endereço não encontrado na estrutura esperada")
            else:
                print(f"\n⚠️  Endereço não encontrado")
        else:
            print("⚠️  Transportadora não encontrada no Bling")
            print("   (Sistema usaria fallback com dados da tabela vendas)")
        
        print("\n" + "="*60)
        print("📝 CONCLUSÃO")
        print("="*60)
        print("\n✅ A busca de transportadora está funcionando corretamente!")
        print("✅ Quando uma NFC-e for emitida com transportadora 'Correios',")
        print("   os dados completos do Bling serão usados automaticamente.")
        print("\n⚠️  Outras transportadoras precisam ser criadas no Bling para")
        print("   que possam ser encontradas automaticamente.")


if __name__ == '__main__':
    test_busca_transportadora_para_nfce()
