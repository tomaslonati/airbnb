"""
Conexión a AstraDB/Cassandra.
"""

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
from typing import Optional
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

# Sesión global
_cassandra_session: Optional = None


@retry_on_connection_error()
async def get_client():
    """Obtiene la sesión de Cassandra."""
    global _cassandra_session

    if _cassandra_session is None:
        logger.info("Creando sesión Cassandra")

        # Configuración de autenticación
        auth_provider = PlainTextAuthProvider(
            username=db_config.cassandra_username,
            password=db_config.cassandra_password
        )

        # Configuración del cluster
        cluster = Cluster(
            cloud={
                'secure_connect_bundle': db_config.cassandra_bundle_path
            },
            auth_provider=auth_provider,
            load_balancing_policy=DCAwareRoundRobinPolicy()
        )

        _cassandra_session = cluster.connect(db_config.cassandra_keyspace)
        logger.info("Sesión Cassandra creada exitosamente")

    return _cassandra_session


async def close_client():
    """Cierra la sesión de Cassandra."""
    global _cassandra_session

    if _cassandra_session:
        _cassandra_session.shutdown()
        _cassandra_session = None
        logger.info("Sesión Cassandra cerrada")


async def execute_query(query: str, params: list = None):
    """Ejecuta una consulta CQL."""
    session = await get_client()
    if params:
        return session.execute(query, params)
    return session.execute(query)


async def execute_prepared(prepared_query, params: list):
    """Ejecuta una consulta preparada."""
    session = await get_client()
    return session.execute(prepared_query, params)
