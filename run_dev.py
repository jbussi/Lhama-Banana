#!/usr/bin/env python3
"""
Script para executar a aplicação em modo de desenvolvimento
"""

import os
import sys
from app import create_app

def main():
    """Função principal para executar em desenvolvimento"""
    
    # Definir variáveis de ambiente para desenvolvimento
    os.environ['FLASK_DEBUG'] = '1'
    os.environ['FLASK_ENV'] = 'development'
    
    print("🚀 Iniciando LhamaBanana em modo de desenvolvimento...")
    print("=" * 50)
    
    try:
        # Criar aplicação
        app = create_app()
        
        # Configurações de desenvolvimento
        host = '127.0.0.1'  # localhost
        port = 5000
        debug = True
        
        print(f"🌐 Servidor rodando em: http://{host}:{port}")
        print(f"🔧 Modo Debug: {'Ativado' if debug else 'Desativado'}")
        print(f"📁 Diretório de trabalho: {os.getcwd()}")
        print("=" * 50)
        print("📋 Rotas disponíveis:")
        print("   • Home: http://127.0.0.1:5000/")
        print("   • Loja: http://127.0.0.1:5000/produtos/")
        print("   • Carrinho: http://127.0.0.1:5000/carrinho")
        print("   • Checkout: http://127.0.0.1:5000/checkout")
        print("   • Login: http://127.0.0.1:5000/auth/login")
        print("   • API Checkout: http://127.0.0.1:5000/api/checkout/process")
        print("   • API Frete: http://127.0.0.1:5000/api/shipping/calculate")
        print("=" * 50)
        print("💡 Dicas:")
        print("   • Pressione Ctrl+C para parar o servidor")
        print("   • O servidor recarrega automaticamente quando você edita arquivos")
        print("   • Banco de dados não é obrigatório em desenvolvimento")
        print("=" * 50)
        
        # Executar aplicação
        app.run(host=host, port=port, debug=debug)
        
    except KeyboardInterrupt:
        print("\n\n👋 Servidor parado pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")
        print("\n🔧 Soluções possíveis:")
        print("   1. Verifique se a porta 5000 não está em uso")
        print("   2. Execute: pip install -r requirements.txt")
        print("   3. Verifique se o arquivo key.json existe")
        sys.exit(1)

if __name__ == '__main__':
    main()
