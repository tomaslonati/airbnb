"""
Conexión a Neo4j AuraDB.
"""

from neo4j import GraphDatabase
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

        _neo4j_driver = GraphDatabase.driver(
            db_config.neo4j_uri,
            auth=(db_config.neo4j_user, db_config.neo4j_password)
        )

        # Verificar conectividad
        _neo4j_driver.verify_connectivity()
        logger.info("Driver Neo4j creado exitosamente")

    return _neo4j_driver


async def close_client():
    """Cierra el driver de Neo4j."""
    global _neo4j_driver

    if _neo4j_driver:
        _neo4j_driver.close()
        _neo4j_driver = None
        logger.info("Driver Neo4j cerrado")


def execute_query(query: str, parameters: dict = None, database: str = "neo4j"):
    """Ejecuta una consulta Cypher en Neo4j."""
    try:
        driver = _neo4j_driver
        if not driver:
            logger.error("Driver Neo4j no inicializado")
            return None

        records, summary, keys = driver.execute_query(
            query,
            parameters=parameters or {},
            database_=database
        )

        logger.info(f"Consulta ejecutada: {summary.query[:100]}...")
        logger.info(f"Registros devueltos: {len(records)}")

        return {
            "records": records,
            "summary": summary,
            "keys": keys
        }

    except Exception as e:
        logger.error(f"Error ejecutando consulta Neo4j: {e}")
        raise


def create_relationship(from_node: dict, to_node: dict, relationship: str, properties: dict = None):
    """Crea una relación entre dos nodos."""
    try:
        query = f"""
        MERGE (a:{from_node['label']} {{{from_node['property']}: $from_value}})
        MERGE (b:{to_node['label']} {{{to_node['property']}: $to_value}})
        MERGE (a)-[r:{relationship}]->(b)
        """

        if properties:
            props = ", ".join([f"{k}: ${k}" for k in properties.keys()])
            query += f" SET r += {{{props}}}"

        params = {
            "from_value": from_node["value"],
            "to_value": to_node["value"]
        }

        if properties:
            params.update(properties)

        return execute_query(query, params)

    except Exception as e:
        logger.error(f"Error creando relación: {e}")
        raise
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
