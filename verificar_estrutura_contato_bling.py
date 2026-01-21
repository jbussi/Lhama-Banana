"""
Script para verificar a estrutura completa do contato retornado pelo Bling
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_contact_service import find_contact_in_bling

def verificar_estrutura():
    app = create_app()
    
    with app.app_context():
        cnpj = "34028316000103"  # Correios
        
        print("="*60)
        print("🔍 Verificando estrutura do contato do Bling")
        print("="*60)
        
        contato = find_contact_in_bling(cnpj)
        
        if contato:
            print("\n✅ Contato encontrado!")
            print("\n📋 Estrutura completa retornada:")
            print(json.dumps(contato, indent=2, ensure_ascii=False, default=str))
            
            print("\n" + "="*60)
            print("📍 Estrutura do Endereço:")
            print("="*60)
            
            endereco = contato.get('endereco')
            if endereco:
                print(f"\nTipo: {type(endereco)}")
                print(f"Conteúdo: {json.dumps(endereco, indent=2, ensure_ascii=False, default=str)}")
                
                # Verificar diferentes possibilidades
                print("\n🔍 Verificando campos:")
                print(f"  - 'geral': {endereco.get('geral') if isinstance(endereco, dict) else 'N/A'}")
                print(f"  - 'cobranca': {endereco.get('cobranca') if isinstance(endereco, dict) else 'N/A'}")
                print(f"  - Direto no objeto: {endereco.get('endereco') if isinstance(endereco, dict) else 'N/A'}")
            else:
                print("\n❌ Campo 'endereco' não encontrado no contato")
        else:
            print("\n❌ Contato não encontrado")

if __name__ == '__main__':
    verificar_estrutura()
