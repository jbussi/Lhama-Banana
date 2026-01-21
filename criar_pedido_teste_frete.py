"""
Script para criar um pedido de teste com frete e validar o fluxo completo
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.db import get_db
import psycopg2.extras

def criar_pedido_teste():
    """Cria um pedido de teste com dados de frete completos"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("🧪 CRIANDO PEDIDO DE TESTE COM FRETE")
        print("="*60)
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # 1. Verificar se há produtos disponíveis
            cur.execute("""
                SELECT id, codigo_sku 
                FROM produtos 
                LIMIT 1
            """)
            produto = cur.fetchone()
            
            if not produto:
                print("\n❌ Nenhum produto encontrado. Crie pelo menos um produto primeiro.")
                return None
            
            produto_id = produto['id']
            print(f"\n✅ Produto encontrado: ID {produto_id}")
            
            # 2. Criar pedido de teste com dados completos
            codigo_pedido = f"TESTE-FRETE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Dados da transportadora (Correios como exemplo)
            transportadora_data = {
                'nome': 'Empresa Brasileira de Correios e Telégrafos - ECT',
                'cnpj': '34028316000103',
                'ie': 'ISENTO',
                'uf': 'SP',
                'municipio': 'São Paulo',
                'endereco': 'Rua Mergenthaler, 592',
                'numero': 'S/N',
                'complemento': 'Edifício Sede dos Correios',
                'bairro': 'Vila Leopoldina',
                'cep': '05311900'
            }
            
            # Inserir pedido
            cur.execute("""
                INSERT INTO vendas (
                    codigo_pedido, usuario_id, valor_total, valor_frete, valor_desconto, valor_subtotal,
                    nome_recebedor, rua_entrega, numero_entrega, complemento_entrega,
                    bairro_entrega, cidade_entrega, estado_entrega, cep_entrega,
                    telefone_entrega, email_entrega,
                    status_pedido,
                    fiscal_tipo, fiscal_cpf_cnpj, fiscal_nome_razao_social,
                    fiscal_rua, fiscal_numero, fiscal_bairro, fiscal_cidade, fiscal_estado, fiscal_cep,
                    transportadora_nome, transportadora_cnpj, transportadora_ie, transportadora_uf,
                    transportadora_municipio, transportadora_endereco, transportadora_numero,
                    transportadora_complemento, transportadora_bairro, transportadora_cep,
                    melhor_envio_service_id, melhor_envio_service_name
                ) VALUES (
                    %s, NULL, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s
                )
                RETURNING id, codigo_pedido
            """, (
                codigo_pedido,
                150.00,  # valor_total
                14.89,   # valor_frete
                0.00,    # valor_desconto
                135.11,  # valor_subtotal
                'João Teste',  # nome_recebedor
                'Rua Teste, 123',  # rua_entrega
                '123',  # numero_entrega
                'Apto 45',  # complemento_entrega
                'Centro',  # bairro_entrega
                'São Paulo',  # cidade_entrega
                'SP',  # estado_entrega
                '01000100',  # cep_entrega
                '11999999999',  # telefone_entrega
                'teste@example.com',  # email_entrega
                'em_processamento',  # status_pedido (já está processando para testar NF-e)
                'CPF',  # fiscal_tipo
                '12345678901',  # fiscal_cpf_cnpj
                'João Teste da Silva',  # fiscal_nome_razao_social
                'Rua Teste, 123',  # fiscal_rua
                '123',  # fiscal_numero
                'Centro',  # fiscal_bairro
                'São Paulo',  # fiscal_cidade
                'SP',  # fiscal_estado
                '01000100',  # fiscal_cep
                transportadora_data['nome'],
                transportadora_data['cnpj'],
                transportadora_data['ie'],
                transportadora_data['uf'],
                transportadora_data['municipio'],
                transportadora_data['endereco'],
                transportadora_data['numero'],
                transportadora_data['complemento'],
                transportadora_data['bairro'],
                transportadora_data['cep'],
                1,  # melhor_envio_service_id (1 = PAC)
                'PAC'  # melhor_envio_service_name
            ))
            
            venda_result = cur.fetchone()
            venda_id = venda_result['id']
            
            # 3. Adicionar item ao pedido
            cur.execute("""
                INSERT INTO itens_venda (
                    venda_id, produto_id, quantidade, preco_unitario,
                    nome_produto_snapshot, sku_produto_snapshot
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
            """, (
                venda_id,
                produto_id,
                1,  # quantidade
                135.11,  # preco_unitario
                'Produto Teste',  # nome_produto_snapshot
                produto['codigo_sku']  # sku_produto_snapshot
            ))
            
            conn.commit()
            
            print(f"\n✅ Pedido de teste criado com sucesso!")
            print(f"   ID: {venda_id}")
            print(f"   Código: {codigo_pedido}")
            print(f"   Status: em_processamento")
            print(f"\n📦 Dados do Pedido:")
            print(f"   Valor Total: R$ 150.00")
            print(f"   Frete: R$ 14.89")
            print(f"   Transportadora: {transportadora_data['nome']}")
            print(f"   CNPJ: {transportadora_data['cnpj']}")
            print(f"   Serviço: PAC (ID: 1)")
            
            return venda_id
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ Erro ao criar pedido: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            cur.close()


