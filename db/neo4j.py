"""
Conexión a Neo4j AuraDB.
"""

from neo4j import GraphDatabase
from typing import Optional
import socket
import re
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

# Driver global
_neo4j_driver: Optional = None


def resolve_neo4j_uri():
    """Resuelve la URI de Neo4j con fallback DNS."""
    original_uri = db_config.neo4j_uri
    
    if not original_uri:
        logger.error("Neo4j URI no configurada")
        return None
        
    # Extraer el hostname de la URI y convertir esquema
    match = re.match(r'(neo4j\+s?://)([^:]+)(.*)', original_uri)
    if not match:
        logger.error(f"URI Neo4j inválida: {original_uri}")
        return original_uri
        
    protocol, hostname, rest = match.groups()
    
    # Convertir neo4j+s a bolt+s para compatibilidad con configuraciones SSL
    if protocol.startswith('neo4j+s'):
        protocol = 'bolt+s://'
    
    try:
        # Intentar resolver DNS normal
        socket.gethostbyname(hostname)
        logger.info(f"DNS resuelto correctamente para {hostname}")
        return f"{protocol}{hostname}{rest}"
        
    except socket.gaierror as e:
        logger.warning(f"Error DNS para {hostname}: {e}")
        
        if db_config.neo4j_enable_fallback:
            # Usar IP de fallback
            fallback_uri = f"{protocol}{db_config.neo4j_fallback_ip}{rest}"
            logger.info(f"Usando URI fallback: {fallback_uri}")
            return fallback_uri
        else:
            logger.error("Fallback DNS deshabilitado")
            return f"{protocol}{hostname}{rest}"


@retry_on_connection_error()
async def get_client():
    """Obtiene el driver de Neo4j con timeout rápido."""
    global _neo4j_driver

    if _neo4j_driver is None:
        logger.info("Creando driver Neo4j")

        # Resolver URI con fallback
        neo4j_uri = resolve_neo4j_uri()
        if not neo4j_uri:
            raise ConnectionError("No se pudo resolver URI de Neo4j")

        try:
            _neo4j_driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(db_config.neo4j_user, db_config.neo4j_password),
                max_connection_lifetime=10,
                max_connection_pool_size=5,
                connection_timeout=3  # Timeout muy rápido
            )

            # Test rápido con timeout
            import asyncio
            try:
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: _neo4j_driver.execute_query("RETURN 1 as test")
                    ), 
                    timeout=3.0
                )
                logger.info(f"Driver Neo4j creado exitosamente con URI: {neo4j_uri}")
            except asyncio.TimeoutError:
                logger.warning("Timeout en test de conexión Neo4j")
                _neo4j_driver.close()
                _neo4j_driver = None
                raise ConnectionError("Timeout conectando a Neo4j")

        except Exception as e:
            logger.error(f"Error creando driver Neo4j: {e}")
            if _neo4j_driver:
                _neo4j_driver.close()
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
    """Verifica si Neo4j está disponible con timeout rápido."""
    try:
        import time
        
        neo4j_uri = resolve_neo4j_uri()
        if not neo4j_uri:
            return False
        
        start_time = time.time()
        driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(db_config.neo4j_user, db_config.neo4j_password),
            connection_timeout=2  # Timeout muy rápido
        )

        # Test súper rápido
        driver.execute_query("RETURN 1 as test")
        driver.close()
        
        elapsed = time.time() - start_time
        logger.info(f"Neo4j disponible en {elapsed:.2f}s")
        return True

    except Exception as e:
        logger.warning(f"Neo4j no disponible: {e}")
        return False


def quick_check():
    """Verificación muy rápida de Neo4j (solo DNS)."""
    try:
        original_uri = db_config.neo4j_uri
        if not original_uri:
            return False
            
        # Solo verificar si podemos resolver el hostname
        match = re.match(r'neo4j\+s://([^:]+)', original_uri)
        if match:
            hostname = match.group(1)
            socket.gethostbyname(hostname)
            logger.info("Neo4j quick check: DNS OK")
            return True
        return False
        
    except Exception as e:
        logger.warning(f"Neo4j quick check failed: {e}")
        return False

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
