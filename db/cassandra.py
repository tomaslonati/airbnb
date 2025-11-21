"""
Conexión a AstraDB usando DataAPIClient.
"""

from astrapy import DataAPIClient
from typing import Optional, Any
from datetime import date
from config import db_config
from utils.logging import get_logger
from utils.retry import retry_on_connection_error
import uuid

logger = get_logger(__name__)

# Clientes globales
_astra_client: Optional[DataAPIClient] = None
_astra_database: Optional[Any] = None


def generate_deterministic_uuid(base_value: int, entity_type: str = "entity") -> str:
    """
    Genera un UUID determinístico basado en un valor entero y tipo de entidad.
    Esto asegura que el mismo ID siempre genere el mismo UUID.
    """
    # Crear un namespace UUID basado en el tipo de entidad
    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, f"airbnb.{entity_type}")
    # Generar UUID determinístico basado en el valor
    deterministic_uuid = uuid.uuid5(namespace, str(base_value))
    return str(deterministic_uuid)


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
            collection = database.create_collection(
                collection_name, dimension=dimension)
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
        logger.info(
            f"Documento insertado en '{collection_name}': {result.inserted_id}")
        return result

    except Exception as e:
        logger.error(f"Error insertando documento en '{collection_name}': {e}")
        raise


async def insert_many_documents(collection_name: str, documents: list):
    """Inserta múltiples documentos en una colección de forma eficiente."""
    try:
        if not documents:
            return []

        collection = await get_collection(collection_name)
        result = collection.insert_many(documents)
        logger.info(
            f"Insertados {len(documents)} documentos en '{collection_name}' (batch)")
        return result

    except Exception as e:
        logger.error(
            f"Error insertando documentos en lote en '{collection_name}': {e}")
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
        logger.info(
            f"Encontrados {len(documents)} documentos en '{collection_name}'")
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
    logger.warning(
        "execute_query no es compatible con AstraDB DataAPI. Use las funciones de colección.")
    raise NotImplementedError(
        "Use create_collection, insert_document, find_documents, etc.")


# ============================================================================
# HELPERS PARA SINCRONIZACIÓN DE DISPONIBILIDAD CON POSTGRES
# ============================================================================

async def cassandra_mark_unavailable(propiedad_id: int, fechas: list, ciudad_id: int = None):
    """
    Marca fechas como no disponibles en Cassandra.
    Decrementa noches_disponibles e incrementa noches_ocupadas.
    """
    try:
        from datetime import date

        # Si no se proporciona ciudad_id, obtenerlo de PostgreSQL
        if ciudad_id is None:
            ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)

        if not ciudad_id:
            logger.warning(
                f"No se encontró ciudad_id para propiedad {propiedad_id}")
            return

        for fecha in fechas:
            await _update_ocupacion_ciudad(ciudad_id, fecha, occupied_delta=1, available_delta=-1)
            await _update_ocupacion_propiedad(propiedad_id, fecha, ocupada=True)
            # Remover de propiedades disponibles
            await _remove_propiedad_disponible(fecha, propiedad_id)

        logger.info(
            f"Cassandra: {len(fechas)} fechas marcadas como no disponibles para propiedad {propiedad_id}")

    except Exception as e:
        logger.error(f"Error en cassandra_mark_unavailable: {e}")


async def cassandra_mark_available(propiedad_id: int, fechas: list, ciudad_id: int = None):
    """
    Marca fechas como disponibles en Cassandra.
    Incrementa noches_disponibles y decrementa noches_ocupadas.
    """
    try:
        # Si no se proporciona ciudad_id, obtenerlo de PostgreSQL
        if ciudad_id is None:
            ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)

        if not ciudad_id:
            logger.warning(
                f"No se encontró ciudad_id para propiedad {propiedad_id}")
            return

        for fecha in fechas:
            await _update_ocupacion_ciudad(ciudad_id, fecha, occupied_delta=-1, available_delta=1)
            await _update_ocupacion_propiedad(propiedad_id, fecha, ocupada=False)
            # Agregar a propiedades disponibles
            await _add_propiedad_disponible(fecha, propiedad_id, ciudad_id)

        logger.info(
            f"Cassandra: {len(fechas)} fechas marcadas como disponibles para propiedad {propiedad_id}")

    except Exception as e:
        logger.error(f"Error en cassandra_mark_available: {e}")


