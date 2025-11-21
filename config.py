"""
Configuración de bases de datos para el proyecto Airbnb.
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Cargar variables de entorno
load_dotenv()


class DatabaseConfig(BaseSettings):
    """Configuración de todas las bases de datos."""

    model_config = ConfigDict(extra='ignore')

    # AstraDB/Cassandra - DataAPI
    astra_db_token: str = os.getenv("ASTRA_DB_TOKEN", "")
    astra_db_endpoint: str = os.getenv("ASTRA_DB_ENDPOINT", "")

    # Cassandra CQL - Para reservas
    cassandra_host: str = os.getenv("CASSANDRA_HOST", "localhost")
    cassandra_port: int = int(os.getenv("CASSANDRA_PORT", "9042"))
    cassandra_username: str = os.getenv("CASSANDRA_USERNAME", "cassandra")
    cassandra_password: str = os.getenv("CASSANDRA_PASSWORD", "cassandra")

    # Neo4j AuraDB
    neo4j_uri: str = os.getenv("NEO4J_URI", "")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    # Fallback IPs para problemas DNS
    neo4j_fallback_ip: str = os.getenv("NEO4J_FALLBACK_IP", "34.205.14.132")
    neo4j_enable_fallback: bool = os.getenv("NEO4J_ENABLE_FALLBACK", "true").lower() == "true"

    # MongoDB Atlas
    mongo_connection_string: str = os.getenv("MONGO_CONNECTION_STRING", "")
    mongo_database: str = os.getenv("MONGO_DATABASE", "airbnb_db")

    # Redis Cloud
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_username: str = os.getenv("REDIS_USERNAME", "default")
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # PostgreSQL/Supabase
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "password")
    postgres_database: str = os.getenv("POSTGRES_DATABASE", "airbnb")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


# Instancia global de configuración
db_config = DatabaseConfig()

# Para compatibilidad con importaciones existentes
app_config = db_config  # Alias para compatibilidad
neo4j_uri = db_config.neo4j_uri
neo4j_user = db_config.neo4j_user
neo4j_password = db_config.neo4j_password
neo4j_database = db_config.neo4j_database
