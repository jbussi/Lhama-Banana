"""
Script para restaurar campo preco_promocional
"""
import os
import sys
import psycopg2

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

def main():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Adicionar coluna se não existir
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='produtos' AND column_name='preco_promocional'
                ) THEN
                    ALTER TABLE produtos ADD COLUMN preco_promocional DECIMAL(10, 2);
                    RAISE NOTICE '[OK] Campo preco_promocional adicionado';
                ELSE
                    RAISE NOTICE '[PULADO] Campo preco_promocional ja existe';
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("[OK] Campo preco_promocional restaurado com sucesso!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERRO] Erro ao restaurar campo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
