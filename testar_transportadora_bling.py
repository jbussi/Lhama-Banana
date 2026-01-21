"""
Script para testar a busca de transportadora no Bling e preenchimento na NFC-e
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_contact_service import find_contact_in_bling
from blueprints.services.bling_order_service import get_order_for_bling_sync
from blueprints.services.db import get_db
import psycopg2.extras

def test_buscar_transportadora_bling():
    """Testa buscar transportadora no Bling por CNPJ"""
    app = create_app()
    
    with app.app_context():
        # CNPJs das transportadoras cadastradas
        transportadoras_teste = [
            ("Correios", "34028316000103"),
            ("Jadlog", "04263361000188"),
            ("Buslog", "12437084000104"),
            ("Azul Cargo", "15479373000164"),
            ("JeT", "03900533000118")
        ]
        
        print("="*60)
        print("🔍 TESTE: Buscar Transportadoras no Bling")
        print("="*60)
        
        resultados = []
        
        for nome, cnpj in transportadoras_teste:
            print(f"\n📦 Testando: {nome} (CNPJ: {cnpj})")
            try:
                contato = find_contact_in_bling(cnpj)
                if contato:
                    print(f"  ✅ Encontrado!")
                    print(f"     ID Bling: {contato.get('id')}")
                    print(f"     Nome: {contato.get('nome')}")
                    print(f"     CNPJ: {contato.get('numeroDocumento')}")
                    print(f"     IE: {contato.get('ie', 'Não informado')}")
                    
                    # Verificar endereço
                    endereco = contato.get('endereco', {})
                    if endereco:
                        geral = endereco.get('geral') or {}
                        if geral:
                            print(f"     Endereço: {geral.get('endereco', '')}, {geral.get('numero', '')}")
                            print(f"     Cidade: {geral.get('municipio', '')}/{geral.get('uf', '')}")
                    
                    resultados.append({
                        'nome': nome,
                        'cnpj': cnpj,
                        'encontrado': True,
                        'bling_id': contato.get('id')
                    })
                else:
                    print(f"  ❌ Não encontrado no Bling")
                    resultados.append({
                        'nome': nome,
                        'cnpj': cnpj,
                        'encontrado': False
                    })
            except Exception as e:
                print(f"  ❌ Erro: {e}")
                resultados.append({
                    'nome': nome,
                    'cnpj': cnpj,
                    'encontrado': False,
                    'erro': str(e)
                })
        
        # Resumo
        print("\n" + "="*60)
        print("📊 RESUMO")
        print("="*60)
        encontrados = [r for r in resultados if r.get('encontrado')]
        nao_encontrados = [r for r in resultados if not r.get('encontrado')]
        
        print(f"\n✅ Encontradas: {len(encontrados)}/{len(transportadoras_teste)}")
        for r in encontrados:
            print(f"   - {r['nome']} (ID: {r.get('bling_id')})")
        
        if nao_encontrados:
            print(f"\n❌ Não encontradas: {len(nao_encontrados)}")
            for r in nao_encontrados:
                print(f"   - {r['nome']} (CNPJ: {r['cnpj']})")
        
        return resultados


def test_venda_com_transportadora():
    """Testa buscar vendas com transportadora escolhida"""
    app = create_app()
    
    with app.app_context():
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        print("\n" + "="*60)
        print("🔍 TESTE: Buscar Vendas com Transportadora")
        print("="*60)
        
        try:
            # Buscar vendas com transportadora escolhida
            cur.execute("""
                SELECT 
                    id, codigo_pedido, 
                    transportadora_nome, transportadora_cnpj,
                    valor_frete, status_pedido
                FROM vendas
                WHERE transportadora_nome IS NOT NULL 
                  AND transportadora_cnpj IS NOT NULL
                ORDER BY id DESC
                LIMIT 5
            """)
            
            vendas = cur.fetchall()
            
            if not vendas:
                print("\n⚠️  Nenhuma venda encontrada com transportadora escolhida")
                print("   Crie um pedido com frete para testar")
                return None
            
            print(f"\n📦 Encontradas {len(vendas)} venda(s) com transportadora:")
            
            for venda in vendas:
                print(f"\n  Pedido #{venda['id']} - {venda['codigo_pedido']}")
                print(f"    Transportadora: {venda['transportadora_nome']}")
                print(f"    CNPJ: {venda['transportadora_cnpj']}")
                print(f"    Frete: R$ {float(venda['valor_frete']):.2f}")
                print(f"    Status: {venda['status_pedido']}")
            
            # Retornar primeira venda para teste completo
            return dict(vendas[0])
            
        except Exception as e:
            print(f"\n❌ Erro ao buscar vendas: {e}")
            return None
        finally:
            cur.close()


def test_emissao_nfce_com_transportadora(venda_id: int):
    """Testa a emissão de NFC-e com transportadora do Bling"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print(f"🧪 TESTE: Emissão NFC-e com Transportadora (Venda #{venda_id})")
        print("="*60)
        
        # Buscar dados da venda
        venda_data = get_order_for_bling_sync(venda_id)
        
        if not venda_data:
            print(f"\n❌ Venda {venda_id} não encontrada")
            return
        
        print(f"\n📋 Dados da Venda:")
        print(f"   Código: {venda_data.get('codigo_pedido')}")
        print(f"   Valor Total: R$ {float(venda_data.get('valor_total', 0)):.2f}")
        print(f"   Frete: R$ {float(venda_data.get('valor_frete', 0)):.2f}")
        
        transportadora_nome = venda_data.get('transportadora_nome')
        transportadora_cnpj = venda_data.get('transportadora_cnpj')
        
        print(f"\n🚚 Transportadora Escolhida:")
        print(f"   Nome: {transportadora_nome}")
        print(f"   CNPJ: {transportadora_cnpj}")
        
        if not transportadora_cnpj:
            print("\n⚠️  Venda não tem transportadora escolhida")
            return
        
        # Buscar no Bling
        print(f"\n🔍 Buscando transportadora no Bling...")
        try:
            from blueprints.services.bling_contact_service import find_contact_in_bling
            transportadora_bling = find_contact_in_bling(transportadora_cnpj)
            
            if transportadora_bling:
                print(f"✅ Transportadora encontrada no Bling!")
                print(f"   ID Bling: {transportadora_bling.get('id')}")
                print(f"   Nome: {transportadora_bling.get('nome')}")
                print(f"   CNPJ: {transportadora_bling.get('numeroDocumento')}")
                print(f"   IE: {transportadora_bling.get('ie', 'Não informado')}")
                
                # Verificar endereço
                endereco = transportadora_bling.get('endereco', {})
                if endereco:
                    geral = endereco.get('geral') or {}
                    if geral:
                        print(f"\n📍 Endereço Completo:")
                        print(f"   Logradouro: {geral.get('endereco', '')}, {geral.get('numero', '')}")
                        print(f"   Complemento: {geral.get('complemento', 'N/A')}")
                        print(f"   Bairro: {geral.get('bairro', 'N/A')}")
                        print(f"   Município: {geral.get('municipio', '')}/{geral.get('uf', '')}")
                        print(f"   CEP: {geral.get('cep', 'N/A')}")
                
                print(f"\n✅ Dados completos disponíveis para preencher na NFC-e!")
            else:
                print(f"⚠️  Transportadora não encontrada no Bling")
                print(f"   Será usado fallback com dados da tabela vendas")
        except Exception as e:
            print(f"❌ Erro ao buscar transportadora: {e}")
        
        # Perguntar se quer emitir NFC-e
        print(f"\n💡 Para testar a emissão completa da NFC-e, execute:")
        print(f"   docker-compose exec flask python testar_emissao_nfce.py {venda_id}")


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🧪 TESTE COMPLETO: Transportadora no Bling + NFC-e")
    print("="*60)
    
    # Teste 1: Buscar transportadoras no Bling
    resultados_bling = test_buscar_transportadora_bling()
    
    # Teste 2: Buscar venda com transportadora
    venda = test_venda_com_transportadora()
    
    # Teste 3: Testar busca para uma venda específica
    if venda:
        venda_id = venda.get('id')
        test_emissao_nfce_com_transportadora(venda_id)
    else:
        print("\n💡 Para testar emissão completa, crie um pedido com frete primeiro")
    
    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS")
    print("="*60)

if __name__ == '__main__':
    main()
