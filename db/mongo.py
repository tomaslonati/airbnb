"""
Conexión a MongoDB Atlas usando pymongo.
"""

from pymongo.mongo_client import MongoClient
from typing import Optional
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

# Cliente global
_mongo_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    """Obtiene el cliente de MongoDB."""
    global _mongo_client

    if _mongo_client is None:
        logger.info("Creando cliente MongoDB")
        
        # Log seguro: solo mostrar host si la cadena de conexión existe
        if db_config.mongo_connection_string:
            try:
                host_info = db_config.mongo_connection_string.split('@')[1].split('?')[0]
                logger.info(f"Conectando a: {host_info}")
            except (IndexError, AttributeError):
                logger.info("Conectando a MongoDB")
        else:
            logger.warning("MONGO_CONNECTION_STRING no configurado")

        try:
            _mongo_client = MongoClient(
                db_config.mongo_connection_string,
                maxPoolSize=20,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )

            # Verificar conexión
            _mongo_client.admin.command('ping')
            logger.info("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.error(f"Error al conectar a MongoDB: {e}")
            # No relanzar el error para permitir que la app inicie sin MongoDB
            _mongo_client = None

    return _mongo_client


def close_client():
    """Cierra el cliente de MongoDB."""
    global _mongo_client

    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        logger.info("Cliente MongoDB cerrado")


def get_database():
    """Obtiene la base de datos configurada."""
    client = get_client()
    return client[db_config.mongo_database]


def get_collection(collection_name: str):
    """Obtiene una colección específica."""
    database = get_database()
    return database[collection_name]


def find_documents(collection_name: str, filter_query: dict = None, limit: int = None):
    """Busca documentos en una colección."""
    collection = get_collection(collection_name)
    cursor = collection.find(filter_query or {})
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def insert_document(collection_name: str, document: dict):
    """Inserta un documento en una colección."""
    collection = get_collection(collection_name)
    return collection.insert_one(document)
