"""
Conexión a Redis Cloud.
"""

import redis.asyncio as redis
from typing import Optional
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

# Cliente global
_redis_client: Optional[redis.Redis] = None


@retry_on_connection_error()
async def get_client() -> redis.Redis:
    """Obtiene el cliente de Redis."""
    global _redis_client

    if _redis_client is None:
        logger.info("Creando cliente Redis")

        _redis_client = redis.from_url(
            db_config.redis_url,
            max_connections=20,
            retry_on_timeout=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        # Verificar conexión
        await _redis_client.ping()
        logger.info("Cliente Redis creado exitosamente")

    return _redis_client


async def close_client():
    """Cierra el cliente de Redis."""
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Cliente Redis cerrado")


async def get_key(key: str) -> Optional[str]:
    """Obtiene el valor de una clave."""
    client = await get_client()
    value = await client.get(key)
    return value.decode('utf-8') if value else None


async def set_key(key: str, value: str, expire: int = None):
    """Establece una clave con valor y tiempo de expiración opcional."""
    client = await get_client()
    return await client.set(key, value, ex=expire)


async def delete_key(key: str):
    """Elimina una clave."""
    client = await get_client()
    return await client.delete(key)


async def set_hash(key: str, field: str, value: str):
    """Establece un campo en un hash."""
    client = await get_client()
    return await client.hset(key, field, value)


async def get_hash(key: str, field: str = None):
    """Obtiene un campo de un hash o todo el hash."""
    client = await get_client()
    if field:
        value = await client.hget(key, field)
        return value.decode('utf-8') if value else None
    else:
        hash_data = await client.hgetall(key)
        return {k.decode('utf-8'): v.decode('utf-8') for k, v in hash_data.items()}
