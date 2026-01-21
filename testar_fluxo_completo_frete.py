"""
Teste completo do fluxo de frete: armazenamento, NF-e e etiqueta
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.db import get_db
import psycopg2.extras
from blueprints.services.bling_contact_service import find_contact_in_bling

def testar_armazenamento_frete():
    """Testa se os dados de frete estão sendo armazenados corretamente"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🧪 TESTE 1: Armazenamento de Dados de Frete no Pedido")
        print("="*60)
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Buscar pedidos recentes com dados de frete
            cur.execute("""
                SELECT 
                    id, codigo_pedido, 
                    transportadora_nome, transportadora_cnpj, transportadora_ie,
                    melhor_envio_service_id, melhor_envio_service_name,
                    valor_frete,                     status_pedido,
                    data_venda
                FROM vendas
                WHERE transportadora_cnpj IS NOT NULL
                   OR melhor_envio_service_id IS NOT NULL
                ORDER BY data_venda DESC
                LIMIT 5
            """)
            
            pedidos = cur.fetchall()
            
            if not pedidos:
                print("\n⚠️  Nenhum pedido encontrado com dados de frete armazenados")
                print("   (Isso é normal se ainda não houver pedidos com frete)")
                return True
            
            print(f"\n✅ Encontrados {len(pedidos)} pedido(s) com dados de frete:\n")
            
            todos_completos = True
            for pedido in pedidos:
                print(f"📦 Pedido: {pedido['codigo_pedido']} (ID: {pedido['id']})")
                print(f"   Status: {pedido['status_pedido']}")
                print(f"   Frete: R$ {float(pedido['valor_frete'] or 0):.2f}")
                
                # Verificar dados da transportadora
                if pedido['transportadora_nome']:
                    print(f"   ✅ Transportadora: {pedido['transportadora_nome']}")
                    if pedido['transportadora_cnpj']:
                        print(f"      CNPJ: {pedido['transportadora_cnpj']}")
                    else:
                        print(f"      ⚠️  CNPJ não informado")
                        todos_completos = False
                else:
                    print(f"   ⚠️  Transportadora não informada")
                    todos_completos = False
                
                # Verificar serviço de frete
                if pedido['melhor_envio_service_id']:
                    print(f"   ✅ Serviço: {pedido['melhor_envio_service_name']} (ID: {pedido['melhor_envio_service_id']})")
                else:
                    print(f"   ⚠️  Serviço de frete não informado")
                    todos_completos = False
                
                print()
            
            if todos_completos:
                print("✅ TESTE 1 PASSOU: Dados de frete estão sendo armazenados corretamente")
            else:
                print("⚠️  TESTE 1 PARCIAL: Alguns dados estão faltando (pode ser normal para pedidos antigos)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro no teste: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cur.close()


def testar_busca_transportadora_bling():
    """Testa se o sistema consegue buscar transportadoras no Bling"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("🧪 TESTE 2: Busca de Transportadoras no Bling")
        print("="*60)
        
        # CNPJs das transportadoras conhecidas
        transportadoras_teste = [
            {'nome': 'Correios', 'cnpj': '34028316000103'},
            {'nome': 'JADLOG', 'cnpj': '04884082000135'},
            {'nome': 'Loggi', 'cnpj': '24217653000195'},
        ]
        
        print(f"\n📦 Testando busca de {len(transportadoras_teste)} transportadoras...\n")
        
        encontradas = 0
        for transp in transportadoras_teste:
            print(f"🔍 Buscando: {transp['nome']} (CNPJ: {transp['cnpj']})")
            
            try:
                contato = find_contact_in_bling(transp['cnpj'])
                
                if contato:
                    encontradas += 1
                    print(f"   ✅ ENCONTRADO! (ID: {contato.get('id')})")
                    print(f"      Nome no Bling: {contato.get('nome')}")
                    
                    # Verificar dados completos
                    tem_endereco = bool(contato.get('endereco', {}).get('geral', {}).get('endereco'))
                    tem_ie = bool(contato.get('ie'))
                    
                    print(f"      Endereço: {'✅' if tem_endereco else '❌'}")
                    print(f"      IE: {'✅' if tem_ie else '❌'}")
                else:
                    print(f"   ❌ NÃO ENCONTRADO")
            except Exception as e:
                print(f"   ❌ ERRO: {e}")
            
            print()
        
        if encontradas == len(transportadoras_teste):
            print("✅ TESTE 2 PASSOU: Busca de transportadoras no Bling funcionando")
        else:
            print(f"⚠️  TESTE 2 PARCIAL: {encontradas}/{len(transportadoras_teste)} transportadoras encontradas")
        
        return encontradas == len(transportadoras_teste)


def testar_dados_nfe():
    """Testa se os dados necessários para NF-e estão disponíveis"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("🧪 TESTE 3: Dados Necessários para Emissão de NF-e")
        print("="*60)
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Verificar se há pedidos prontos para emitir NF-e
            cur.execute("""
                SELECT 
                    v.id, v.codigo_pedido, v.status_pedido,
                    v.transportadora_nome, v.transportadora_cnpj,
                    v.melhor_envio_service_id, v.melhor_envio_service_name,
                    v.fiscal_cpf_cnpj, v.fiscal_nome_razao_social,
                    bp.bling_pedido_id
                FROM vendas v
                LEFT JOIN bling_pedidos bp ON v.id = bp.venda_id
                WHERE v.transportadora_cnpj IS NOT NULL
                  AND v.status_pedido IN ('processando_envio', 'enviado', 'entregue', 'em_processamento', 'nfe_aguardando_aprovacao')
                ORDER BY v.data_venda DESC
                LIMIT 3
            """)
            
            pedidos = cur.fetchall()
            
            if not pedidos:
                print("\n⚠️  Nenhum pedido encontrado pronto para emissão de NF-e")
                print("   (Crie um pedido com frete para testar)")
                return True
            
            print(f"\n📋 Verificando {len(pedidos)} pedido(s)...\n")
            
            todos_ok = True
            for pedido in pedidos:
                print(f"📦 Pedido: {pedido['codigo_pedido']} (ID: {pedido['id']})")
                print(f"   Status: {pedido['status_pedido']}")
                
                # Verificar dados fiscais
                tem_fiscal = bool(pedido['fiscal_cpf_cnpj'] and pedido['fiscal_nome_razao_social'])
                print(f"   Dados fiscais: {'✅' if tem_fiscal else '❌'}")
                if not tem_fiscal:
                    todos_ok = False
                
                # Verificar transportadora
                tem_transportadora = bool(pedido['transportadora_cnpj'])
                print(f"   Transportadora CNPJ: {'✅' if tem_transportadora else '❌'}")
                if not tem_transportadora:
                    todos_ok = False
                
                # Verificar serviço
                tem_servico = bool(pedido['melhor_envio_service_id'])
                print(f"   Serviço de frete: {'✅' if tem_servico else '❌'}")
                if not tem_servico:
                    todos_ok = False
                
                # Verificar se está no Bling
                tem_bling = bool(pedido['bling_pedido_id'])
                print(f"   Pedido no Bling: {'✅' if tem_bling else '⚠️  (pode ser criado depois)'}")
                
                print()
            
            if todos_ok:
                print("✅ TESTE 3 PASSOU: Dados necessários para NF-e estão disponíveis")
            else:
                print("⚠️  TESTE 3 PARCIAL: Alguns dados estão faltando")
            
            return todos_ok
            
        except Exception as e:
            print(f"\n❌ Erro no teste: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cur.close()


def testar_etiquetas():
    """Testa se há etiquetas criadas com os dados corretos"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("🧪 TESTE 4: Verificação de Etiquetas Criadas")
        print("="*60)
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Buscar etiquetas recentes através da tabela de link
            cur.execute("""
                SELECT 
                    ef.id, ef.codigo_pedido,
                    ef.melhor_envio_service_id, ef.melhor_envio_service_name,
                    ef.status_etiqueta, ef.codigo_rastreamento,
                    v.melhor_envio_service_id as venda_service_id,
                    v.melhor_envio_service_name as venda_service_name,
                    evl.venda_id
                FROM etiquetas_frete ef
                JOIN etiquetas_frete_venda_lnk evl ON ef.id = evl.etiqueta_frete_id
                JOIN vendas v ON evl.venda_id = v.id
                ORDER BY ef.created_at DESC
                LIMIT 5
            """)
            
            etiquetas = cur.fetchall()
            
            if not etiquetas:
                print("\n⚠️  Nenhuma etiqueta encontrada")
                print("   (Isso é normal se ainda não houver etiquetas criadas)")
                return True
            
            print(f"\n📦 Encontradas {len(etiquetas)} etiqueta(s):\n")
            
            todas_ok = True
            for etiqueta in etiquetas:
                print(f"🏷️  Etiqueta ID: {etiqueta['id']} - Pedido: {etiqueta['codigo_pedido']}")
                print(f"   Status: {etiqueta['status_etiqueta']}")
                print(f"   Serviço na etiqueta: {etiqueta['melhor_envio_service_name']} (ID: {etiqueta['melhor_envio_service_id']})")
                print(f"   Serviço no pedido: {etiqueta['venda_service_name']} (ID: {etiqueta['venda_service_id']})")
                
                # Verificar se o serviço bate com o pedido
                if etiqueta['melhor_envio_service_id'] == etiqueta['venda_service_id']:
                    print(f"   ✅ Serviço corresponde ao pedido")
                else:
                    print(f"   ⚠️  Serviço não corresponde (pode ser normal se foi alterado)")
                    todas_ok = False
                
                if etiqueta['codigo_rastreamento']:
                    print(f"   ✅ Código de rastreamento: {etiqueta['codigo_rastreamento']}")
                else:
                    print(f"   ⚠️  Código de rastreamento não disponível ainda")
                
                print()
            
            if todas_ok:
                print("✅ TESTE 4 PASSOU: Etiquetas estão sendo criadas corretamente")
            else:
                print("⚠️  TESTE 4 PARCIAL: Algumas etiquetas podem ter inconsistências")
            
            return todas_ok
            
        except Exception as e:
            print(f"\n❌ Erro no teste: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cur.close()


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("🧪 TESTE COMPLETO: Fluxo de Frete, NF-e e Etiqueta")
    print("="*60)
    
    resultados = []
    
    # Teste 1: Armazenamento
    resultados.append(("Armazenamento de Dados de Frete", testar_armazenamento_frete()))
    
    # Teste 2: Busca Bling
    resultados.append(("Busca de Transportadoras no Bling", testar_busca_transportadora_bling()))
    
    # Teste 3: Dados NF-e
    resultados.append(("Dados para Emissão de NF-e", testar_dados_nfe()))
    
    # Teste 4: Etiquetas
    resultados.append(("Verificação de Etiquetas", testar_etiquetas()))
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    total = len(resultados)
    aprovados = sum(1 for _, resultado in resultados if resultado)
    
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "⚠️  PARCIAL/AVISOS"
        print(f"\n{nome}: {status}")
    
    print(f"\n{'='*60}")
    print(f"✅ Testes aprovados: {aprovados}/{total}")
    
    if aprovados == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   O sistema está funcionando corretamente.")
    else:
        print("\n⚠️  Alguns testes tiveram avisos (pode ser normal dependendo dos dados)")
        print("   Verifique os detalhes acima.")
    
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
