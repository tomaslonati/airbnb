"""
Conexión a AstraDB usando DataAPIClient.
"""

from astrapy import DataAPIClient
from typing import Optional, Any
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error

logger = get_logger(__name__)

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
        
        # Verificar conexión
        collections = _astra_database.list_collection_names()
        logger.info(f"Conectado a AstraDB. Colecciones: {collections}")

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
        logger.info(f"Documento insertado en '{collection_name}': {result.inserted_id}")
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
        logger.info(f"Encontrados {len(documents)} documentos en '{collection_name}'")
        return documents
        
    except Exception as e:
        logger.error(f"Error buscando documentos en '{collection_name}': {e}")
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


async def get_cassandra_client():
    """Alias para get_astra_client."""
    return await get_astra_client()


async def execute_query(query: str, *args):
    """Función legacy para compatibilidad."""
    logger.warning("execute_query no es compatible con AstraDB DataAPI. Use las funciones de colección.")
    raise NotImplementedError("Use create_collection, insert_document, find_documents, etc.")


# ============================================================================
# HELPERS PARA SINCRONIZACIÓN DE DISPONIBILIDAD CON POSTGRES
# ============================================================================

async def cassandra_mark_unavailable(propiedad_id: int, fechas: list):
    """
    Marca fechas como no disponibles en Cassandra.
    Decrementa noches_disponibles e incrementa noches_ocupadas.
    """
    try:
        from datetime import date
        
        # Obtener ciudad_id de PostgreSQL
        ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)
        if not ciudad_id:
            logger.warning(f"No se encontró ciudad_id para propiedad {propiedad_id}")
            return

        for fecha in fechas:
            await _update_ocupacion_ciudad(ciudad_id, fecha, occupied_delta=1, available_delta=-1)
            await _update_ocupacion_propiedad(propiedad_id, fecha, ocupada=True)
            # Remover de propiedades disponibles
            await _remove_propiedad_disponible(fecha, propiedad_id)
            
        logger.info(f"Cassandra: {len(fechas)} fechas marcadas como no disponibles para propiedad {propiedad_id}")
        
    except Exception as e:
        logger.error(f"Error en cassandra_mark_unavailable: {e}")


async def cassandra_mark_available(propiedad_id: int, fechas: list):
    """
    Marca fechas como disponibles en Cassandra.
    Incrementa noches_disponibles y decrementa noches_ocupadas.
    """
    try:
        # Obtener ciudad_id de PostgreSQL
        ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)
        if not ciudad_id:
            logger.warning(f"No se encontró ciudad_id para propiedad {propiedad_id}")
            return

        for fecha in fechas:
            await _update_ocupacion_ciudad(ciudad_id, fecha, occupied_delta=-1, available_delta=1)
            await _update_ocupacion_propiedad(propiedad_id, fecha, ocupada=False)
            # Agregar a propiedades disponibles
            await _add_propiedad_disponible(fecha, propiedad_id, ciudad_id)
            
        logger.info(f"Cassandra: {len(fechas)} fechas marcadas como disponibles para propiedad {propiedad_id}")
        
    except Exception as e:
        logger.error(f"Error en cassandra_mark_available: {e}")


async def cassandra_init_date(propiedad_id: int, fechas: list):
    """
    Inicializa fechas disponibles en Cassandra para una nueva propiedad.
    """
    try:
        # Obtener ciudad_id de PostgreSQL
        ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)
        if not ciudad_id:
            logger.warning(f"No se encontró ciudad_id para propiedad {propiedad_id}")
            return

        for fecha in fechas:
            await _update_ocupacion_ciudad(ciudad_id, fecha, occupied_delta=0, available_delta=1)
            await _update_ocupacion_propiedad(propiedad_id, fecha, ocupada=False)
            # Agregar a propiedades disponibles
            await _add_propiedad_disponible(fecha, propiedad_id, ciudad_id)
            
        logger.info(f"Cassandra: {len(fechas)} fechas inicializadas para propiedad {propiedad_id}")
        
    except Exception as e:
        logger.error(f"Error en cassandra_init_date: {e}")


