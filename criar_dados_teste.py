"""
Script para criar dados de teste: produto e venda completa
==========================================================
Cria rapidamente um produto e uma venda com todos os dados necessarios
para testar a integracao com Bling.
"""
import os
import sys
from datetime import datetime
import psycopg2
import psycopg2.extras

# Carregar variaveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[AVISO] python-dotenv nao instalado. Usando variaveis de ambiente do sistema.")

# Configuracao do banco de dados (mesma do config.py)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'sistema_usuarios')  # Nome correto do banco
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'far111111')  # Senha padrao do env.example

def get_db_connection():
    """Conecta ao banco de dados"""
    # Usar string de conexao para evitar problemas de encoding
    dsn = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
    return psycopg2.connect(dsn, client_encoding='UTF8')


def criar_produto_teste():
    """Cria um produto de teste com todos os dados fiscais"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Verificar se ja existe produto de teste
        cur.execute("""
            SELECT id FROM produtos 
            WHERE codigo_sku = 'TESTE-BLING-001'
            LIMIT 1
        """)
        existing = cur.fetchone()
        
        if existing:
            produto_id = existing['id'] if isinstance(existing, dict) else existing[0]
            print(f"[OK] Produto de teste ja existe: ID {produto_id}")
            return produto_id
        
        # Buscar ou criar categoria (nome_produto precisa de categoria_id)
        cur.execute("SELECT id FROM categorias LIMIT 1")
        categoria_row = cur.fetchone()
        if not categoria_row:
            # Criar categoria padrao
            cur.execute("""
                INSERT INTO categorias (nome, criado_em, atualizado_em)
                VALUES ('Teste', NOW(), NOW())
                RETURNING id
            """)
            categoria_id = cur.fetchone()[0] if not isinstance(cur.fetchone(), dict) else cur.fetchone()['id']
            conn.commit()
            # Refazer busca
            cur.execute("SELECT id FROM categorias WHERE nome = 'Teste' LIMIT 1")
            categoria_row = cur.fetchone()
        
        categoria_id = categoria_row['id'] if isinstance(categoria_row, dict) else categoria_row[0]
        
        # Buscar ou criar nome_produto
        cur.execute("SELECT id FROM nome_produto WHERE nome = 'Produto Teste Bling' LIMIT 1")
        nome_produto_row = cur.fetchone()
        if nome_produto_row:
            nome_produto_id = nome_produto_row['id'] if isinstance(nome_produto_row, dict) else nome_produto_row[0]
        else:
            # Criar nome_produto (usando criado_em e atualizado_em, precisa categoria_id)
            cur.execute("""
                INSERT INTO nome_produto (nome, categoria_id, criado_em, atualizado_em)
                VALUES ('Produto Teste Bling', %s, NOW(), NOW())
                RETURNING id
            """, (categoria_id,))
            result = cur.fetchone()
            nome_produto_id = result['id'] if isinstance(result, dict) else result[0]
            conn.commit()
        
        # Buscar estampa padrao (precisa categoria_id e imagem_url)
        cur.execute("SELECT id FROM estampa LIMIT 1")
        estampa_row = cur.fetchone()
        if estampa_row:
            estampa_id = estampa_row['id'] if isinstance(estampa_row, dict) else estampa_row[0]
        else:
            # Criar estampa padrao (precisa categoria_id e imagem_url obrigatorios)
            cur.execute("""
                INSERT INTO estampa (nome, categoria_id, imagem_url, custo_por_metro, criado_em, atualizado_em)
                VALUES ('Sem Estampa', %s, 'https://via.placeholder.com/300', 0.00, NOW(), NOW())
                RETURNING id
            """, (categoria_id,))
            result = cur.fetchone()
            estampa_id = result['id'] if isinstance(result, dict) else result[0]
            conn.commit()
        
        # Buscar tamanho padrao
        cur.execute("SELECT id FROM tamanho LIMIT 1")
        tamanho_row = cur.fetchone()
        if tamanho_row:
            tamanho_id = tamanho_row['id'] if isinstance(tamanho_row, dict) else tamanho_row[0]
        else:
            # Criar tamanho padrao (usa criado_em e atualizado_em)
            cur.execute("""
                INSERT INTO tamanho (nome, criado_em, atualizado_em)
                VALUES ('Unico', NOW(), NOW())
                RETURNING id
            """)
            result = cur.fetchone()
            tamanho_id = result['id'] if isinstance(result, dict) else result[0]
            conn.commit()
        
        # Verificar colunas existentes na tabela produtos
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='produtos'
            ORDER BY ordinal_position
        """)
        colunas_produtos = [row[0] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
        
        # Montar INSERT com campos que existem
        campos_insert = ['nome_produto_id', 'estampa_id', 'tamanho_id', 'codigo_sku', 
                        'preco_venda', 'custo', 'estoque']
        valores_insert = [nome_produto_id, estampa_id, tamanho_id, 'TESTE-BLING-001', 
                         100.00, 50.00, 10]
        
        # Adicionar campos opcionais se existirem
        if 'ncm' in colunas_produtos:
            campos_insert.append('ncm')
            valores_insert.append('85171200')
        if 'ativo' in colunas_produtos:
            campos_insert.append('ativo')
            valores_insert.append(True)
        if 'criado_em' in colunas_produtos:
            campos_insert.append('criado_em')
        if 'atualizado_em' in colunas_produtos:
            campos_insert.append('atualizado_em')
        
        # Construir SQL
        campos_sql = ', '.join(campos_insert)
        placeholders = ', '.join(['%s'] * len(valores_insert))
        if 'criado_em' in campos_insert:
            placeholders += ', NOW()'
        if 'atualizado_em' in campos_insert:
            placeholders += ', NOW()'
        
        cur.execute(f"""
            INSERT INTO produtos ({campos_sql})
            VALUES ({placeholders})
            RETURNING id
        """, valores_insert)
        
        result = cur.fetchone()
        produto_id = result['id'] if isinstance(result, dict) else result[0]
        conn.commit()
        
        print(f"[OK] Produto criado: ID {produto_id}")
        print(f"   Nome: Produto Teste Bling")
        print(f"   SKU: TESTE-BLING-001")
        if 'ncm' in colunas_produtos:
            print(f"   NCM: 85171200")
        print(f"   Preco: R$ 100,00")
        
        return produto_id
        
    except Exception as e:
        conn.rollback()
        print(f"[ERRO] Erro ao criar produto: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cur.close()
        conn.close()


def criar_venda_teste(produto_id):
    """Cria uma venda de teste com todos os dados fiscais"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Verificar se ja existe venda de teste
        cur.execute("""
            SELECT id FROM vendas 
            WHERE codigo_pedido = 'TESTE-BLING-001' 
            LIMIT 1
        """)
        existing = cur.fetchone()
        
        if existing:
            venda_id = existing['id'] if isinstance(existing, dict) else existing[0]
            print(f"[OK] Venda de teste ja existe: ID {venda_id}")
            return venda_id
        
        # Verificar colunas da tabela vendas
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='vendas'
            ORDER BY ordinal_position
        """)
        colunas_vendas = [row[0] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
        
        # Montar INSERT dinamicamente - apenas campos que existem
        campos_venda = []
        valores_venda = []
        
        # Campos obrigatorios e comuns
        if 'codigo_pedido' in colunas_vendas:
            campos_venda.append('codigo_pedido')
            valores_venda.append('TESTE-BLING-001')
        
        if 'valor_total' in colunas_vendas:
            campos_venda.append('valor_total')
            valores_venda.append(110.00)
        
        if 'valor_subtotal' in colunas_vendas:
            campos_venda.append('valor_subtotal')
            valores_venda.append(100.00)
        
        if 'valor_frete' in colunas_vendas:
            campos_venda.append('valor_frete')
            valores_venda.append(10.00)
        
        if 'valor_desconto' in colunas_vendas:
            campos_venda.append('valor_desconto')
            valores_venda.append(0.00)
        
        if 'status_pedido' in colunas_vendas:
            campos_venda.append('status_pedido')
            valores_venda.append('processando_envio')
        
        # Dados fiscais (apenas se existirem)
        campos_fiscais = ['fiscal_tipo', 'fiscal_cpf_cnpj', 'fiscal_nome_razao_social',
                         'fiscal_inscricao_estadual', 'fiscal_rua', 'fiscal_numero',
                         'fiscal_complemento', 'fiscal_bairro', 'fiscal_cidade',
                         'fiscal_estado', 'fiscal_cep']
        valores_fiscais = ['F', '12345678909', 'Joao Silva Teste', None,
                          'Rua das Flores', '123', 'Apto 45', 'Centro',
                          'Sao Paulo', 'SP', '01310100']
        
        for campo, valor in zip(campos_fiscais, valores_fiscais):
            if campo in colunas_vendas:
                campos_venda.append(campo)
                valores_venda.append(valor)
        
        # Dados de entrega
        campos_entrega = ['nome_recebedor', 'rua_entrega', 'numero_entrega',
                         'complemento_entrega', 'bairro_entrega', 'cidade_entrega',
                         'estado_entrega', 'cep_entrega', 'telefone_entrega', 'email_entrega']
        valores_entrega = ['Joao Silva Teste', 'Rua das Flores', '123', 'Apto 45',
                          'Centro', 'Sao Paulo', 'SP', '01310100', '11999999999',
                          'joao.teste@example.com']
        
        for campo, valor in zip(campos_entrega, valores_entrega):
            if campo in colunas_vendas:
                campos_venda.append(campo)
                valores_venda.append(valor)
        
        # Construir SQL
        campos_sql = ', '.join(campos_venda)
        valores_params = []
        placeholders = []
        for v in valores_venda:
            if v is None:
                placeholders.append('NULL')
            else:
                placeholders.append('%s')
                valores_params.append(v)
        
        placeholders_sql = ', '.join(placeholders)
        
        cur.execute(f"""
            INSERT INTO vendas ({campos_sql})
            VALUES ({placeholders_sql})
            RETURNING id
        """, valores_params)
        
        result = cur.fetchone()
        venda_id = result['id'] if isinstance(result, dict) else result[0]
        
        # Criar item da venda
        cur.execute("""
            INSERT INTO itens_venda (
                venda_id,
                produto_id,
                quantidade,
                preco_unitario,
                subtotal,
                nome_produto_snapshot,
                sku_produto_snapshot,
                criado_em
            ) VALUES (
                %s, %s, 1, 100.00, 100.00,
                'Produto Teste Bling',
                'TESTE-BLING-001',
                NOW()
            )
        """, (venda_id, produto_id))
        
        # Verificar colunas da tabela pagamentos
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='pagamentos'
            ORDER BY ordinal_position
        """)
        colunas_pagamentos = [row[0] if isinstance(row, dict) else row[0] for row in cur.fetchall()]
        
        # Criar pagamento confirmado (para testar NF-e e financeiro)
        campos_pagamento = ['venda_id', 'valor_pago', 'forma_pagamento_tipo', 'status_pagamento']
        valores_pagamento = [venda_id, 110.00, 'PIX', 'PAID']
        
        if 'parcelas' in colunas_pagamentos:
            campos_pagamento.append('parcelas')
            valores_pagamento.append(1)
        
        if 'valor_parcela' in colunas_pagamentos:
            campos_pagamento.append('valor_parcela')
            valores_pagamento.append(110.00)
        
        if 'pago_em' in colunas_pagamentos:
            campos_pagamento.append('pago_em')
        
        if 'criado_em' in colunas_pagamentos:
            campos_pagamento.append('criado_em')
        
        campos_sql = ', '.join(campos_pagamento)
        placeholders_list = []
        valores_params = []
        
        for campo in campos_pagamento:
            if campo == 'venda_id':
                placeholders_list.append('%s')
                valores_params.append(venda_id)
            elif campo == 'valor_pago':
                placeholders_list.append('%s')
                valores_params.append(110.00)
            elif campo == 'forma_pagamento_tipo':
                placeholders_list.append('%s')
                valores_params.append('PIX')
            elif campo == 'status_pagamento':
                placeholders_list.append('%s')
                valores_params.append('PAID')
            elif campo == 'parcelas':
                placeholders_list.append('%s')
                valores_params.append(1)
            elif campo == 'valor_parcela':
                placeholders_list.append('%s')
                valores_params.append(110.00)
            elif campo in ['pago_em', 'criado_em']:
                placeholders_list.append('NOW()')
        
        placeholders_sql = ', '.join(placeholders_list)
        
        cur.execute(f"""
            INSERT INTO pagamentos ({campos_sql})
            VALUES ({placeholders_sql})
        """, valores_params)
        
        conn.commit()
        
        print(f"\n[OK] Venda criada: ID {venda_id}")
        print(f"   Codigo: TESTE-BLING-001")
        print(f"   Status: processando_envio")
        print(f"   Valor Total: R$ 110,00")
        print(f"   Cliente: Joao Silva Teste")
        print(f"   CPF: 123.456.789-09")
        print(f"   Endereco: Rua das Flores, 123 - Centro, Sao Paulo/SP")
        print(f"   CEP: 01310-100")
        print(f"   Pagamento: PIX - PAID (confirmado)")
        
        return venda_id
        
    except Exception as e:
        conn.rollback()
        print(f"[ERRO] Erro ao criar venda: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    """Funcao principal"""
    print("=" * 60)
    print("CRIANDO DADOS DE TESTE PARA INTEGRACAO BLING")
    print("=" * 60)
    
    try:
        # Criar produto
        print("\n1. Criando produto de teste...")
        produto_id = criar_produto_teste()
        
        # Criar venda
        print("\n2. Criando venda de teste...")
        venda_id = criar_venda_teste(produto_id)
        
        print("\n" + "=" * 60)
        print("[OK] DADOS DE TESTE CRIADOS COM SUCESSO!")
        print("=" * 60)
        print(f"\nProximos passos:")
        print(f"1. Sincronizar produto: POST /api/bling/produtos/sync/{produto_id}")
        print(f"2. Sincronizar venda: POST /api/bling/pedidos/sync/{venda_id}")
        print(f"3. Aprovar pedido: POST /api/bling/pedidos/approve/{venda_id}")
        print(f"4. Emitir NF-e: POST /api/bling/pedidos/nfe/emitir/{venda_id}")
        print(f"5. Verificar financeiro: POST /api/bling/financeiro/conta-receber/{venda_id}")
        
    except Exception as e:
        print(f"\n[ERRO] Erro ao criar dados de teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
