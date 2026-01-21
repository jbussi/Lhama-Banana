"""
Script para limpar todos os dados do banco de dados
===================================================
Remove produtos, vendas, pagamentos, logs, etc.
Mantém apenas a estrutura das tabelas e dados essenciais (usuários, configurações)
"""
import os
import sys
import psycopg2
import psycopg2.extras

# Carregar variaveis de ambiente do .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[AVISO] python-dotenv nao instalado. Usando variaveis de ambiente do sistema.")

# Configuracao do banco de dados
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'sistema_usuarios')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'far111111')

def get_db_connection():
    """Conecta ao banco de dados"""
    dsn = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
    return psycopg2.connect(dsn, client_encoding='UTF8')


def limpar_banco():
    """Limpa todos os dados, mantendo apenas estrutura e dados essenciais"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        print("=" * 60)
        print("LIMPANDO BANCO DE DADOS")
        print("=" * 60)
        
        # Ordem de exclusao (respeitando foreign keys)
        tabelas_para_limpar = [
            # Tabelas do Bling (logs e sincronizacoes)
            ('bling_contas_receber', 'Contas a receber do Bling'),
            ('bling_pedidos', 'Pedidos sincronizados com Bling'),
            ('bling_sync_logs', 'Logs de sincronizacao Bling'),
            ('bling_produtos', 'Produtos sincronizados com Bling'),
            ('bling_tokens', 'Tokens OAuth do Bling'),  # Opcional - manter se quiser manter autenticacao
            
            # Pagamentos e vendas
            ('pagamentos', 'Pagamentos'),
            ('itens_venda', 'Itens de venda'),
            ('vendas', 'Vendas/Pedidos'),
            
            # Carrinhos (se existir)
            ('carrinhos', 'Carrinhos de compras'),
            
            # Cupons usados
            ('cupom_usado', 'Cupons utilizados'),
            ('cupom', 'Cupons de desconto'),
            
            # Produtos e variacoes
            ('imagens_produto', 'Imagens de produtos'),
            ('produtos', 'Produtos'),
            ('estampa', 'Estampas'),
            ('nome_produto', 'Nomes de produtos'),
            ('tamanho', 'Tamanhos'),
            ('tecidos', 'Tecidos'),
            
            # Etiquetas de frete
            ('etiquetas_frete', 'Etiquetas de frete'),
            
            # Avaliacoes
            ('avaliacoes', 'Avaliacoes de produtos'),
        ]
        
        # Limpar cada tabela
        for tabela, descricao in tabelas_para_limpar:
            try:
                # Verificar se tabela existe
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (tabela,))
                
                if not cur.fetchone()[0]:
                    print(f"[PULADO] Tabela '{tabela}' nao existe")
                    continue
                
                # Contar registros antes
                cur.execute(f"SELECT COUNT(*) FROM {tabela}")
                count_antes = cur.fetchone()[0]
                
                if count_antes == 0:
                    print(f"[OK] {descricao}: ja esta vazia")
                else:
                    # Limpar tabela
                    cur.execute(f"DELETE FROM {tabela}")
                    registros_removidos = cur.rowcount
                    print(f"[OK] {descricao}: {registros_removidos} registro(s) removido(s)")
                    
            except Exception as e:
                print(f"[ERRO] Erro ao limpar {descricao}: {e}")
                # Continuar com outras tabelas
                pass
        
        # Limpar categorias (opcional - descomentar se quiser limpar)
        # try:
        #     cur.execute("SELECT COUNT(*) FROM categorias")
        #     count = cur.fetchone()[0]
        #     if count > 0:
        #         cur.execute("DELETE FROM categorias")
        #         print(f"[OK] Categorias: {cur.rowcount} registro(s) removido(s)")
        #     else:
        #         print("[OK] Categorias: ja esta vazia")
        # except Exception as e:
        #     print(f"[AVISO] Erro ao limpar categorias: {e}")
        
        # Confirmar todas as mudancas
        conn.commit()
        
        print("\n" + "=" * 60)
        print("[OK] LIMPEZA CONCLUIDA COM SUCESSO!")
        print("=" * 60)
        print("\nDados removidos:")
        print("  - Todos os produtos e variacoes")
        print("  - Todas as vendas e pagamentos")
        print("  - Todos os logs de sincronizacao Bling")
        print("  - Todos os dados sincronizados com Bling")
        print("\nDados mantidos:")
        print("  - Usuarios")
        print("  - Categorias (se existirem)")
        print("  - Estrutura das tabelas")
        print("\nProximo passo:")
        print("  - Criar produtos e vendas diretamente no Bling")
        print("  - Sincronizar do Bling para o sistema local")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERRO] Erro durante a limpeza: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


def confirmar_limpeza(skip_confirm=False):
    """Solicita confirmacao antes de limpar"""
    print("\n" + "=" * 60)
    print("ATENCAO: Esta operacao vai remover TODOS os dados!")
    print("=" * 60)
    print("\nSerá removido:")
    print("  - Todos os produtos")
    print("  - Todas as vendas")
    print("  - Todos os pagamentos")
    print("  - Todos os logs do Bling")
    print("  - Todos os dados sincronizados")
    print("\nSerá mantido:")
    print("  - Usuarios")
    print("  - Categorias")
    print("  - Estrutura das tabelas")
    print("\n" + "=" * 60)
    
    if skip_confirm:
        print("\n[AVISO] Modo nao-interativo: pulando confirmacao")
        return True
    
    try:
        resposta = input("\nDeseja continuar? (digite 'SIM' para confirmar): ")
        
        if resposta.upper() != 'SIM':
            print("\n[OK] Operacao cancelada pelo usuario.")
            return False
        
        return True
    except (EOFError, KeyboardInterrupt):
        print("\n\n[ERRO] Nao foi possivel ler entrada do usuario.")
        print("[AVISO] Use o parametro --yes para pular confirmacao:")
        print("  python limpar_banco_dados.py --yes")
        return False


def main():
    """Funcao principal"""
    skip_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    if not confirmar_limpeza(skip_confirm=skip_confirm):
        return
    
    try:
        limpar_banco()
    except KeyboardInterrupt:
        print("\n\n[AVISO] Operacao interrompida pelo usuario.")
        sys.exit(0)


if __name__ == '__main__':
    main()
