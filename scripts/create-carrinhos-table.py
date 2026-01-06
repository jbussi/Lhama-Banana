#!/usr/bin/env python3
"""
Script para criar a tabela carrinhos e carrinho_itens no banco de dados.
Execute este script quando o banco de dados estiver disponível.
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blueprints.services.db import get_db

def create_carrinhos_tables():
    """Cria as tabelas carrinhos e carrinho_itens se não existirem."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verifica se a tabela já existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'carrinhos'
            );
        """)
        exists = cur.fetchone()[0]
        
        if exists:
            print("✓ A tabela 'carrinhos' já existe.")
            return True
        
        print("Criando tabela 'carrinhos'...")
        
        # Cria a tabela carrinhos
        cur.execute("""
            CREATE TABLE carrinhos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                session_id VARCHAR(255) UNIQUE,
                criado_em TIMESTAMP DEFAULT NOW(),
                atualizado_em TIMESTAMP DEFAULT NOW(),
                expira_em TIMESTAMP,
                UNIQUE (usuario_id)
            );
        """)
        
        print("✓ Tabela 'carrinhos' criada com sucesso.")
        
        # Cria a tabela carrinho_itens
        print("Criando tabela 'carrinho_itens'...")
        cur.execute("""
            CREATE TABLE carrinho_itens (
                id SERIAL PRIMARY KEY,
                carrinho_id INTEGER REFERENCES carrinhos(id) ON DELETE CASCADE,
                produto_id INTEGER REFERENCES produtos(id) ON DELETE RESTRICT,
                quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                preco_unitario_no_momento DECIMAL(10, 2) NOT NULL,
                adicionado_em TIMESTAMP DEFAULT NOW(),
                UNIQUE (carrinho_id, produto_id)
            );
        """)
        
        print("✓ Tabela 'carrinho_itens' criada com sucesso.")
        
        # Cria ou atualiza a função update_timestamp se não existir
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_timestamp()
            RETURNS TRIGGER AS $$
            BEGIN
               NEW.atualizado_em = NOW();
               RETURN NEW;
            END;
            $$ language plpgsql;
        """)
        
        # Cria os triggers
        cur.execute("""
            DROP TRIGGER IF EXISTS trg_carrinhos_update_timestamp ON carrinhos;
            CREATE TRIGGER trg_carrinhos_update_timestamp 
                BEFORE UPDATE ON carrinhos 
                FOR EACH ROW 
                EXECUTE FUNCTION update_timestamp();
        """)
        
        cur.execute("""
            DROP TRIGGER IF EXISTS trg_carrinho_itens_update_timestamp ON carrinho_itens;
            CREATE TRIGGER trg_carrinho_itens_update_timestamp 
                BEFORE UPDATE ON carrinho_itens 
                FOR EACH ROW 
                EXECUTE FUNCTION update_timestamp();
        """)
        
        conn.commit()
        print("\n✓ Todas as tabelas e triggers foram criadas com sucesso!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Erro ao criar tabelas: {e}")
        return False
    finally:
        if cur:
            cur.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Criando tabelas de carrinho no banco de dados")
    print("=" * 60)
    success = create_carrinhos_tables()
    sys.exit(0 if success else 1)

