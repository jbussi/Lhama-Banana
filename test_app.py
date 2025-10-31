#!/usr/bin/env python3
"""
Script de teste para verificar se a aplicação está funcionando corretamente
"""

import os
import sys

# Definir variáveis de ambiente para desenvolvimento
os.environ['FLASK_DEBUG'] = '1'
os.environ['FLASK_ENV'] = 'development'

def test_imports():
    """Testa se todos os imports estão funcionando"""
    print("🔍 Testando imports...")
    
    try:
        from app import create_app
        print("✅ App importado com sucesso")
        
        from blueprints import checkout_api_bp, shipping_api_bp
        print("✅ Blueprints de checkout e frete importados com sucesso")
        
        from blueprints.services import (
            create_order_and_items, create_payment_entry, 
            call_pagseguro_api, create_pagseguro_payload
        )
        print("✅ Serviços de checkout importados com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False

def test_app_creation():
    """Testa se a aplicação pode ser criada"""
    print("\n🔍 Testando criação da aplicação...")
    
    try:
        from app import create_app
        app = create_app()
        print("✅ Aplicação criada com sucesso")
        
        # Verificar se as rotas estão registradas
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"✅ {len(routes)} rotas registradas")
        
        # Verificar rotas específicas
        important_routes = [
            '/', '/checkout', '/carrinho', '/api/checkout/process',
            '/api/shipping/calculate', '/order-status/<codigo_pedido>'
        ]
        
        for route in important_routes:
            if any(route in r for r in routes):
                print(f"✅ Rota {route} encontrada")
            else:
                print(f"⚠️  Rota {route} não encontrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação da aplicação: {e}")
        return False

def test_configuration():
    """Testa se a configuração está correta"""
    print("\n🔍 Testando configuração...")
    
    try:
        from app import create_app
        app = create_app()
        
        # Verificar configurações importantes
        configs_to_check = [
            'SECRET_KEY', 'FIREBASE_ADMIN_SDK_PATH', 'DATABASE_CONFIG',
            'PAGSEGURO_SANDBOX_API_TOKEN', 'DEBUG'
        ]
        
        for config in configs_to_check:
            if hasattr(app.config, config) or config in app.config:
                print(f"✅ Configuração {config} encontrada")
            else:
                print(f"⚠️  Configuração {config} não encontrada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes da aplicação LhamaBanana\n")
    
    tests = [
        test_imports,
        test_app_creation,
        test_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Resultado dos testes: {passed}/{total} passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! A aplicação está funcionando corretamente.")
        print("\n📝 Próximos passos:")
        print("1. Iniciar o PostgreSQL se necessário")
        print("2. Executar as migrações do banco de dados")
        print("3. Executar: python app.py")
        return 0
    else:
        print("❌ Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
