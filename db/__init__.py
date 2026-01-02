"""
Módulo de Banco de Dados
========================
Este módulo fornece acesso às funcionalidades de banco de dados.
"""

from .connection import (
    init_db_pool,
    get_db,
    close_db_connection,
    close_pool
)

__all__ = [
    'init_db_pool',
    'get_db',
    'close_db_connection',
    'close_pool'
]

