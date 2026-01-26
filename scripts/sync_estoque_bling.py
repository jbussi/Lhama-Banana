#!/usr/bin/env python3
"""
Script para sincronizar estoque do Bling para o banco local
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from blueprints.services.bling_product_service import sync_stock_from_bling

def main():
    """Sincroniza estoque do Bling para o banco local"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Sincronizando estoque do Bling para o banco local...")
        print("=" * 60)
        
        # Sincronizar todos os produtos
        result = sync_stock_from_bling(produto_id=None)
        
        if result.get('success') or (isinstance(result.get('success'), int) and result.get('success', 0) > 0):
            success_count = result.get('success', 0) if isinstance(result.get('success'), int) else len([r for r in result.get('results', []) if r.get('success')])
            total = result.get('total', 0)
            errors = result.get('errors', 0)
            
            print(f"✅ Sincronização concluída!")
            print(f"   Total de produtos: {total}")
            print(f"   Sincronizados com sucesso: {success_count}")
            print(f"   Erros: {errors}")
            
            if result.get('results'):
                print("\n📦 Produtos sincronizados:")
                for r in result.get('results', []):
                    if r.get('success'):
                        print(f"   - Produto ID {r.get('produto_id')}: Estoque = {r.get('estoque_novo', 'N/A')}")
            
            if errors > 0:
                print("\n⚠️  Alguns produtos tiveram erros:")
                for r in result.get('results', []):
                    if not r.get('success'):
                        print(f"   - Produto ID {r.get('produto_id')}: {r.get('error', 'Erro desconhecido')}")
        else:
            print(f"❌ Erro na sincronização: {result.get('error', 'Erro desconhecido')}")
            return 1
        
        print("=" * 60)
        return 0

if __name__ == '__main__':
    sys.exit(main())