async def cassandra_init_date(propiedad_id: int, fechas: list, ciudad_id: int = None):
    """
    Inicializa fechas disponibles en Cassandra para una nueva propiedad usando batch operations.
    """
    try:
        # Si no se proporciona ciudad_id, obtenerlo de PostgreSQL
        if ciudad_id is None:
            ciudad_id = await get_ciudad_id_for_propiedad(propiedad_id)

        if not ciudad_id:
            logger.warning(
                f"No se encontró ciudad_id para propiedad {propiedad_id}")
            return

        import asyncio

        # Preparar tareas para ejecutar en paralelo
        tasks = []

        # Actualizar ocupación por ciudad usando UPDATE atómico
        for fecha in fechas:
            fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
            # UPDATE atómico: incrementar noches_disponibles para esta ciudad/fecha
            await _update_ocupacion_ciudad(ciudad_id, fecha_str, occupied_delta=0, available_delta=1)

        # 2. Preparar documentos para ocupación por propiedad y disponibilidad
        ocupacion_propiedad_docs = []
        disponibilidad_docs = []

        # Preparar documentos restantes para batch insert
        for fecha in fechas:
            fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)

            # Documento para ocupación por propiedad
            ocupacion_propiedad_docs.append({
                "propiedad_id": propiedad_id,  # bigint según esquema de AstraDB
                "fecha": fecha_str,
                "ocupada": False
            })

            # Documento para disponibilidad - usar colección correcta
            disponibilidad_docs.append({
                "fecha": fecha_str,
                "propiedades_disponibles": [propiedad_id],
                "ciudad_ids": [ciudad_id]
            })

        # Ejecutar operaciones batch en paralelo (solo las que no son ocupacion_por_ciudad)
        if ocupacion_propiedad_docs:
            tasks.append(insert_many_documents(
                "ocupacion_por_propiedad", ocupacion_propiedad_docs))
        if disponibilidad_docs:
            tasks.append(insert_many_documents(
                "propiedades_disponibles_por_fecha", disponibilidad_docs))

        # Ejecutar todas las tareas en paralelo
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(
            f"Cassandra: {len(fechas)} fechas inicializadas para propiedad {propiedad_id} (optimizado)")

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

        logger.info(
            f"[CU6] cassandra_add_reserva llamado con: reserva_id={reserva_id}, host_id={host_id}, fecha_inicio={fecha_inicio}")

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
            "nombre": propiedad_data.get('nombre', ''),
            "capacidad": propiedad_data.get('capacidad', 1),
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

        # Buscar todos los documentos para esta fecha que contengan la propiedad
        docs = await find_documents("propiedades_disponibles_por_fecha", {"fecha": fecha_str}, limit=50)

        for doc in docs:
            propiedades = doc.get("propiedades_disponibles", [])
            if propiedad_id in propiedades:
                # Remover la propiedad del array
                propiedades.remove(propiedad_id)

                if propiedades:  # Si aún quedan propiedades
                    # Actualizar el documento con el array modificado
                    collection.update_one(
                        {"_id": doc["_id"]},
                        {"$set": {"propiedades_disponibles": propiedades}}
                    )
                else:  # Si no quedan propiedades, eliminar el documento completo
                    collection.delete_one({"_id": doc["_id"]})

                logger.debug(
                    f"Propiedad {propiedad_id} removida de documento para fecha {fecha_str}")

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
            "status": reserva_data.get('estado', 'confirmada'),
            "total_price": float(reserva_data.get('precio_total', 0))
        }

        logger.info(
            f"[CU6] Insertando reserva en reservas_por_host_fecha: {new_doc}")
        collection.insert_one(new_doc)
        logger.info(
            f"[CU6] ✓ Reserva {reserva_id} insertada exitosamente para host {host_id} en fecha {fecha_str}")

    except Exception as e:
        logger.error(f"[CU6] ✗ Error agregando reserva por host: {e}")


