import psycopg2.pool
from flask import g


connection_pool = None

def init_db_pool(db_config: dict):
    """
    Inicializa o pool de conexões com o banco de dados.
    Esta função deve ser chamada uma única vez na inicialização da aplicação.
    Recebe as configurações do DB via dicionário.
    """
    global connection_pool
    if connection_pool is None:  
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=20, 
                host=db_config.get("host"),
                dbname=db_config.get("dbname"),
                user=db_config.get("user"),
                password=db_config.get("password")
            )
            print("Database connection pool initialized successfully.")
        except Exception as e:
            print(f"Erro ao inicializar o pool de conexões do banco de dados: {e}")
            raise 
def get_db():
    """
    Obtém uma conexão do pool e a armazena em `g`.
    Garante que cada requisição tenha sua própria conexão.
    """
    if "db" not in g: 
        if connection_pool is None: 
            raise RuntimeError("Connection pool not initialized. Call init_db_pool() first.")
        g.db = connection_pool.getconn()
    return g.db

def close_db_connection(exception=None):
    """
    Devolve a conexão ao pool no final da requisição.
    É chamada pelo `app.teardown_appcontext`.
    """
    db_conn = g.pop("db", None) 
    if db_conn is not None:
        if exception is not None: 
            db_conn.rollback()
        else: 
            try:
                db_conn.commit() 
            except psycopg2.Error as e:
                print(f"ATENÇÃO: Erro ao commitar na finalização da requisição: {e}")
                db_conn.rollback() 
        
        connection_pool.putconn(db_conn)