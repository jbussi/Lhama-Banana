"""
Módulo de Conexão com Banco de Dados PostgreSQL
================================================
Este módulo fornece uma interface reutilizável para conexões com o banco de dados
usando psycopg2 com pool de conexões.

Uso:
    from db.connection import init_db_pool, get_db, close_db_connection
    
    # Na inicialização da aplicação
    init_db_pool(db_config)
    
    # Em rotas/views
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios")
    # ...
"""

import psycopg2.pool
from flask import g
from typing import Dict, Optional


# Pool global de conexões
connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None


def init_db_pool(db_config: Dict[str, str]) -> None:
    """
    Inicializa o pool de conexões com o banco de dados.
    
    Esta função deve ser chamada uma única vez na inicialização da aplicação.
    Recebe as configurações do DB via dicionário com as chaves:
    - host: endereço do servidor PostgreSQL
    - dbname: nome do banco de dados
    - user: usuário do banco de dados
    - password: senha do banco de dados
    
    Args:
        db_config: Dicionário com as configurações de conexão
        
    Raises:
        Exception: Se houver erro ao inicializar o pool de conexões
    """
    global connection_pool
    
    if connection_pool is not None:
        print("⚠️  Pool de conexões já foi inicializado. Ignorando nova inicialização.")
        return
    
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            host=db_config.get("host"),
            dbname=db_config.get("dbname"),
            user=db_config.get("user"),
            password=db_config.get("password")
        )
        print("✅ Pool de conexões do banco de dados inicializado com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao inicializar o pool de conexões do banco de dados: {e}")
        raise


def get_db():
    """
    Obtém uma conexão do pool e a armazena em `g` (contexto do Flask).
    
    Garante que cada requisição tenha sua própria conexão. A conexão é
    automaticamente devolvida ao pool no final da requisição através
    do teardown_appcontext.
    
    Returns:
        psycopg2.connection: Conexão com o banco de dados
        
    Raises:
        RuntimeError: Se o pool não foi inicializado
    """
    if "db" not in g:
        if connection_pool is None:
            raise RuntimeError(
                "Pool de conexões não inicializado. "
                "Chame init_db_pool() antes de usar get_db()."
            )
        g.db = connection_pool.getconn()
    return g.db


def close_db_connection(exception=None) -> None:
    """
    Devolve a conexão ao pool no final da requisição.
    
    É chamada automaticamente pelo `app.teardown_appcontext` do Flask.
    Sempre devolve a conexão ao pool, mesmo em caso de erro.
    
    Args:
        exception: Exceção que ocorreu durante a requisição (se houver)
    """
    db_conn = g.pop("db", None)
    
    if db_conn is not None:
        try:
            if exception is not None:
                # Em caso de erro, faz rollback
                db_conn.rollback()
            else:
                # Sem erro, tenta fazer commit
                try:
                    db_conn.commit()
                except psycopg2.Error as e:
                    print(f"⚠️  Erro ao commitar na finalização da requisição: {e}")
                    db_conn.rollback()
        except Exception as e:
            print(f"⚠️  Erro ao fechar conexão: {e}")
        finally:
            # Sempre devolve a conexão ao pool, mesmo em caso de erro
            try:
                connection_pool.putconn(db_conn)
            except Exception as e:
                print(f"❌ ERRO CRÍTICO: Falha ao devolver conexão ao pool: {e}")


def close_pool() -> None:
    """
    Fecha todas as conexões do pool.
    
    Útil para encerrar a aplicação de forma limpa.
    """
    global connection_pool
    
    if connection_pool is not None:
        try:
            connection_pool.closeall()
            print("✅ Pool de conexões fechado com sucesso.")
        except Exception as e:
            print(f"⚠️  Erro ao fechar pool de conexões: {e}")
        finally:
            connection_pool = None

