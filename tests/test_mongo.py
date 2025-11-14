"""
Script de prueba para verificar la conexión a MongoDB Atlas.
"""
from db.mongo import get_client, get_database, get_collection, close_client
from utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def test_mongo_connection():
    """Prueba la conexión a MongoDB."""
    try:
        logger.info("=== Iniciando prueba de MongoDB ===")

        # Test 1: Conexión y Ping
        logger.info("Test 1: Verificando conexión con PING...")
        client = get_client()
        client.admin.command('ping')
        logger.info("✓ PING exitoso - Conexión establecida")

        # Test 2: Listar bases de datos
        logger.info("\nTest 2: Listando bases de datos...")
        db_list = client.list_database_names()
        logger.info(f"✓ Bases de datos disponibles: {db_list}")

        # Test 3: Información del servidor
        logger.info("\nTest 3: Información del servidor...")
        server_info = client.server_info()
        logger.info(f"✓ Versión de MongoDB: {server_info.get('version')}")
        logger.info(f"✓ Información del servidor obtenida correctamente")

        # Test 4: Obtener base de datos configurada
        logger.info("\nTest 4: Accediendo a la base de datos configurada...")
        db = get_database()
        logger.info(f"✓ Base de datos '{db.name}' accedida")

        # Test 5: Listar colecciones
        logger.info("\nTest 5: Listando colecciones...")
        collections = db.list_collection_names()
        if collections:
            logger.info(f"✓ Colecciones existentes: {collections}")
        else:
            logger.info("✓ No hay colecciones aún (base de datos nueva)")

        # Test 6: Crear colección de prueba y operaciones CRUD
        logger.info("\nTest 6: Operaciones CRUD básicas...")
        test_collection = get_collection('test_connection')

        # INSERT
        logger.info("  - Insertando documento de prueba...")
        test_doc = {
            'test': True,
            'message': 'Conexión exitosa a MongoDB',
            'timestamp': '2024-11-14'
        }
        insert_result = test_collection.insert_one(test_doc)
        logger.info(f"✓ Documento insertado con ID: {insert_result.inserted_id}")

        # FIND
        logger.info("  - Buscando documento insertado...")
        found_doc = test_collection.find_one({'test': True})
        if found_doc:
            logger.info(f"✓ Documento encontrado: {found_doc.get('message')}")

        # COUNT
        logger.info("  - Contando documentos de prueba...")
        count = test_collection.count_documents({'test': True})
        logger.info(f"✓ Documentos de prueba encontrados: {count}")

        # UPDATE
        logger.info("  - Actualizando documento...")
        update_result = test_collection.update_one(
            {'test': True},
            {'$set': {'updated': True}}
        )
        logger.info(f"✓ Documentos modificados: {update_result.modified_count}")

        # DELETE
        logger.info("  - Eliminando documentos de prueba...")
        delete_result = test_collection.delete_many({'test': True})
        logger.info(f"✓ Documentos eliminados: {delete_result.deleted_count}")

        # Test 7: Verificar índices
        logger.info("\nTest 7: Verificando índices de la colección...")
        indexes = list(test_collection.list_indexes())
        logger.info(f"✓ Índices disponibles: {len(indexes)}")

        logger.info("\n=== ✓ Todas las pruebas de MongoDB exitosas ===")
        logger.info("✅ Pinged your deployment. You successfully connected to MongoDB!")

    except Exception as e:
        logger.error(f"✗ Error durante las pruebas: {e}", exc_info=True)
        raise
    finally:
        close_client()
        logger.info("Conexión cerrada")


if __name__ == "__main__":
    test_mongo_connection()