async def cassandra_add_reserva(reserva_data: dict):
    """
    Agrega una reserva a las tablas de Cassandra.
    """
    try:
        reserva_id = reserva_data.get('reserva_id')
        host_id = reserva_data.get('host_id') 
        ciudad_id = reserva_data.get('ciudad_id')
        fecha_inicio = reserva_data.get('fecha_inicio')
        fecha_fin = reserva_data.get('fecha_fin')
        propiedad_id = reserva_data.get('propiedad_id')
        
        # Agregar a reservas por host
        await _add_reserva_por_host(host_id, fecha_inicio, reserva_id, reserva_data)
        
        # Agregar a reservas por ciudad  
        await _add_reserva_por_ciudad(ciudad_id, fecha_inicio, reserva_id, reserva_data)
        
        logger.info(f"Cassandra: Reserva {reserva_id} agregada correctamente")
        
    except Exception as e:
        logger.error(f"Error agregando reserva a Cassandra: {e}")


async def cassandra_remove_reserva(reserva_data: dict):
    """
    Elimina una reserva de las tablas de Cassandra.
    """
    try:
        reserva_id = reserva_data.get('reserva_id')
        host_id = reserva_data.get('host_id')
        ciudad_id = reserva_data.get('ciudad_id') 
        fecha_inicio = reserva_data.get('fecha_inicio')
        
        # Remover de reservas por host
        await _remove_reserva_por_host(host_id, fecha_inicio, reserva_id)
        
        # Remover de reservas por ciudad
        await _remove_reserva_por_ciudad(ciudad_id, fecha_inicio, reserva_id)
        
        logger.info(f"Cassandra: Reserva {reserva_id} eliminada correctamente")
        
    except Exception as e:
        logger.error(f"Error eliminando reserva de Cassandra: {e}")


# ============================================================================
# FUNCIONES AUXILIARES PARA NUEVAS TABLAS
# ============================================================================

