"""
Script para testar emissão de NFC-e
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Lhama-Banana')))

from app import create_app
from blueprints.services.bling_nfe_service import emit_nfce_consumidor
import traceback

def testar_emissao_nfce(venda_id):
    """
    Testa emissão de NFC-e para um pedido específico
    """
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 80)
            print(f"🧪 TESTE DE EMISSÃO DE NFC-e")
            print("=" * 80)
            print(f"Venda ID: {venda_id}")
            print()
            
            # Verificar dados do pedido antes
            from blueprints.services.db import get_db
            import psycopg2.extras
            
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            try:
                cur.execute("""
                    SELECT 
                        id, codigo_pedido, status_pedido, valor_total, valor_frete, valor_desconto,
                        transportadora_nome, melhor_envio_service_id, melhor_envio_service_name,
                        fiscal_cpf_cnpj, fiscal_nome_razao_social
                    FROM vendas
                    WHERE id = %s
                """, (venda_id,))
                
                venda = cur.fetchone()
                
                if not venda:
                    print(f"❌ Venda {venda_id} não encontrada")
                    return
                
                print("📋 Dados do pedido:")
                print(f"   Código: {venda['codigo_pedido']}")
                print(f"   Status: {venda['status_pedido']}")
                print(f"   Valor Total: R$ {venda['valor_total']:.2f}")
                print(f"   Valor Frete: R$ {venda['valor_frete']:.2f}")
                print(f"   Valor Desconto: R$ {venda['valor_desconto']:.2f}")
                print(f"   Transportadora: {venda['transportadora_nome'] or 'N/A'}")
                print(f"   Serviço ME: {venda['melhor_envio_service_name'] or 'N/A'}")
                print(f"   CPF/CNPJ: {venda['fiscal_cpf_cnpj'] or 'N/A'}")
                print(f"   Nome/Razão: {venda['fiscal_nome_razao_social'] or 'N/A'}")
                print()
                
                # Verificar se tem dados fiscais
                if not venda['fiscal_cpf_cnpj']:
                    print("⚠️ AVISO: Pedido sem CPF/CNPJ fiscal. A emissão pode falhar.")
                    print()
                
            finally:
                cur.close()
            
            # Tentar emitir NFC-e
            print("🚀 Iniciando emissão de NFC-e...")
            print()
            
            result = emit_nfce_consumidor(venda_id)
            
            print()
            print("=" * 80)
            print("📊 RESULTADO DA EMISSÃO")
            print("=" * 80)
            
            if result.get('success'):
                print("✅ SUCESSO!")
                print(f"   NFC-e ID: {result.get('nfe_id')}")
                print(f"   Número: {result.get('nfe_numero')}")
                print(f"   Chave de Acesso: {result.get('nfe_chave_acesso')}")
                print(f"   Situação: {result.get('nfe_situacao')}")
                print(f"   Mensagem: {result.get('message')}")
            else:
                print("❌ ERRO!")
                print(f"   Erro: {result.get('error')}")
                if result.get('details'):
                    print(f"   Detalhes: {result.get('details')}")
                if result.get('error_type'):
                    print(f"   Tipo de Erro: {result.get('error_type')}")
            
            return result
            
        except Exception as e:
            print()
            print("=" * 80)
            print("❌ ERRO INESPERADO")
            print("=" * 80)
            print(f"Erro: {str(e)}")
            print()
            print("Traceback completo:")
            traceback.print_exc()
            return None


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Testar emissão de NFC-e')
    parser.add_argument('venda_id', type=int, help='ID da venda para testar')
    
    args = parser.parse_args()
    
    testar_emissao_nfce(args.venda_id)
