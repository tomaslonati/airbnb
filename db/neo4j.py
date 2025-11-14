"""
Conexión a Neo4j AuraDB.
"""

from neo4j import AsyncGraphDatabase
from typing import Optional
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

# Driver global
_neo4j_driver: Optional = None


@retry_on_connection_error()
async def get_client():
    """Obtiene el driver de Neo4j."""
    global _neo4j_driver

    if _neo4j_driver is None:
        logger.info("Creando driver Neo4j")

        _neo4j_driver = AsyncGraphDatabase.driver(
            db_config.neo4j_uri,
            auth=(db_config.neo4j_user, db_config.neo4j_password),
            max_connection_pool_size=20,
            connection_acquisition_timeout=30,
            max_transaction_retry_time=15
        )

        # Verificar conectividad
        await _neo4j_driver.verify_connectivity()
        logger.info("Driver Neo4j creado exitosamente")

    return _neo4j_driver


async def close_client():
    """Cierra el driver de Neo4j."""
    global _neo4j_driver

    if _neo4j_driver:
        await _neo4j_driver.close()
        _neo4j_driver = None
        logger.info("Driver Neo4j cerrado")


async def execute_query(query: str, parameters: dict = None):
    """Ejecuta una consulta Cypher."""
    driver = await get_client()

    async with driver.session() as session:
        result = await session.run(query, parameters or {})
        records = await result.data()
        return records


async def execute_write_transaction(query: str, parameters: dict = None):
    """Ejecuta una transacción de escritura."""
    driver = await get_client()

    async with driver.session() as session:
        result = await session.execute_write(
            lambda tx: tx.run(query, parameters or {})
        )
        return result


async def execute_read_transaction(query: str, parameters: dict = None):
    """Ejecuta una transacción de lectura."""
    driver = await get_client()

    async with driver.session() as session:
        result = await session.execute_read(
            lambda tx: tx.run(query, parameters or {}).data()
        )
        return result
