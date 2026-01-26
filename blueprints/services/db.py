import psycopg2
import psycopg2.pool
from flask import g
import logging

logger = logging.getLogger(__name__)

connection_pool = None
_db_config = None

def init_db_pool(db_config: dict):
    """
    Inicializa o pool de conexões com o banco de dados.
    Esta função deve ser chamada uma única vez na inicialização da aplicação.
    Recebe as configurações do DB via dicionário.
    """
    global connection_pool, _db_config
    _db_config = db_config
    if connection_pool is None:  
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20, 
                host=db_config.get("host"),
                dbname=db_config.get("dbname"),
                user=db_config.get("user"),
                password=db_config.get("password"),
                # Configurações para melhor gerenciamento de conexões
                connect_timeout=10,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            print("Database connection pool initialized successfully.")
        except Exception as e:
            print(f"Erro ao inicializar o pool de conexões do banco de dados: {e}")
            raise 

def _is_connection_valid(conn):
    """
    Verifica se uma conexão está válida e ativa.
    """
    if conn is None:
        return False
    try:
        # Tentar executar uma query simples para verificar se a conexão está viva
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        return True
    except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.DatabaseError):
        return False
    except Exception:
        # Outros erros podem indicar que a conexão está válida mas houve outro problema
        # Nesse caso, assumimos que está válida
        return True

def _get_new_connection():
    """
    Obtém uma nova conexão diretamente do pool ou cria uma nova se necessário.
    """
    global connection_pool, _db_config
    
    if connection_pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_db_pool() first.")
    
    try:
        # Tentar obter do pool
        conn = connection_pool.getconn()
        # Verificar se a conexão está válida
        if _is_connection_valid(conn):
            return conn
        else:
            # Conexão inválida, tentar fechar e obter nova
            try:
                connection_pool.putconn(conn, close=True)
            except Exception:
                pass
            # Tentar obter nova conexão
            conn = connection_pool.getconn()
            if _is_connection_valid(conn):
                return conn
            else:
                # Se ainda estiver inválida, criar conexão direta como fallback
                logger.warning("Pool retornou conexão inválida, criando conexão direta")
                return psycopg2.connect(
                    host=_db_config.get("host"),
                    dbname=_db_config.get("dbname"),
                    user=_db_config.get("user"),
                    password=_db_config.get("password"),
                    connect_timeout=10
                )
    except psycopg2.pool.PoolError:
        # Pool esgotado ou erro, criar conexão direta como fallback
        logger.warning("Pool esgotado ou erro, criando conexão direta")
        return psycopg2.connect(
            host=_db_config.get("host"),
            dbname=_db_config.get("dbname"),
            user=_db_config.get("user"),
            password=_db_config.get("password"),
            connect_timeout=10
        )

def get_db():
    """
    Obtém uma conexão do pool e a armazena em `g`.
    Garante que cada requisição tenha sua própria conexão.
    Verifica se a conexão está válida e reconecta se necessário.
    """
    if "db" not in g: 
        g.db = _get_new_connection()
    else:
        # Verificar se a conexão existente ainda está válida
        if not _is_connection_valid(g.db):
            logger.warning("Conexão existente inválida, obtendo nova conexão")
            try:
                # Tentar fechar a conexão antiga
                try:
                    connection_pool.putconn(g.db, close=True)
                except Exception:
                    try:
                        g.db.close()
                    except Exception:
                        pass
            except Exception:
                pass
            g.db = _get_new_connection()
    return g.db

def close_db_connection(exception=None):
    """
    Devolve a conexão ao pool no final da requisição.
    É chamada pelo `app.teardown_appcontext`.
    Sempre devolve a conexão ao pool, mesmo em caso de erro.
    """
    db_conn = g.pop("db", None) 
    if db_conn is not None:
        try:
            # Verificar se a conexão ainda está válida antes de tentar commit/rollback
            if not _is_connection_valid(db_conn):
                logger.warning("Conexão inválida detectada no teardown, fechando diretamente")
                try:
                    db_conn.close()
                except Exception:
                    pass
                return
            
            # Verificar se está em autocommit
            # psycopg2 não expõe autocommit diretamente, então tentamos fazer commit/rollback
            # e ignoramos erros se estiver em autocommit
            if exception is not None: 
                try:
                    db_conn.rollback()
                except (psycopg2.OperationalError, psycopg2.InterfaceError):
                    # Conexão foi fechada, apenas fechar
                    try:
                        db_conn.close()
                    except Exception:
                        pass
                    return
                except Exception:
                    # Ignorar erro se estiver em autocommit
                    pass
            else: 
                try:
                    db_conn.commit() 
                except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                    # Conexão foi fechada, apenas fechar
                    logger.warning(f"Conexão fechada durante commit: {e}")
                    try:
                        db_conn.close()
                    except Exception:
                        pass
                    return
                except psycopg2.Error as e:
                    # Se o erro for relacionado a autocommit ou transação, apenas logar
                    error_str = str(e).lower()
                    if 'autocommit' in error_str or 'no transaction' in error_str or 'tuples_ok' in error_str:
                        # Está em autocommit ou não há transação - isso é normal
                        pass
                    else:
                        logger.warning(f"Erro ao commitar na finalização da requisição: {e}")
                        try:
                            db_conn.rollback()
                        except Exception:
                            pass
                except Exception as e:
                    # Outros erros podem ser ignorados se estiver em autocommit
                    pass
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            logger.warning(f"Erro operacional ao fechar conexão: {e}")
            try:
                db_conn.close()
            except Exception:
                pass
            return
        except Exception as e:
            logger.warning(f"Erro ao fechar conexão: {e}")
        finally:
            # Sempre devolve a conexão ao pool, mesmo em caso de erro
            try:
                # Verificar se a conexão ainda está válida antes de devolver ao pool
                if _is_connection_valid(db_conn):
                    connection_pool.putconn(db_conn)
                else:
                    # Conexão inválida, fechar e não devolver ao pool
                    try:
                        db_conn.close()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Erro crítico ao devolver conexão ao pool: {e}")
                # Tentar fechar a conexão se não conseguir devolver ao pool
                try:
                    db_conn.close()
                except Exception:
                    pass