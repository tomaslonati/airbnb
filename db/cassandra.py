"""
Conexión a AstraDB usando DataAPIClient.
"""

from astrapy import DataAPIClient
from typing import Optional, Any
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error
import logging

# Configurar logger para reducir logs verbosos
logger = get_logger(__name__)

# Desactivar logging verbose de astrapy y httpx
logging.getLogger('astrapy').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# Clientes globales
_astra_client: Optional[DataAPIClient] = None
_astra_database: Optional[Any] = None


@retry_on_connection_error()
async def get_astra_client():
    """Obtiene el cliente de AstraDB DataAPI."""
    global _astra_client, _astra_database

    if _astra_client is None:
        logger.info("Creando cliente AstraDB DataAPI")
        
        # Inicializar cliente
        _astra_client = DataAPIClient(db_config.astra_db_token)
        _astra_database = _astra_client.get_database_by_api_endpoint(
            db_config.astra_db_endpoint
        )
        
        # Verificar conexión silenciosamente
        collections = _astra_database.list_collection_names()
        logger.info(f"✅ Conectado a AstraDB ({len(collections)} colecciones)")

    return _astra_database


async def create_collection(collection_name: str, dimension: int = None):
    """Crea una colección en AstraDB."""
    try:
        database = await get_astra_client()
        
        if dimension:
            # Colección vectorial
            collection = database.create_collection(collection_name, dimension=dimension)
        else:
            # Colección normal
            collection = database.create_collection(collection_name)
        
        logger.info(f"Colección '{collection_name}' creada exitosamente")
        return collection
        
    except Exception as e:
        logger.error(f"Error creando colección '{collection_name}': {e}")
        raise


async def get_collection(collection_name: str):
    """Obtiene una colección de AstraDB."""
    try:
        database = await get_astra_client()
        collection = database.get_collection(collection_name)
        return collection
        
    except Exception as e:
        logger.error(f"Error obteniendo colección '{collection_name}': {e}")
        raise


async def insert_document(collection_name: str, document: dict):
    """Inserta un documento en una colección."""
    try:
        collection = await get_collection(collection_name)
        result = collection.insert_one(document)
        logger.debug(f"Documento insertado en '{collection_name}': {result.inserted_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error insertando documento en '{collection_name}': {e}")
        raise


async def find_documents(collection_name: str, filter_dict: dict = None, limit: int = 20):
    """Busca documentos en una colección."""
    try:
        collection = await get_collection(collection_name)
        
        if filter_dict:
            cursor = collection.find(filter_dict, limit=limit)
        else:
            cursor = collection.find({}, limit=limit)
        
        documents = list(cursor)
        logger.debug(f"Encontrados {len(documents)} documentos en '{collection_name}'")
        return documents
        
    except Exception as e:
        logger.error(f"Error buscando documentos en '{collection_name}': {e}")
        raise


async def update_document(collection_name: str, filter_dict: dict, update_data: dict):
    """Actualiza un documento en una colección."""
    try:
        collection = await get_collection(collection_name)
        result = collection.update_one(filter_dict, {"$set": update_data})
        logger.info(f"Documento actualizado en '{collection_name}': {result.modified_count} modificados")
        return result
        
    except Exception as e:
        logger.error(f"Error actualizando documento en '{collection_name}': {e}")
        raise


async def delete_document(collection_name: str, filter_dict: dict):
    """Elimina un documento de una colección."""
    try:
        collection = await get_collection(collection_name)
        result = collection.delete_one(filter_dict)
        logger.info(f"Documento eliminado de '{collection_name}': {result.deleted_count} eliminados")
        return result
        
    except Exception as e:
        logger.error(f"Error eliminando documento de '{collection_name}': {e}")
        raise


async def count_documents(collection_name: str, filter_dict: dict = None):
    """Cuenta documentos en una colección."""
    try:
        collection = await get_collection(collection_name)
        
        if filter_dict:
            count = collection.count_documents(filter_dict)
        else:
            count = collection.count_documents({})
        
        logger.info(f"Conteo de documentos en '{collection_name}': {count}")
        return count
        
    except Exception as e:
        logger.error(f"Error contando documentos en '{collection_name}': {e}")
        raise


async def close_client():
    """Cierra las conexiones."""
    global _astra_client, _astra_database

    if _astra_client:
        # AstraDB se cierra automáticamente
        _astra_client = None
        _astra_database = None
        logger.info("Cliente AstraDB cerrado")


# Funciones legacy compatibles
async def get_client():
    """Función legacy para compatibilidad."""
    return await get_astra_client()


async def execute_query(query: str, *args):
    """Función legacy para compatibilidad."""
    logger.warning("execute_query no es compatible con AstraDB DataAPI. Use las funciones de colección.")
    raise NotImplementedError("Use create_collection, insert_document, find_documents, etc.")