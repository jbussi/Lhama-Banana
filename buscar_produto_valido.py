#!/usr/bin/env python3
"""
Script para encontrar um produto válido para teste de sincronização Bling
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db.connection import get_db
import psycopg2.extras

def buscar_produto_valido():
    """Busca um produto que tenha NCM válido para teste"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar produto com NCM válido
        cur.execute("""
            SELECT 
                p.id,
                p.codigo_sku,
                p.ncm,
                p.preco_venda,
                p.preco_promocional,
                p.ativo,
                p.estoque,
                np.nome as nome_produto
            FROM produtos p
            JOIN nome_produto np ON p.nome_produto_id = np.id
            WHERE p.ncm IS NOT NULL 
              AND LENGTH(p.ncm) = 8
              AND p.ativo = TRUE
              AND p.preco_venda > 0
              AND p.codigo_sku IS NOT NULL
            ORDER BY p.id
            LIMIT 1
        """)
        
        produto = cur.fetchone()
        
        if produto:
            print(f"✅ Produto encontrado:")
            print(f"   ID: {produto['id']}")
            print(f"   SKU: {produto['codigo_sku']}")
            print(f"   Nome: {produto['nome_produto']}")
            print(f"   NCM: {produto['ncm']}")
            print(f"   Preço Venda: R$ {produto['preco_venda']:.2f}")
            print(f"   Preço Promocional: {'R$ ' + str(produto['preco_promocional']) + '0' if produto['preco_promocional'] else 'Não'}")
            print(f"   Estoque: {produto['estoque']}")
            return produto['id']
        else:
            print("❌ Nenhum produto válido encontrado.")
            print("   Um produto válido precisa ter:")
            print("   - NCM com 8 dígitos")
            print("   - SKU configurado")
            print("   - Preço de venda > 0")
            print("   - Ativo = TRUE")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar produto: {e}")
        return None
    finally:
        cur.close()

if __name__ == "__main__":
    produto_id = buscar_produto_valido()
    if produto_id:
        print(f"\n🎯 Use o ID {produto_id} no teste")
        sys.exit(0)
    else:
        print("\n⚠️  Adicione NCM a um produto antes de testar")
        sys.exit(1)


