#!/usr/bin/env python3
"""
Script de teste para sincronização de produtos com Bling
"""
import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def test_sync_product(produto_id: int):
    """Testa sincronização de um produto"""
    app = create_app()
    
    with app.app_context():
        from blueprints.services.bling_product_service import sync_product_to_bling
        
        print(f"\n🔄 Testando sincronização do produto ID: {produto_id}")
        print("=" * 60)
        
        try:
            result = sync_product_to_bling(produto_id)
            
            print("\n📊 Resultado:")
            print(f"  Success: {result.get('success')}")
            print(f"  Action: {result.get('action')}")
            
            if result.get('success'):
                print(f"  ✅ Bling ID: {result.get('bling_id')}")
                print(f"  ✅ Mensagem: {result.get('message')}")
            else:
                print(f"  ❌ Erro: {result.get('error')}")
                if result.get('details'):
                    print(f"  📋 Detalhes:")
                    for detail in result.get('details', []):
                        print(f"     - {detail}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Erro na sincronização: {e}")
            import traceback
            traceback.print_exc()
            return None

def test_get_product_status(produto_id: int):
    """Verifica status de sincronização"""
    app = create_app()
    
    with app.app_context():
        from blueprints.services.bling_product_service import get_bling_product_by_local_id
        
        print(f"\n📋 Verificando status do produto ID: {produto_id}")
        print("=" * 60)
        
        try:
            bling_produto = get_bling_product_by_local_id(produto_id)
            
            if bling_produto:
                print("\n✅ Produto sincronizado:")
                print(f"  Bling ID: {bling_produto['bling_id']}")
                print(f"  Bling Código: {bling_produto['bling_codigo']}")
                print(f"  Status: {bling_produto['status_sincronizacao']}")
                print(f"  Última sincronização: {bling_produto.get('ultima_sincronizacao')}")
                if bling_produto.get('erro_ultima_sync'):
                    print(f"  ⚠️  Erro: {bling_produto['erro_ultima_sync']}")
            else:
                print("\n⚠️  Produto não sincronizado ainda")
            
            return bling_produto
            
        except Exception as e:
            print(f"\n❌ Erro ao verificar status: {e}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    produto_id = 6
    
    print("🧪 Teste de Sincronização Bling - LhamaBanana")
    print("=" * 60)
    
    # Testar sincronização
    result = test_sync_product(produto_id)
    
    # Verificar status após sincronização
    if result:
        test_get_product_status(produto_id)
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")

