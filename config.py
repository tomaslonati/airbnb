"""
Configuración del proyecto usando Pydantic BaseSettings.
Todas las credenciales y configuraciones se leen desde variables de entorno.
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class DatabaseConfig(BaseSettings):
    """Configuración de todas las bases de datos."""

    # Supabase / PostgreSQL
    postgres_url: str = Field(..., env="POSTGRES_URL")
    # Mantener campos individuales como fallback (opcional)
    postgres_host: str = Field(default="", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_database: str = Field(default="", env="POSTGRES_DATABASE")
    postgres_user: str = Field(default="", env="POSTGRES_USER")
    postgres_password: str = Field(default="", env="POSTGRES_PASSWORD")

    # AstraDB / Cassandra
    astra_db_token: str = Field(default="", env="ASTRA_DB_TOKEN")
    astra_db_endpoint: str = Field(default="", env="ASTRA_DB_ENDPOINT")
    astra_db_keyspace: str = Field(
        default="airbnb_metrics", env="ASTRA_DB_KEYSPACE")
    # Legacy Cassandra config (opcional)
    cassandra_bundle_path: str = Field(default="", env="CASSANDRA_BUNDLE_PATH")
    cassandra_username: str = Field(default="", env="CASSANDRA_USERNAME")
    cassandra_password: str = Field(default="", env="CASSANDRA_PASSWORD")
    cassandra_keyspace: str = Field("airbnb_ks", env="CASSANDRA_KEYSPACE")

    # MongoDB Atlas
    mongo_connection_string: str = Field(..., env="MONGO_CONNECTION_STRING")
    mongo_database: str = Field("airbnb_db", env="MONGO_DATABASE")

    # Neo4j AuraDB
    neo4j_uri: str = Field(default="", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="", env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")

    # Redis Cloud
    redis_host: str = Field(..., env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_username: str = Field("default", env="REDIS_USERNAME")
    redis_password: str = Field(..., env="REDIS_PASSWORD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignorar campos extra del .env


class AppConfig(BaseSettings):
    """Configuración general de la aplicación."""

    app_name: str = Field("Airbnb Backend", env="APP_NAME")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    max_pool_size: int = Field(20, env="MAX_POOL_SIZE")
    timeout_seconds: int = Field(30, env="TIMEOUT_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignorar campos extra del .env


# Instancias globales de configuración
db_config = DatabaseConfig()
app_config = AppConfig()