async def _add_propiedad_disponible(fecha, propiedad_id: int, ciudad_id: int):
    """Agrega una propiedad a la tabla propiedades_disponibles_por_fecha."""
    try:
        collection = await get_collection("propiedades_disponibles_por_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        
        # Obtener datos adicionales de PostgreSQL
        propiedad_data = await _get_propiedad_data(propiedad_id)
        
        new_doc = {
            "fecha": fecha_str,
            "propiedad_id": propiedad_id,
            "ciudad_id": ciudad_id,
            "titulo": propiedad_data.get('titulo', ''),
            "precio_noche": propiedad_data.get('precio_noche', 0),
            "capacidad": propiedad_data.get('capacidad', 1),
            "tipo_propiedad": propiedad_data.get('tipo_propiedad', ''),
            "disponible": True
        }
        
        collection.insert_one(new_doc)
        
    except Exception as e:
        logger.error(f"Error agregando propiedad disponible: {e}")


async def _remove_propiedad_disponible(fecha, propiedad_id: int):
    """Remueve una propiedad de la tabla propiedades_disponibles_por_fecha."""
    try:
        collection = await get_collection("propiedades_disponibles_por_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"fecha": fecha_str, "propiedad_id": propiedad_id}
        
        collection.delete_one(filter_doc)
        
    except Exception as e:
        logger.error(f"Error removiendo propiedad disponible: {e}")


async def _add_reserva_por_host(host_id: int, fecha, reserva_id: int, reserva_data: dict):
    """Agrega una reserva a la tabla reservas_por_host_fecha."""
    try:
        collection = await get_collection("reservas_por_host_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        
        new_doc = {
            "host_id": host_id,
            "fecha": fecha_str,
            "reserva_id": reserva_id,
            "propiedad_id": reserva_data.get('propiedad_id'),
            "huesped_id": reserva_data.get('huesped_id'),
            "fecha_inicio": reserva_data.get('fecha_inicio', ''),
            "fecha_fin": reserva_data.get('fecha_fin', ''),
            "estado": reserva_data.get('estado', 'confirmada'),
            "precio_total": reserva_data.get('precio_total', 0),
            "created_at": reserva_data.get('created_at', '')
        }
        
        collection.insert_one(new_doc)
        
    except Exception as e:
        logger.error(f"Error agregando reserva por host: {e}")


async def _remove_reserva_por_host(host_id: int, fecha, reserva_id: int):
    """Remueve una reserva de la tabla reservas_por_host_fecha."""
    try:
        collection = await get_collection("reservas_por_host_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"host_id": host_id, "fecha": fecha_str, "reserva_id": reserva_id}
        
        collection.delete_one(filter_doc)
        
    except Exception as e:
        logger.error(f"Error removiendo reserva por host: {e}")


async def _add_reserva_por_ciudad(ciudad_id: int, fecha, reserva_id: int, reserva_data: dict):
    """Agrega una reserva a la tabla reservas_por_ciudad_fecha."""
    try:
        collection = await get_collection("reservas_por_ciudad_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        
        new_doc = {
            "ciudad_id": ciudad_id,
            "fecha": fecha_str,
            "reserva_id": reserva_id,
            "propiedad_id": reserva_data.get('propiedad_id'),
            "host_id": reserva_data.get('host_id'),
            "huesped_id": reserva_data.get('huesped_id'),
            "fecha_inicio": reserva_data.get('fecha_inicio', ''),
            "fecha_fin": reserva_data.get('fecha_fin', ''),
            "estado": reserva_data.get('estado', 'confirmada'),
            "precio_total": reserva_data.get('precio_total', 0),
            "created_at": reserva_data.get('created_at', '')
        }
        
        collection.insert_one(new_doc)
        
    except Exception as e:
        logger.error(f"Error agregando reserva por ciudad: {e}")


async def _remove_reserva_por_ciudad(ciudad_id: int, fecha, reserva_id: int):
    """Remueve una reserva de la tabla reservas_por_ciudad_fecha."""
    try:
        collection = await get_collection("reservas_por_ciudad_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"ciudad_id": ciudad_id, "fecha": fecha_str, "reserva_id": reserva_id}
        
        collection.delete_one(filter_doc)
        
    except Exception as e:
        logger.error(f"Error removiendo reserva por ciudad: {e}")


async def _get_propiedad_data(propiedad_id: int):
    """Obtiene datos adicionales de una propiedad desde PostgreSQL."""
    try:
        from db.postgres import get_client as get_postgres_client
        
        pool = await get_postgres_client()
        result = await pool.fetchrow(
            """
            SELECT titulo, precio_noche, capacidad, tipo_propiedad 
            FROM propiedad 
            WHERE id = $1
            """, 
            propiedad_id
        )
        
        if result:
            return dict(result)
        return {}
        
    except Exception as e:
        logger.error(f"Error obteniendo datos de propiedad {propiedad_id}: {e}")
        return {}


# ============================================================================
# FUNCIONES DE CONSULTA PARA LOS NUEVOS CU
# ============================================================================

async def get_propiedades_disponibles_por_fecha(fecha, ciudad_id: int = None, limit: int = 100):
    """
    CU 4: Obtiene TODAS las propiedades disponibles en una fecha específica.
    """
    try:
        collection = await get_collection("propiedades_disponibles_por_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"fecha": fecha_str}
        
        # Solo filtrar por ciudad si se especifica explícitamente
        if ciudad_id:
            filter_doc["ciudad_id"] = ciudad_id
            
        documents = await find_documents("propiedades_disponibles_por_fecha", filter_doc, limit=limit)
        logger.info(f"Encontradas {len(documents)} propiedades disponibles para {fecha_str}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error obteniendo propiedades disponibles: {e}")
        return []


async def get_reservas_por_host_fecha(host_id: int, fecha, limit: int = 100):
    """
    CU 6: Obtiene TODAS las reservas de un host en una fecha específica.
    """
    try:
        collection = await get_collection("reservas_por_host_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        
        # Convertir host_id a string para compatibilidad con UUID
        filter_doc = {
            "host_id": str(host_id),
            "fecha": fecha_str
        }
        
        documents = await find_documents("reservas_por_host_fecha", filter_doc, limit=limit)
        logger.info(f"Encontradas {len(documents)} reservas para host {host_id} en {fecha_str}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error obteniendo reservas por host: {e}")
        return []


async def get_reservas_por_ciudad_fecha(ciudad_id: int, fecha, limit: int = 100):
    """
    CU 5: Obtiene TODAS las reservas de una ciudad en una fecha específica.
    """
    try:
        collection = await get_collection("reservas_por_ciudad_fecha")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {
            "ciudad_id": ciudad_id,
            "fecha": fecha_str
        }
        
        documents = await find_documents("reservas_por_ciudad_fecha", filter_doc, limit=limit)
        logger.info(f"Encontradas {len(documents)} reservas para ciudad {ciudad_id} en {fecha_str}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error obteniendo reservas por ciudad: {e}")
        return []


# ============================================================================
# HELPERS EXISTENTES (NO MODIFICADOS)
# ============================================================================


async def get_ciudad_id_for_propiedad(propiedad_id: int):
    """Obtiene el ciudad_id de una propiedad desde PostgreSQL."""
    try:
        from db.postgres import get_client as get_postgres_client
        
        pool = await get_postgres_client()
        result = await pool.fetchrow(
            "SELECT ciudad_id FROM propiedad WHERE id = $1", 
            propiedad_id
        )
        
        return result['ciudad_id'] if result else None
        
    except Exception as e:
        logger.error(f"Error obteniendo ciudad_id para propiedad {propiedad_id}: {e}")
        return None


async def _update_ocupacion_ciudad(ciudad_id: int, fecha, occupied_delta: int, available_delta: int):
    """Actualiza métricas de ocupación por ciudad."""
    try:
        collection = await get_collection("ocupacion_por_ciudad")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"ciudad_id": ciudad_id, "fecha": fecha_str}
        
        # Buscar documento existente
        existing = await find_documents("ocupacion_por_ciudad", filter_doc, limit=1)
        
        if existing:
            doc = existing[0]
            noches_ocupadas = max(0, doc.get('noches_ocupadas', 0) + occupied_delta)
            noches_disponibles = max(0, doc.get('noches_disponibles', 0) + available_delta)
            
            # Solo actualizar campos no-clave primaria
            update_fields = {
                "noches_ocupadas": noches_ocupadas,
                "noches_disponibles": noches_disponibles
            }
            
            collection.update_one(
                filter_doc, 
                {"$set": update_fields}
            )
        else:
            # Insertar nuevo documento
            new_doc = {
                "ciudad_id": ciudad_id,
                "fecha": fecha_str,
                "noches_ocupadas": max(0, occupied_delta),
                "noches_disponibles": max(0, available_delta)
            }
            
            collection.insert_one(new_doc)
        
    except Exception as e:
        logger.error(f"Error actualizando ocupación ciudad: {e}")


async def _update_ocupacion_propiedad(propiedad_id: int, fecha, ocupada: bool):
    """Actualiza estado de ocupación por propiedad."""
    try:
        collection = await get_collection("ocupacion_por_propiedad")
        
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"propiedad_id": propiedad_id, "fecha": fecha_str}
        
        # Buscar si el documento existe
        existing = await find_documents("ocupacion_por_propiedad", filter_doc, limit=1)
        
        if existing:
            # Solo actualizar el campo ocupada (no las claves primarias)
            collection.update_one(
                filter_doc, 
                {"$set": {"ocupada": ocupada}}
            )
        else:
            # Insertar nuevo documento con todas las claves
            new_doc = {
                "propiedad_id": propiedad_id,
                "fecha": fecha_str,
                "ocupada": ocupada
            }
            collection.insert_one(new_doc)
        
    except Exception as e:
        logger.error(f"Error actualizando ocupación propiedad: {e}")