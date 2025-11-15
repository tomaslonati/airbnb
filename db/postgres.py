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
            command_timeout=30,
            statement_cache_size=0  # Desabilitar prepared statements para PgBouncer
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
    """Ejecuta una consulta SQL que retorna resultados."""
    pool = await get_client()
    async with pool.acquire() as connection:
        return await connection.fetch(query, *args)


async def execute_query_one(query: str, *args):
    """Ejecuta una consulta SQL que retorna un solo resultado."""
    pool = await get_client()
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, *args)


async def execute_command(query: str, *args):
    """Ejecuta un comando SQL (INSERT, UPDATE, DELETE) sin retornar resultados."""
    pool = await get_client()
    async with pool.acquire() as connection:
        return await connection.execute(query, *args)


async def insert_one(table: str, data: dict):
    """Inserta un registro en una tabla y retorna el ID generado."""
    pool = await get_client()
    columns = ', '.join(data.keys())
    placeholders = ', '.join(f'${i+1}' for i in range(len(data)))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
    
    async with pool.acquire() as connection:
        result = await connection.fetchrow(query, *data.values())
        return result['id'] if result else None


async def update_by_id(table: str, id: int, data: dict):
    """Actualiza un registro por ID."""
    pool = await get_client()
    set_clause = ', '.join(f"{key} = ${i+2}" for i, key in enumerate(data.keys()))
    query = f"UPDATE {table} SET {set_clause} WHERE id = $1"
    
    async with pool.acquire() as connection:
        return await connection.execute(query, id, *data.values())


async def delete_by_id(table: str, id: int):
    """Elimina un registro por ID."""
    pool = await get_client()
    query = f"DELETE FROM {table} WHERE id = $1"
    
    async with pool.acquire() as connection:
        return await connection.execute(query, id)


async def get_by_id(table: str, id: int):
    """Obtiene un registro por ID."""
    pool = await get_client()
    query = f"SELECT * FROM {table} WHERE id = $1"
    
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, id)


async def get_all(table: str, limit: int = 100, offset: int = 0):
    """Obtiene todos los registros de una tabla con paginación."""
    pool = await get_client()
    query = f"SELECT * FROM {table} ORDER BY id LIMIT $1 OFFSET $2"
    
    async with pool.acquire() as connection:
        return await connection.fetch(query, limit, offset)


async def count_records(table: str, where_clause: str = None, *args):
    """Cuenta registros en una tabla, opcionalmente con filtro WHERE."""
    pool = await get_client()
    query = f"SELECT COUNT(*) as total FROM {table}"
    if where_clause:
        query += f" WHERE {where_clause}"
    
    async with pool.acquire() as connection:
        result = await connection.fetchrow(query, *args)
        return result['total'] if result else 0


async def execute_transaction(queries: list):
    """
    Ejecuta múltiples queries en una transacción.
    queries: lista de tuplas (query, *args)
    """
    pool = await get_client()
    async with pool.acquire() as connection:
        async with connection.transaction():
            results = []
            for query_data in queries:
                query = query_data[0]
                args = query_data[1:] if len(query_data) > 1 else ()
                result = await connection.execute(query, *args)
                results.append(result)
            return results


async def table_exists(table_name: str) -> bool:
    """Verifica si una tabla existe en el esquema public."""
    pool = await get_client()
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = $1
        )
    """
    async with pool.acquire() as connection:
        result = await connection.fetchrow(query, table_name)
        return result['exists'] if result else False


async def ping() -> bool:
    """Verifica la conexión con la base de datos."""
    try:
        pool = await get_client()
        async with pool.acquire() as connection:
            await connection.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Error en ping a PostgreSQL: {e}")
        return False
