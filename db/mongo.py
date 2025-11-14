"""
Conexión a MongoDB Atlas usando motor.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

# Cliente global
_mongo_client: Optional[AsyncIOMotorClient] = None


@retry_on_connection_error()
async def get_client() -> AsyncIOMotorClient:
    """Obtiene el cliente de MongoDB."""
    global _mongo_client

    if _mongo_client is None:
        logger.info("Creando cliente MongoDB")

        _mongo_client = AsyncIOMotorClient(
            db_config.mongo_connection_string,
            maxPoolSize=20,
            minPoolSize=5,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000
        )

        # Verificar conexión
        await _mongo_client.admin.command('ping')
        logger.info("Cliente MongoDB creado exitosamente")

    return _mongo_client


async def close_client():
    """Cierra el cliente de MongoDB."""
    global _mongo_client

    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        logger.info("Cliente MongoDB cerrado")


async def get_database():
    """Obtiene la base de datos configurada."""
    client = await get_client()
    return client[db_config.mongo_database]


async def get_collection(collection_name: str):
    """Obtiene una colección específica."""
    database = await get_database()
    return database[collection_name]


async def find_documents(collection_name: str, filter_query: dict = None, limit: int = None):
    """Busca documentos en una colección."""
    collection = await get_collection(collection_name)
    cursor = collection.find(filter_query or {})
    if limit:
        cursor = cursor.limit(limit)
    return await cursor.to_list(length=None)


async def insert_document(collection_name: str, document: dict):
    """Inserta un documento en una colección."""
    collection = await get_collection(collection_name)
    return await collection.insert_one(document)
