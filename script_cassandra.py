# script_cassandra.py (Versión v3 - DataAPI Completa)
import asyncio
from dotenv import load_dotenv, find_dotenv
from utils.logging import get_logger

# Importamos el módulo de Cassandra de TU PROPIO proyecto
from db import cassandra 

logger = get_logger(__name__)

# --- 1. LOS DATOS (¡Completos, con WIFI!) ---
COLLECTION_NAME = "properties_by_city_wifi_capacity"

DOCUMENTOS = [
    {
        "ciudad_nombre": "Buenos Aires",
        "tiene_wifi": True,
        "capacidad": 4,
        "propiedad_id": 26,
        "nombre_propiedad": "casa con pileta"
    },
    {
        "ciudad_nombre": "Buenos Aires",
        "tiene_wifi": True,
        "capacidad": 4,
        "propiedad_id": 24,
        "nombre_propiedad": "depto en Palermo"
    },
    {
        "ciudad_nombre": "Buenos Aires",
        "tiene_wifi": False,
        "capacidad": 3,
        "propiedad_id": 25,
        "nombre_propiedad": "monoambiente en el centro"
    }
]

async def crear_y_poblar_cassandra():
    """
    Script para CREAR la colección (tabla) y POBLARLA (insertar datos)
    usando la DataAPI de AstraDB.
    """
    logger.info(f"Iniciando script para '{COLLECTION_NAME}'...")
    load_dotenv(find_dotenv()) # Cargar el .env

    try:
        # --- 2. PASO DE CREACIÓN (Lo que faltaba) ---
        # (Asumimos que tu db/cassandra.py tiene una función 'create_collection')
        logger.info(f"Intentando crear la colección '{COLLECTION_NAME}' (si no existe)...")
        
        # Intentamos crear la colección. Si ya existe, AstraDB dará un error
        # que podemos ignorar si es 'COLLECTION_ALREADY_EXISTS'.
        try:
            await cassandra.create_collection(COLLECTION_NAME)
            logger.info(f"¡Colección '{COLLECTION_NAME}' creada exitosamente!")
        except Exception as e:
            if "COLLECTION_ALREADY_EXISTS" in str(e):
                logger.warning(f"La colección '{COLLECTION_NAME}' ya existe. Continuando...")
            else:
                # Si es otro error, lo lanzamos
                raise e

        # --- 3. PASO DE POBLADO (Insertar) ---
        logger.info(f"Insertando {len(DOCUMENTOS)} documentos en '{COLLECTION_NAME}'...")
        
        for i, doc in enumerate(DOCUMENTOS):
            logger.info(f"Insertando documento {i+1}/{len(DOCUMENTOS)} (ID: {doc['propiedad_id']})...")
            
            # Usamos la función 'insert_document' que nos pidió el error
            await cassandra.insert_document(COLLECTION_NAME, doc)
            
            logger.info(f"...Documento {doc['propiedad_id']} insertado.")

        logger.info(f"¡Éxito! Datos insertados en '{COLLECTION_NAME}'.")

    except AttributeError as e:
        logger.error(f"¡Error! El módulo 'db/cassandra.py' no tiene la función 'create_collection' o 'insert_document'.")
        logger.error(f"Error detallado: {e}")
    except Exception as e:
        logger.error(f"Error al poblar Cassandra: {e}")
    
    finally:
        if hasattr(cassandra, 'close_session'):
            await cassandra.close_session()
            logger.info("Conexión a Cassandra cerrada.")


if __name__ == "__main__":
    asyncio.run(crear_y_poblar_cassandra())