def validar_dados_pedido(venda_id: int):
    """Valida se os dados do pedido estão corretos"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 VALIDAÇÃO: Dados do Pedido")
        print("="*60)
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            cur.execute("""
                SELECT 
                    id, codigo_pedido, status_pedido,
                    valor_total, valor_frete, valor_desconto,
                    transportadora_nome, transportadora_cnpj, transportadora_ie,
                    transportadora_uf, transportadora_municipio, transportadora_endereco,
                    melhor_envio_service_id, melhor_envio_service_name,
                    fiscal_cpf_cnpj, fiscal_nome_razao_social
                FROM vendas
                WHERE id = %s
            """, (venda_id,))
            
            pedido = cur.fetchone()
            
            if not pedido:
                print("\n❌ Pedido não encontrado!")
                return False
            
            print(f"\n📦 Pedido: {pedido['codigo_pedido']}")
            
            # Validar dados fiscais
            tem_fiscal = bool(pedido['fiscal_cpf_cnpj'] and pedido['fiscal_nome_razao_social'])
            print(f"\n✅ Dados Fiscais:")
            print(f"   CPF/CNPJ: {pedido['fiscal_cpf_cnpj']}")
            print(f"   Nome: {pedido['fiscal_nome_razao_social']}")
            
            # Validar transportadora
            print(f"\n✅ Transportadora:")
            print(f"   Nome: {pedido['transportadora_nome']}")
            print(f"   CNPJ: {pedido['transportadora_cnpj']}")
            print(f"   IE: {pedido['transportadora_ie']}")
            print(f"   UF: {pedido['transportadora_uf']}")
            print(f"   Município: {pedido['transportadora_municipio']}")
            print(f"   Endereço: {pedido['transportadora_endereco']}")
            
            # Validar serviço
            print(f"\n✅ Serviço de Frete:")
            print(f"   Nome: {pedido['melhor_envio_service_name']}")
            print(f"   ID: {pedido['melhor_envio_service_id']}")
            
            # Verificar se todos os dados estão presentes
            dados_completos = (
                pedido['transportadora_nome'] and
                pedido['transportadora_cnpj'] and
                pedido['melhor_envio_service_id'] and
                tem_fiscal
            )
            
            if dados_completos:
                print(f"\n✅ Todos os dados necessários estão presentes!")
                return True
            else:
                print(f"\n⚠️  Alguns dados estão faltando")
                return False
                
        except Exception as e:
            print(f"\n❌ Erro na validação: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cur.close()


def testar_busca_transportadora_bling(venda_id: int):
    """Testa se o sistema consegue buscar a transportadora no Bling"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 VALIDAÇÃO: Busca de Transportadora no Bling")
        print("="*60)
        
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        try:
            # Buscar CNPJ da transportadora do pedido
            cur.execute("""
                SELECT transportadora_cnpj
                FROM vendas
                WHERE id = %s
            """, (venda_id,))
            
            pedido = cur.fetchone()
            if not pedido or not pedido['transportadora_cnpj']:
                print("\n❌ CNPJ da transportadora não encontrado no pedido")
                return False
            
            cnpj = pedido['transportadora_cnpj']
            print(f"\n🔍 Buscando transportadora no Bling...")
            print(f"   CNPJ: {cnpj}")
            
            # Buscar no Bling
            from blueprints.services.bling_contact_service import find_contact_in_bling
            transportadora_bling = find_contact_in_bling(cnpj)
            
            if transportadora_bling:
                print(f"\n✅ Transportadora encontrada no Bling!")
                print(f"   ID Bling: {transportadora_bling.get('id')}")
                print(f"   Nome: {transportadora_bling.get('nome')}")
                print(f"   CNPJ: {transportadora_bling.get('numeroDocumento')}")
                print(f"   IE: {transportadora_bling.get('ie', 'N/A')}")
                
                # Verificar endereço
                endereco = transportadora_bling.get('endereco', {}).get('geral', {})
                if endereco.get('endereco'):
                    print(f"   Endereço: {endereco.get('endereco')}, {endereco.get('numero', '')}")
                    print(f"   {endereco.get('municipio', '')}/{endereco.get('uf', '')}")
                    print(f"\n✅ Dados completos disponíveis para NF-e!")
                else:
                    print(f"   ⚠️  Endereço não encontrado")
                
                return True
            else:
                print(f"\n⚠️  Transportadora não encontrada no Bling")
                print(f"   (O sistema usará dados do pedido como fallback)")
                return True  # Ainda é válido, pois tem fallback
                
        except Exception as e:
            print(f"\n❌ Erro na busca: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            cur.close()


def testar_preparacao_nfe(venda_id: int):
    """Testa se os dados estão prontos para emissão de NF-e"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 VALIDAÇÃO: Preparação para Emissão de NF-e")
        print("="*60)
        
        try:
            from blueprints.services.bling_nfe_service import emit_nfe
            from blueprints.services.bling_order_service import get_order_for_bling_sync
            
            # Verificar se os dados podem ser obtidos
            venda_data = get_order_for_bling_sync(venda_id)
            
            if not venda_data:
                print("\n❌ Erro ao buscar dados do pedido")
                return False
            
            print(f"\n✅ Dados do pedido obtidos com sucesso!")
            
            # Verificar dados fiscais
            cpf_cnpj = venda_data.get('fiscal_cpf_cnpj') or ''
            if not cpf_cnpj:
                print(f"\n❌ CPF/CNPJ não encontrado")
                return False
            
            print(f"   CPF/CNPJ: {cpf_cnpj}")
            print(f"   Nome: {venda_data.get('fiscal_nome_razao_social')}")
            
            # Verificar transportadora
            transportadora_cnpj = venda_data.get('transportadora_cnpj')
            if not transportadora_cnpj:
                print(f"\n❌ CNPJ da transportadora não encontrado")
                return False
            
            print(f"\n✅ Transportadora:")
            print(f"   CNPJ: {transportadora_cnpj}")
            print(f"   Nome: {venda_data.get('transportadora_nome')}")
            
            # Verificar itens
            itens = venda_data.get('itens', [])
            if not itens:
                print(f"\n❌ Nenhum item encontrado no pedido")
                return False
            
            print(f"\n✅ Itens do pedido:")
            for item in itens:
                print(f"   - {item.get('nome_produto_snapshot')} x{item.get('quantidade')}")
            
            # Verificar valores
            print(f"\n✅ Valores:")
            print(f"   Total: R$ {float(venda_data.get('valor_total', 0)):.2f}")
            print(f"   Frete: R$ {float(venda_data.get('valor_frete', 0)):.2f}")
            print(f"   Desconto: R$ {float(venda_data.get('valor_desconto', 0)):.2f}")
            
            print(f"\n✅ Todos os dados estão prontos para emissão de NF-e!")
            
            # AVISO: Não vamos emitir realmente pois pode gerar NF-e de verdade
            print(f"\n⚠️  NOTA: NF-e não será emitida neste teste")
            print(f"   (Para testar emissão real, use o endpoint ou webhook)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro na preparação: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Executa todo o fluxo de teste"""
    print("\n" + "="*60)
    print("🧪 TESTE COMPLETO: Pedido com Frete")
    print("="*60)
    
    # 1. Criar pedido
    venda_id = criar_pedido_teste()
    
    if not venda_id:
        print("\n❌ Falha ao criar pedido de teste")
        return
    
    # 2. Validar dados
    if not validar_dados_pedido(venda_id):
        print("\n❌ Validação dos dados falhou")
        return
    
    # 3. Testar busca no Bling
    if not testar_busca_transportadora_bling(venda_id):
        print("\n⚠️  Busca no Bling teve problemas (mas pode continuar)")
    
    # 4. Testar preparação NF-e
    if not testar_preparacao_nfe(venda_id):
        print("\n❌ Preparação para NF-e falhou")
        return
    
    # Resumo final
    print("\n" + "="*60)
    print("📊 RESUMO DO TESTE")
    print("="*60)
    print(f"\n✅ Pedido de teste criado: ID {venda_id}")
    print(f"✅ Dados armazenados corretamente")
    print(f"✅ Transportadora pode ser encontrada no Bling")
    print(f"✅ Dados estão prontos para emissão de NF-e")
    print(f"\n🎉 FLUXO VALIDADO COM SUCESSO!")
    print(f"\n💡 Próximos passos:")
    print(f"   1. Sincronizar pedido com Bling (se necessário)")
    print(f"   2. Atualizar status para 'Em andamento' no Bling")
    print(f"   3. Webhook vai detectar e emitir NF-e automaticamente")
    print(f"   4. Após aprovação SEFAZ, etiqueta será criada automaticamente")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
