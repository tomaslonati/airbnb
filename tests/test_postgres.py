"""
Script de prueba para verificar la conexión a Supabase PostgreSQL.
"""
import asyncio
from db.postgres import get_client, execute_query, execute_command, close_client
from utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def test_postgres_connection():
    """Prueba la conexión a PostgreSQL/Supabase."""
    try:
        logger.info("=== Iniciando prueba de PostgreSQL/Supabase ===")
        
        # Test 1: Verificar conexión básica
        logger.info("Test 1: Verificando conexión con SELECT NOW()...")
        pool = await get_client()
        result = await execute_query("SELECT NOW() as current_time")
        logger.info(f"✓ Conexión exitosa. Hora actual: {result[0]['current_time']}")
        
        # Test 2: Verificar versión de PostgreSQL
        logger.info("\nTest 2: Verificando versión de PostgreSQL...")
        result = await execute_query("SELECT version()")
        version = result[0]['version']
        logger.info(f"✓ Versión: {version[:50]}...")
        
        # Test 3: Verificar extensiones disponibles
        logger.info("\nTest 3: Verificando extensiones disponibles...")
        result = await execute_query("""
            SELECT extname, extversion 
            FROM pg_extension 
            ORDER BY extname
            LIMIT 5
        """)
        logger.info("✓ Extensiones instaladas (primeras 5):")
        for row in result:
            logger.info(f"  - {row['extname']}: {row['extversion']}")
        
        # Test 4: Verificar esquemas disponibles
        logger.info("\nTest 4: Verificando esquemas disponibles...")
        result = await execute_query("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_toast', 'pg_catalog', 'information_schema')
            ORDER BY schema_name
        """)
        logger.info("✓ Esquemas disponibles:")
        for row in result:
            logger.info(f"  - {row['schema_name']}")
        
        # Test 5: Crear una tabla de prueba
        logger.info("\nTest 5: Creando tabla de prueba...")
        await execute_command("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ Tabla 'test_connection' creada")
        
        # Test 6: Insertar datos de prueba
        logger.info("\nTest 6: Insertando datos de prueba...")
        await execute_command(
            "INSERT INTO test_connection (message) VALUES ($1)",
            "¡Conexión exitosa desde Python!"
        )
        logger.info("✓ Dato insertado")
        
        # Test 7: Consultar datos insertados
        logger.info("\nTest 7: Consultando datos insertados...")
        result = await execute_query("""
            SELECT id, message, created_at 
            FROM test_connection 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        logger.info("✓ Datos en la tabla:")
        for row in result:
            logger.info(f"  - ID {row['id']}: {row['message']} ({row['created_at']})")
        
        # Test 8: Contar registros
        logger.info("\nTest 8: Contando registros...")
        result = await execute_query("SELECT COUNT(*) as total FROM test_connection")
        total = result[0]['total']
        logger.info(f"✓ Total de registros en test_connection: {total}")
        
        # Test 9: Actualizar un registro
        logger.info("\nTest 9: Actualizando registro...")
        await execute_command(
            "UPDATE test_connection SET message = $1 WHERE id = (SELECT MAX(id) FROM test_connection)",
            "¡Mensaje actualizado correctamente!"
        )
        logger.info("✓ Registro actualizado")
        
        # Test 10: Verificar la actualización
        logger.info("\nTest 10: Verificando actualización...")
        result = await execute_query("""
            SELECT message 
            FROM test_connection 
            WHERE id = (SELECT MAX(id) FROM test_connection)
        """)
        logger.info(f"✓ Mensaje actualizado: {result[0]['message']}")
        
        # Test 11: Verificar pool de conexiones
        logger.info("\nTest 11: Verificando estado del pool...")
        logger.info(f"✓ Tamaño del pool: {pool.get_size()}")
        logger.info(f"✓ Conexiones libres: {pool.get_idle_size()}")
        
        # Opcional: Limpiar tabla de prueba (comentado para verificación)
        # logger.info("\nLimpiando tabla de prueba...")
        # await execute_command("DROP TABLE IF EXISTS test_connection")
        # logger.info("✓ Tabla eliminada")
        
        logger.info("\n💾 Tabla 'test_connection' guardada en Supabase para verificación")
        logger.info("\n=== ✓ Todas las pruebas exitosas ===")
        
    except Exception as e:
        logger.error(f"✗ Error durante las pruebas: {e}", exc_info=True)
        raise
    finally:
        await close_client()
        logger.info("Conexión cerrada")


if __name__ == "__main__":
    asyncio.run(test_postgres_connection())