async def _remove_reserva_por_host(host_id: int, fecha, reserva_id: int):
    """Remueve una reserva de la tabla reservas_por_host_fecha."""
    try:
        collection = await get_collection("reservas_por_host_fecha")

        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {
            "host_id": host_id,
            "fecha": fecha_str,
            "reserva_id": reserva_id
        }

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
        filter_doc = {"ciudad_id": ciudad_id,
                      "fecha": fecha_str, "reserva_id": reserva_id}

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
            SELECT nombre, capacidad
            FROM propiedad 
            WHERE id = $1
            """,
            propiedad_id
        )

        if result:
            return dict(result)
        return {}

    except Exception as e:
        logger.error(
            f"Error obteniendo datos de propiedad {propiedad_id}: {e}")
        return {}


# ============================================================================
# FUNCIONES DE CONSULTA PARA LOS NUEVOS CU
# ============================================================================

async def get_propiedades_disponibles_por_fecha(fecha, ciudad_id: int = None, limit: int = 100):
    """
    CU 4: Obtiene propiedades disponibles en una fecha específica.
    USA SOLO CASSANDRA - Información básica desde propiedades_disponibles_por_fecha.
    """
    try:
        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"fecha": fecha_str}

        documents = await find_documents("propiedades_disponibles_por_fecha", filter_doc, limit=limit)
        logger.info(
            f"Encontrados {len(documents)} documentos de disponibilidad para {fecha_str}")

        propiedades_resultado = []
        propiedades_ids_procesados = set()

        for doc in documents:
            props_disponibles = doc.get('propiedades_disponibles', [])
            ciudades_doc = doc.get('ciudad_ids', [])

            # Filtrar por ciudad si se especifica
            if ciudad_id and ciudad_id not in ciudades_doc:
                continue

            # Procesar cada propiedad disponible
            for prop_id in props_disponibles:
                if prop_id not in propiedades_ids_procesados:
                    propiedades_ids_procesados.add(prop_id)

                    # Determinar ciudad (usar la primera del documento)
                    ciudad_prop_id = ciudades_doc[0] if ciudades_doc else 1

                    # Crear información básica usando solo datos disponibles
                    prop_info = {
                        'propiedad_id': prop_id,
                        'propiedad_nombre': f'Propiedad #{prop_id}',
                        'precio_noche': 75.0,  # Precio base estándar
                        'capacidad_huespedes': 4,  # Capacidad base estándar
                        'ciudad_nombre': _get_ciudad_nombre(ciudad_prop_id),
                        'ciudad_id': ciudad_prop_id,
                        'wifi': True,  # Asumir WiFi disponible
                        'fecha_disponible': fecha_str
                    }
                    propiedades_resultado.append(prop_info)

        logger.info(
            f"[CU4 SOLO CASSANDRA] Encontradas {len(propiedades_resultado)} propiedades disponibles para {fecha_str}")
        return propiedades_resultado

    except Exception as e:
        logger.error(f"Error obteniendo propiedades disponibles: {e}")
        return []


def _get_ciudad_nombre(ciudad_id: int) -> str:
    """Mapeo de IDs de ciudad a nombres (sin consulta SQL)."""
    ciudades_map = {
        1: "Buenos Aires",
        2: "Madrid",
        3: "Barcelona",
        4: "Lima",
        5: "Ciudad de México",
        6: "São Paulo",
        7: "Bogotá",
        8: "Santiago"
    }
    return ciudades_map.get(ciudad_id, f"Ciudad {ciudad_id}")


async def get_reservas_por_host_fecha(host_id: int, fecha, limit: int = 100):
    """
    CU 6: Obtiene TODAS las reservas de un host en una fecha específica.
    """
    try:
        collection = await get_collection("reservas_por_host_fecha")

        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)

        filter_doc = {
            "host_id": host_id,
            "fecha": fecha_str
        }

        documents = await find_documents("reservas_por_host_fecha", filter_doc, limit=limit)
        logger.info(
            f"Encontradas {len(documents)} reservas para host {host_id} en {fecha_str}")

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

        # Convertir ciudad_id a string para compatibilidad
        filter_doc = {
            "ciudad_id": str(ciudad_id),
            "fecha": fecha_str
        }

        documents = await find_documents("reservas_por_ciudad_fecha", filter_doc, limit=limit)
        logger.info(
            f"Encontradas {len(documents)} reservas para ciudad {ciudad_id} en {fecha_str}")

        return documents

    except Exception as e:
        logger.error(f"Error obteniendo reservas por ciudad: {e}")
        return []


async def get_propiedades_ciudad_capacidad_wifi(ciudad_id: int, min_capacidad: int = 3, wifi_required: bool = True, limit: int = 100):
    """
    CU 3: Obtiene propiedades de una ciudad específica con capacidad ≥ min_capacidad y WiFi.
    OPTIMIZADA: Usa SOLO Cassandra con la colección 'properties_by_city_wifi_capacity'.
    """
    try:
        # Consulta simple a la colección optimizada - SOLO CASSANDRA
        collection = await get_collection("properties_by_city_wifi_capacity")

        # Mapear ID a nombre de ciudad
        ciudad_nombres = {
            1: "Buenos Aires",
            2: "Madrid",
            3: "Barcelona",
            4: "Lima",
            5: "Ciudad de México",
            6: "Bariloche",
            7: "Mar del Plata"
        }
        ciudad_nombre = ciudad_nombres.get(ciudad_id, f"Ciudad_{ciudad_id}")

        # Filtrar por ciudad en Cassandra
        filter_doc = {
            "ciudad_nombre": ciudad_nombre
        }

        documents = await find_documents("properties_by_city_wifi_capacity", filter_doc, limit=limit)

        # Filtrar en memoria por capacidad y WiFi
        propiedades_filtradas = []
        for doc in documents:
            capacidad = doc.get('capacidad')
            wifi = doc.get('tiene_wifi', False)

            # Validar capacidad (≥ min_capacidad)
            if capacidad is not None and int(capacidad) >= min_capacidad:
                # Validar WiFi si es requerido
                if not wifi_required or wifi:
                    # Formatear el documento para compatibilidad
                    prop_doc = {
                        'propiedad_id': doc.get('propiedad_id'),
                        'propiedad_nombre': doc.get('nombre_propiedad', 'Sin nombre'),
                        'precio_noche': 75.0,  # Precio por defecto desde Cassandra
                        'capacidad_huespedes': doc.get('capacidad'),
                        'wifi': doc.get('tiene_wifi', False),
                        'ciudad_nombre': doc.get('ciudad_nombre'),
                        'ciudad_id': ciudad_id
                    }
                    propiedades_filtradas.append(prop_doc)

        logger.info(
            f"[CASSANDRA ONLY] Encontradas {len(propiedades_filtradas)} propiedades en {ciudad_nombre} con capacidad ≥{min_capacidad} y WiFi={wifi_required}")

        return propiedades_filtradas

    except Exception as e:
        logger.error(
            f"Error obteniendo propiedades por ciudad con filtros: {e}")
        return []


# FUNCIONES DE ACTUALIZACIÓN DE OCUPACIÓN
# ============================================================================

async def cassandra_sync_propiedad_cu3(propiedad_id: int, ciudad_id: int, nombre: str, capacidad: int, servicios_ids: list):
    """
    Sincroniza una nueva propiedad con la colección CU3 si cumple los criterios.
    Se llama cuando se crea una nueva propiedad.
    """
    try:
        # Verificar si la propiedad cumple criterios del CU3: capacidad ≥3 y WiFi
        if capacidad >= 3 and 1 in servicios_ids:  # servicio_id = 1 es WiFi
            # Obtener nombre de la ciudad
            ciudad_nombres = {
                1: "Buenos Aires",
                2: "Madrid",
                3: "Barcelona",
                4: "Lima",
                5: "Ciudad de México",
                6: "Bariloche",
                7: "Mar del Plata"
            }
            ciudad_nombre = ciudad_nombres.get(
                ciudad_id, f"Ciudad_{ciudad_id}")

            # Crear documento para la colección CU3
            propiedad_cu3 = {
                "ciudad_nombre": ciudad_nombre,
                "tiene_wifi": True,  # Confirmado por estar en servicios_ids
                "capacidad": capacidad,
                "propiedad_id": propiedad_id,
                "nombre_propiedad": nombre
            }

            # Insertar en la colección optimizada para CU3
            await insert_document("properties_by_city_wifi_capacity", propiedad_cu3)

            logger.info(
                f"✅ Propiedad {propiedad_id} agregada a CU3 Cassandra: {nombre} (cap:{capacidad}, wifi:true)")
        else:
            logger.info(
                f"ℹ️  Propiedad {propiedad_id} NO cumple criterios CU3: {nombre} (cap:{capacidad}, wifi:{1 in servicios_ids})")

    except Exception as e:
        logger.error(
            f"Error sincronizando propiedad {propiedad_id} con CU3 Cassandra: {e}")


async def cassandra_remove_propiedad_cu3(propiedad_id: int):
    """
    Remueve una propiedad de la colección CU3 cuando se elimina o actualiza.
    """
    try:
        collection = await get_collection("properties_by_city_wifi_capacity")

        # Buscar y eliminar el documento de la propiedad
        filter_doc = {"propiedad_id": propiedad_id}
        result = collection.delete_one(filter_doc)

        if result.deleted_count > 0:
            logger.info(
                f"✅ Propiedad {propiedad_id} removida de CU3 Cassandra")
        else:
            logger.info(
                f"ℹ️  Propiedad {propiedad_id} no estaba en CU3 Cassandra")

    except Exception as e:
        logger.error(
            f"Error removiendo propiedad {propiedad_id} de CU3 Cassandra: {e}")
        logger.error(
            f"Error obteniendo propiedades por ciudad con filtros: {e}")
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
        logger.info(
            f"Encontradas {len(documents)} reservas para ciudad {ciudad_id} en {fecha_str}")

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
        logger.error(
            f"Error obteniendo ciudad_id para propiedad {propiedad_id}: {e}")
        return None


async def _update_ocupacion_ciudad(ciudad_id: int, fecha, occupied_delta: int, available_delta: int):
    """Actualiza métricas de ocupación por ciudad usando patrón read-compute-write."""
    try:
        collection = await get_collection("ocupacion_por_ciudad")

        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(
            fecha) if isinstance(fecha, date) else str(fecha)
        filter_doc = {"ciudad_id": ciudad_id, "fecha": fecha_str}

        # PASO 1: Leer documento actual
        existing_doc = collection.find_one(filter_doc)

        if existing_doc:
            # PASO 2: Calcular nuevos valores
            new_noches_ocupadas = existing_doc.get(
                "noches_ocupadas", 0) + occupied_delta
            new_noches_disponibles = existing_doc.get(
                "noches_disponibles", 0) + available_delta
        else:
            # Si no existe, usar los deltas como valores iniciales
            new_noches_ocupadas = max(0, occupied_delta)
            new_noches_disponibles = max(0, available_delta)

        # PASO 3: Actualizar usando updateOne con $set (compatible con Tables)
        # IMPORTANTE: NO incluir PRIMARY KEY (ciudad_id, fecha) en $set
        update_doc = {
            "noches_ocupadas": max(0, new_noches_ocupadas),  # Nunca negativos
            "noches_disponibles": max(0, new_noches_disponibles)
        }

        # Usar updateOne con $set para Tables (NO incluir PK en el update)
        collection.update_one(
            filter_doc,
            {"$set": update_doc},
            upsert=True
        )

        logger.debug(f"Read-compute-write ocupación: ciudad {ciudad_id}, fecha {fecha_str}, "
                     f"ocupadas={new_noches_ocupadas}, disponibles={new_noches_disponibles}")

    except Exception as e:
        logger.error(f"Error actualizando ocupación ciudad: {e}")


async def _update_ocupacion_propiedad(propiedad_id: int, fecha, ocupada: bool):
    """Actualiza estado de ocupación por propiedad."""
    try:
        collection = await get_collection("ocupacion_por_propiedad")

        fecha_str = fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha)
        filter_doc = {"propiedad_id": propiedad_id,
                      "fecha": fecha_str}  # usar bigint como en esquema

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
                "propiedad_id": propiedad_id,  # bigint según esquema
                "fecha": fecha_str,
                "ocupada": ocupada
            }
            collection.insert_one(new_doc)

    except Exception as e:
        logger.error(f"Error actualizando ocupación propiedad: {e}")


async def confirmar_reserva_ocupacion(ciudad_id: int, fechas: list):
    """
    Actualiza ocupacion_por_ciudad cuando se CONFIRMA una reserva.
    Mueve 1 noche de disponible → ocupada para cada fecha.
    """
    try:
        for fecha in fechas:
            await _update_ocupacion_ciudad(
                ciudad_id=ciudad_id,
                fecha=fecha,
                occupied_delta=1,      # +1 ocupada
                available_delta=-1     # -1 disponible
            )
        logger.info(
            f"✅ Reserva confirmada: ciudad {ciudad_id}, {len(fechas)} fechas")

    except Exception as e:
        logger.error(f"Error confirmando reserva ocupación: {e}")
        raise


async def cancelar_reserva_ocupacion(ciudad_id: int, fechas: list):
    """
    Actualiza ocupacion_por_ciudad cuando se CANCELA una reserva.
    Mueve 1 noche de ocupada → disponible para cada fecha.
    """
    try:
        for fecha in fechas:
            await _update_ocupacion_ciudad(
                ciudad_id=ciudad_id,
                fecha=fecha,
                occupied_delta=-1,     # -1 ocupada
                available_delta=1      # +1 disponible
            )
        logger.info(
            f"✅ Reserva cancelada: ciudad {ciudad_id}, {len(fechas)} fechas")

    except Exception as e:
        logger.error(f"Error cancelando reserva ocupación: {e}")
        raise


async def delete_collection_data(collection_name: str):
    """Elimina todos los documentos de una colección."""
    try:
        collection = await get_collection(collection_name)
        result = collection.delete_many({})
        logger.info(
            f"✅ Eliminados {result.deleted_count} documentos de {collection_name}")
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error eliminando datos de {collection_name}: {e}")
        raise
