"""
Script para verificar erros na sincronização de pedidos com Bling
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blueprints.services import get_db
import psycopg2.extras
from blueprints.services.bling_order_service import get_order_for_bling_sync
from blueprints.services.bling_product_service import get_bling_product_by_local_id

def check_order_errors(venda_id: int):
    """Verifica problemas em um pedido específico"""
    print(f"\n{'='*80}")
    print(f"Verificando pedido ID: {venda_id}")
    print(f"{'='*80}")
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar dados da venda
        venda = get_order_for_bling_sync(venda_id)
        
        if not venda:
            print(f"❌ Pedido {venda_id} não encontrado")
            return
        
        print(f"\n📋 DADOS DO PEDIDO:")
        print(f"   Código: {venda.get('codigo_pedido')}")
        print(f"   Valor Total: R$ {venda.get('valor_total', 0):.2f}")
        print(f"   Status: {venda.get('status_pedido')}")
        
        # Verificar dados fiscais
        print(f"\n👤 DADOS FISCAIS:")
        fiscal_cpf_cnpj = venda.get('fiscal_cpf_cnpj')
        print(f"   CPF/CNPJ: {fiscal_cpf_cnpj if fiscal_cpf_cnpj else '❌ AUSENTE'}")
        print(f"   Tipo: {venda.get('fiscal_tipo') if venda.get('fiscal_tipo') else '❌ AUSENTE'}")
        print(f"   Nome/Razão: {venda.get('fiscal_nome_razao_social') if venda.get('fiscal_nome_razao_social') else '❌ AUSENTE'}")
        
        # Verificar endereço
        print(f"\n📍 ENDEREÇO DE ENTREGA:")
        print(f"   CEP: {venda.get('cep_entrega') if venda.get('cep_entrega') else '❌ AUSENTE'}")
        print(f"   Rua: {venda.get('rua_entrega') if venda.get('rua_entrega') else '❌ AUSENTE'}")
        print(f"   Número: {venda.get('numero_entrega') if venda.get('numero_entrega') else '❌ AUSENTE'}")
        print(f"   Cidade: {venda.get('cidade_entrega') if venda.get('cidade_entrega') else '❌ AUSENTE'}")
        print(f"   Estado: {venda.get('estado_entrega') if venda.get('estado_entrega') else '❌ AUSENTE'}")
        
        # Verificar itens
        print(f"\n📦 ITENS DO PEDIDO:")
        itens = venda.get('itens', [])
        print(f"   Total de itens: {len(itens)}")
        
        produtos_nao_sincronizados = []
        for item in itens:
            produto_id = item.get('produto_id')
            nome_produto = item.get('nome_produto_snapshot', 'Produto desconhecido')
            bling_produto_id = item.get('bling_produto_id')
            
            if not bling_produto_id:
                produtos_nao_sincronizados.append({
                    'produto_id': produto_id,
                    'nome': nome_produto
                })
                print(f"   ❌ {nome_produto} (ID: {produto_id}) - NÃO SINCRONIZADO NO BLING")
            else:
                print(f"   ✅ {nome_produto} (ID: {produto_id}) - Bling ID: {bling_produto_id}")
        
        # Resumo de problemas
        print(f"\n🔍 RESUMO DE PROBLEMAS:")
        problemas = []
        
        if not fiscal_cpf_cnpj:
            problemas.append("CPF/CNPJ ausente")
        
        if not venda.get('cep_entrega'):
            problemas.append("CEP ausente")
        
        if produtos_nao_sincronizados:
            problemas.append(f"{len(produtos_nao_sincronizados)} produto(s) não sincronizado(s)")
        
        if problemas:
            for problema in problemas:
                print(f"   ⚠️ {problema}")
        else:
            print(f"   ✅ Nenhum problema aparente encontrado")
        
    finally:
        cur.close()

if __name__ == "__main__":
    # Verificar alguns pedidos que falharam
    pedidos_para_verificar = [3, 5, 10, 15, 20, 25, 30, 33, 34, 35, 40, 43]
    
    for venda_id in pedidos_para_verificar:
        try:
            check_order_errors(venda_id)
        except Exception as e:
            print(f"\n❌ Erro ao verificar pedido {venda_id}: {e}")
    
    print(f"\n{'='*80}")
    print("Verificação concluída")
    print(f"{'='*80}")
