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

        try:
            _neo4j_driver = GraphDatabase.driver(
                db_config.neo4j_uri,
                auth=(db_config.neo4j_user, db_config.neo4j_password),
                max_connection_lifetime=30,
                max_connection_pool_size=10,
                connection_timeout=10
            )

            # Test básico en lugar de verify_connectivity
            result = _neo4j_driver.execute_query("RETURN 1 as test")
            logger.info("Driver Neo4j creado exitosamente")

        except Exception as e:
            logger.error(f"Error creando driver Neo4j: {e}")
            _neo4j_driver = None
            raise

    return _neo4j_driver


async def close_client():
    """Cierra el driver de Neo4j."""
    global _neo4j_driver

    if _neo4j_driver:
        _neo4j_driver.close()
        _neo4j_driver = None
        logger.info("Driver Neo4j cerrado")


def is_available():
    """Verifica si Neo4j está disponible."""
    try:
        from config import db_config
        driver = GraphDatabase.driver(
            db_config.neo4j_uri,
            auth=(db_config.neo4j_user, db_config.neo4j_password),
            connection_timeout=5
        )

        # Test rápido
        driver.execute_query("RETURN 1 as test")
        driver.close()
        return True

    except Exception as e:
        logger.warning(f"Neo4j no disponible: {e}")
        return False


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


def create_node(label: str, properties: dict):
    """Crea un nodo en Neo4j."""
    try:
        driver = _neo4j_driver
        if not driver:
            logger.error("Driver Neo4j no inicializado")
            return None

        props = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{label} {{{props}}}) RETURN n"

        result = driver.execute_query(
            query, parameters=properties, database_="neo4j")
        logger.info(f"Nodo {label} creado exitosamente")
        return result

    except Exception as e:
        logger.error(f"Error creando nodo: {e}")
        raise


def find_nodes(label: str, properties: dict = None):
    """Busca nodos en Neo4j."""
    try:
        driver = _neo4j_driver
        if not driver:
            logger.error("Driver Neo4j no inicializado")
            return None

        if properties:
            where_clause = " AND ".join(
                [f"n.{k} = ${k}" for k in properties.keys()])
            query = f"MATCH (n:{label}) WHERE {where_clause} RETURN n"
            params = properties
        else:
            query = f"MATCH (n:{label}) RETURN n"
            params = {}

        result = driver.execute_query(
            query, parameters=params, database_="neo4j")
        return result[0]  # records

    except Exception as e:
        logger.error(f"Error buscando nodos: {e}")
        raise


def get_recommendations(user_id: str, limit: int = 5):
    """Obtiene recomendaciones basadas en el grafo."""
    try:
        driver = _neo4j_driver
        if not driver:
            logger.error("Driver Neo4j no inicializado")
            return []

        # Consulta de recomendación: personas que conocen a personas que conozco
        query = """
        MATCH (user:Person {id: $user_id})-[:KNOWS]->(friend:Person)-[:KNOWS]->(recommendation:Person)
        WHERE recommendation.id <> $user_id
        AND NOT (user)-[:KNOWS]->(recommendation)
        RETURN recommendation, count(*) as score
        ORDER BY score DESC
        LIMIT $limit
        """

        records, summary, keys = driver.execute_query(
            query,
            parameters={"user_id": user_id, "limit": limit},
            database_="neo4j"
        )

        recommendations = []
        for record in records:
            rec_data = record.data()
            recommendations.append({
                "person": dict(rec_data["recommendation"]),
                "score": rec_data["score"]
            })

        return recommendations

    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones: {e}")
        raise
