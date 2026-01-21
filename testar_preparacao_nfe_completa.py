"""
Teste completo da preparação de NF-e para validar todos os dados
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_order_service import get_order_for_bling_sync
from blueprints.services.bling_contact_service import find_contact_in_bling

def testar_preparacao_nfe_completa(venda_id: int):
    """Testa a preparação completa de NF-e sem emitir"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🧪 TESTE: Preparação Completa de NF-e")
        print("="*60)
        
        # 1. Buscar dados do pedido
        print(f"\n1️⃣  Buscando dados do pedido {venda_id}...")
        venda_data = get_order_for_bling_sync(venda_id)
        
        if not venda_data:
            print("❌ Pedido não encontrado!")
            return False
        
        print("✅ Dados do pedido obtidos")
        
        # 2. Validar dados fiscais
        print(f"\n2️⃣  Validando dados fiscais...")
        cpf_cnpj = venda_data.get('fiscal_cpf_cnpj') or ''
        cpf_cnpj = str(cpf_cnpj).replace('.', '').replace('-', '').replace('/', '')
        
        if not cpf_cnpj:
            print("❌ CPF/CNPJ não encontrado!")
            return False
        
        tipo_pessoa = 'J' if len(cpf_cnpj) == 14 else 'F'
        print(f"✅ CPF/CNPJ: {cpf_cnpj} (Tipo: {tipo_pessoa})")
        print(f"   Nome: {venda_data.get('fiscal_nome_razao_social')}")
        
        # 3. Preparar contato (simulação)
        print(f"\n3️⃣  Preparando dados do contato...")
        contato = {
            "nome": venda_data.get('fiscal_nome_razao_social') or venda_data.get('nome_recebedor') or 'Cliente',
            "tipoPessoa": tipo_pessoa,
            "numeroDocumento": cpf_cnpj,
            "email": venda_data.get('email_entrega') or '',
            "telefone": venda_data.get('telefone_entrega') or ''
        }
        print(f"✅ Contato preparado: {contato['nome']}")
        
        # 4. Preparar endereço
        print(f"\n4️⃣  Preparando endereço...")
        endereco = {
            "endereco": venda_data.get('fiscal_rua') or venda_data.get('rua_entrega') or '',
            "numero": venda_data.get('fiscal_numero') or venda_data.get('numero_entrega') or '',
            "complemento": venda_data.get('fiscal_complemento') or venda_data.get('complemento_entrega') or '',
            "bairro": venda_data.get('fiscal_bairro') or venda_data.get('bairro_entrega') or '',
            "cep": venda_data.get('fiscal_cep') or venda_data.get('cep_entrega') or '',
            "municipio": venda_data.get('fiscal_cidade') or venda_data.get('cidade_entrega') or '',
            "uf": venda_data.get('fiscal_estado') or venda_data.get('estado_entrega') or ''
        }
        print(f"✅ Endereço: {endereco['endereco']}, {endereco['numero']}")
        print(f"   {endereco['municipio']}/{endereco['uf']} - CEP: {endereco['cep']}")
        
        # 5. Preparar itens
        print(f"\n5️⃣  Preparando itens...")
        itens = []
        valor_total_produtos = 0.0
        
        for item in venda_data.get('itens', []):
            preco_unitario = float(item.get('preco_venda_normal', 0) or item.get('preco_unitario', 0))
            quantidade = float(item.get('quantidade', 1))
            subtotal_item = preco_unitario * quantidade
            valor_total_produtos += subtotal_item
            
            item_nfe = {
                "codigo": item.get('bling_produto_codigo') or item.get('sku_produto_snapshot') or '',
                "descricao": item.get('nome_produto_snapshot') or 'Produto',
                "unidade": "UN",
                "quantidade": quantidade,
                "valor": preco_unitario,
                "tipo": "P"
            }
            itens.append(item_nfe)
            print(f"   ✅ {item_nfe['descricao']} x{quantidade} = R$ {subtotal_item:.2f}")
        
        print(f"✅ Valor total dos produtos: R$ {valor_total_produtos:.2f}")
        
        # 6. Calcular valores
        print(f"\n6️⃣  Calculando valores...")
        valor_frete = float(venda_data.get('valor_frete', 0))
        valor_desconto = float(venda_data.get('valor_desconto', 0))
        valor_total_nota = valor_total_produtos - valor_desconto + valor_frete
        
        print(f"   Produtos: R$ {valor_total_produtos:.2f}")
        print(f"   Desconto: R$ {valor_desconto:.2f}")
        print(f"   Frete: R$ {valor_frete:.2f}")
        print(f"   Total da nota: R$ {valor_total_nota:.2f}")
        
        # 7. Buscar transportadora no Bling
        print(f"\n7️⃣  Buscando transportadora no Bling...")
        transportadora_cnpj = venda_data.get('transportadora_cnpj')
        transportadora_bling = None
        
        if transportadora_cnpj:
            transportadora_bling = find_contact_in_bling(transportadora_cnpj)
            
            if transportadora_bling:
                print(f"✅ Transportadora encontrada no Bling!")
                print(f"   ID: {transportadora_bling.get('id')}")
                print(f"   Nome: {transportadora_bling.get('nome')}")
                
                # Preparar dados de transporte
                endereco_bling = transportadora_bling.get('endereco', {})
                geral = endereco_bling.get('geral') or {}
                
                if geral:
                    transporte = {
                        "fretePorConta": 0,
                        "frete": valor_frete,
                        "transportador": {
                            "nome": transportadora_bling.get('nome'),
                            "numeroDocumento": transportadora_bling.get('numeroDocumento'),
                            "ie": transportadora_bling.get('ie'),
                            "endereco": {
                                "endereco": geral.get('endereco', ''),
                                "numero": geral.get('numero', ''),
                                "complemento": geral.get('complemento', ''),
                                "bairro": geral.get('bairro', ''),
                                "municipio": geral.get('municipio', ''),
                                "uf": geral.get('uf', ''),
                                "cep": geral.get('cep', '').replace('-', '').replace(' ', '')
                            }
                        }
                    }
                    print(f"✅ Dados de transporte preparados com dados do Bling")
                else:
                    print(f"⚠️  Endereço não encontrado, usando dados do pedido")
                    transporte = None
            else:
                print(f"⚠️  Transportadora não encontrada no Bling, usar dados do pedido")
                transporte = None
        else:
            print(f"⚠️  CNPJ da transportadora não informado")
            transporte = None
        
        # 8. Resumo do payload que seria enviado
        print(f"\n8️⃣  Resumo do Payload NF-e:")
        print(f"\n   Tipo: 0 (NF-e Modelo 55)")
        print(f"   Contato: {contato['nome']} ({tipo_pessoa})")
        print(f"   Itens: {len(itens)}")
        print(f"   Valor total produtos: R$ {valor_total_produtos:.2f}")
        print(f"   Desconto: R$ {valor_desconto:.2f}")
        print(f"   Frete: R$ {valor_frete:.2f}")
        print(f"   Total nota: R$ {valor_total_nota:.2f}")
        
        if transporte:
            print(f"   Transportadora: {transporte['transportador']['nome']}")
            print(f"   CNPJ: {transporte['transportador']['numeroDocumento']}")
            print(f"   IE: {transporte['transportador']['ie']}")
        
        # Verificar se tudo está ok
        dados_completos = (
            contato.get('nome') and
            contato.get('numeroDocumento') and
            len(itens) > 0 and
            valor_total_produtos > 0
        )
        
        if dados_completos:
            print(f"\n✅ Todos os dados necessários estão presentes!")
            print(f"✅ NF-e pode ser emitida com sucesso!")
            return True
        else:
            print(f"\n❌ Alguns dados estão faltando")
            return False


def main():
    """Executa o teste"""
    import sys
    
    if len(sys.argv) > 1:
        venda_id = int(sys.argv[1])
    else:
        # Buscar último pedido de teste
        app = create_app()
        with app.app_context():
            from blueprints.services.db import get_db
            import psycopg2.extras
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("""
                SELECT id FROM vendas 
                WHERE codigo_pedido LIKE 'TESTE-FRETE-%'
                ORDER BY data_venda DESC 
                LIMIT 1
            """)
            resultado = cur.fetchone()
            cur.close()
            
            if not resultado:
                print("❌ Nenhum pedido de teste encontrado!")
                print("   Execute primeiro: python criar_pedido_teste_frete.py")
                return
            
            venda_id = resultado['id']
            print(f"📦 Usando pedido de teste: ID {venda_id}\n")
    
    resultado = testar_preparacao_nfe_completa(venda_id)
    
    if resultado:
        print("\n" + "="*60)
        print("🎉 TESTE COMPLETO PASSOU!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ TESTE FALHOU")
        print("="*60)


if __name__ == '__main__':
    main()
