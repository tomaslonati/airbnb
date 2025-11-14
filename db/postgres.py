"""
Conexión a Supabase/PostgreSQL usando asyncpg.
"""

import asyncpg
from typing import Optional
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

# Pool global de conexiones
_postgres_pool: Optional[asyncpg.Pool] = None


@retry_on_connection_error()
async def get_client() -> asyncpg.Pool:
    """Obtiene el pool de conexiones de PostgreSQL."""
    global _postgres_pool

    if _postgres_pool is None:
        logger.info("Creando pool de conexiones PostgreSQL")

        _postgres_pool = await asyncpg.create_pool(
            host=db_config.postgres_host,
            port=db_config.postgres_port,
            database=db_config.postgres_database,
            user=db_config.postgres_user,
            password=db_config.postgres_password,
            min_size=5,
            max_size=20,
            command_timeout=30
        )

        logger.info("Pool PostgreSQL creado exitosamente")

    return _postgres_pool


async def close_client():
    """Cierra el pool de conexiones."""
    global _postgres_pool

    if _postgres_pool:
        await _postgres_pool.close()
        _postgres_pool = None
        logger.info("Pool PostgreSQL cerrado")


async def execute_query(query: str, *args):
    """Ejecuta una consulta SQL."""
    pool = await get_client()
    async with pool.acquire() as connection:
        return await connection.fetch(query, *args)


async def execute_command(query: str, *args):
    """Ejecuta un comando SQL (INSERT, UPDATE, DELETE)."""
    pool = await get_client()
    async with pool.acquire() as connection:
        return await connection.execute(query, *args)
