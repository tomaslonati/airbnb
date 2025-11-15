"""
Script de prueba para verificar las funciones helper de PostgreSQL/Supabase.
Similar a test_redis.py pero para PostgreSQL.
"""
import asyncio
from db.postgres import (
    get_client, 
    close_client,
    ping,
    insert_one,
    get_by_id,
    update_by_id,
    delete_by_id,
    get_all,
    count_records,
    execute_query,
    execute_transaction,
    table_exists
)
from utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def test_postgres_helpers():
    """Prueba las funciones helper de PostgreSQL."""
    try:
        logger.info("=== Iniciando prueba de helpers de PostgreSQL/Supabase ===")
        
        # Test 1: Ping (similar a Redis)
        logger.info("Test 1: Verificando conexión con ping()...")
        is_connected = await ping()
        logger.info(f"✓ Conexión activa: {is_connected}")
        
        # Test 2: Verificar si tabla existe
        logger.info("\nTest 2: Verificando si tabla 'test_users' existe...")
        exists = await table_exists('test_users')
        logger.info(f"✓ Tabla 'test_users' existe: {exists}")
        
        # Test 3: Crear tabla de prueba
        logger.info("\nTest 3: Creando tabla 'test_users'...")
        await execute_query("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                city VARCHAR(50),
                age INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✓ Tabla 'test_users' creada")
        
        # Verificar de nuevo
        exists = await table_exists('test_users')
        logger.info(f"✓ Tabla ahora existe: {exists}")
        
        # Test 4: Insertar registros con insert_one (similar a Redis set_key)
        logger.info("\nTest 4: Insertando usuarios con insert_one()...")
        
        user1_id = await insert_one('test_users', {
            'name': 'Juan Pérez',
            'email': 'juan@example.com',
            'city': 'Buenos Aires',
            'age': 30
        })
        logger.info(f"✓ Usuario 1 insertado con ID: {user1_id}")
        
        user2_id = await insert_one('test_users', {
            'name': 'María García',
            'email': 'maria@example.com',
            'city': 'Córdoba',
            'age': 25
        })
        logger.info(f"✓ Usuario 2 insertado con ID: {user2_id}")
        
        user3_id = await insert_one('test_users', {
            'name': 'Carlos López',
            'email': 'carlos@example.com',
            'city': 'Buenos Aires',
            'age': 35
        })
        logger.info(f"✓ Usuario 3 insertado con ID: {user3_id}")
        
        # Test 5: Obtener por ID (similar a Redis get_key)
        logger.info("\nTest 5: Obteniendo usuario por ID con get_by_id()...")
        user = await get_by_id('test_users', user1_id)
        logger.info(f"✓ Usuario obtenido: {user['name']} - {user['email']} - {user['city']}")
        
        # Test 6: Contar registros
        logger.info("\nTest 6: Contando registros totales...")
        total = await count_records('test_users')
        logger.info(f"✓ Total de usuarios: {total}")
        
        # Contar con filtro
        ba_users = await count_records('test_users', 'city = $1', 'Buenos Aires')
        logger.info(f"✓ Usuarios en Buenos Aires: {ba_users}")
        
        # Test 7: Obtener todos con paginación
        logger.info("\nTest 7: Obteniendo todos los usuarios con get_all()...")
        users = await get_all('test_users', limit=10)
        logger.info(f"✓ Usuarios obtenidos: {len(users)}")
        for u in users:
            logger.info(f"  - ID {u['id']}: {u['name']} ({u['city']}, {u['age']} años)")
        
        # Test 8: Actualizar registro (similar a Redis set_key para actualizar)
        logger.info("\nTest 8: Actualizando usuario con update_by_id()...")
        await update_by_id('test_users', user1_id, {
            'city': 'Mendoza',
            'age': 31
        })
        logger.info(f"✓ Usuario {user1_id} actualizado")
        
        # Verificar actualización
        updated_user = await get_by_id('test_users', user1_id)
        logger.info(f"✓ Datos actualizados: {updated_user['name']} - {updated_user['city']} - {updated_user['age']} años")
        
        # Test 9: Consultas personalizadas
        logger.info("\nTest 9: Consultas personalizadas con execute_query()...")
        young_users = await execute_query(
            "SELECT * FROM test_users WHERE age < $1 ORDER BY age",
            32
        )
        logger.info(f"✓ Usuarios menores de 32 años: {len(young_users)}")
        for u in young_users:
            logger.info(f"  - {u['name']}: {u['age']} años")
        
        # Test 10: Transacciones
        logger.info("\nTest 10: Ejecutando transacción con execute_transaction()...")
        await execute_transaction([
            ("INSERT INTO test_users (name, email, city, age) VALUES ($1, $2, $3, $4)", 
             'Ana Torres', 'ana@example.com', 'Rosario', 28),
            ("UPDATE test_users SET age = age + 1 WHERE city = $1", 'Buenos Aires')
        ])
        logger.info("✓ Transacción ejecutada (nuevo usuario + actualización de edades)")
        
        # Verificar cambios de la transacción
        total_after = await count_records('test_users')
        logger.info(f"✓ Total de usuarios después de transacción: {total_after}")
        
        # Test 11: Agrupar y agregar datos
        logger.info("\nTest 11: Consultas de agregación...")
        stats = await execute_query("""
            SELECT 
                city,
                COUNT(*) as usuarios,
                AVG(age) as edad_promedio,
                MIN(age) as edad_min,
                MAX(age) as edad_max
            FROM test_users
            GROUP BY city
            ORDER BY usuarios DESC
        """)
        logger.info("✓ Estadísticas por ciudad:")
        for stat in stats:
            logger.info(f"  - {stat['city']}: {stat['usuarios']} usuarios, edad promedio: {stat['edad_promedio']:.1f}")
        
        # Test 12: Búsqueda con LIKE
        logger.info("\nTest 12: Búsqueda con LIKE...")
        search_results = await execute_query(
            "SELECT name, email FROM test_users WHERE name ILIKE $1",
            '%ar%'
        )
        logger.info(f"✓ Usuarios con 'ar' en el nombre: {len(search_results)}")
        for result in search_results:
            logger.info(f"  - {result['name']} ({result['email']})")
        
        # Test 13: Estado del pool (similar a Redis)
        logger.info("\nTest 13: Verificando estado del pool de conexiones...")
        pool = await get_client()
        logger.info(f"✓ Tamaño del pool: {pool.get_size()}")
        logger.info(f"✓ Conexiones libres: {pool.get_idle_size()}")
        
        # Test 14: Eliminar registro
        logger.info("\nTest 14: Eliminando un usuario con delete_by_id()...")
        await delete_by_id('test_users', user3_id)
        logger.info(f"✓ Usuario {user3_id} eliminado")
        
        # Verificar eliminación
        deleted_user = await get_by_id('test_users', user3_id)
        logger.info(f"✓ Usuario eliminado (debe ser None): {deleted_user}")
        
        final_count = await count_records('test_users')
        logger.info(f"✓ Total de usuarios después de eliminación: {final_count}")
        
        # Opcional: Limpiar (comentado para verificar en Supabase)
        # logger.info("\nLimpiando tabla de prueba...")
        # await execute_query("DROP TABLE IF EXISTS test_users")
        # logger.info("✓ Tabla eliminada")
        
        logger.info("\n💾 Tabla 'test_users' guardada en Supabase para verificación")
        logger.info("\n=== ✓ Todas las pruebas de helpers exitosas ===")
        
    except Exception as e:
        logger.error(f"✗ Error durante las pruebas: {e}", exc_info=True)
        raise
    finally:
        await close_client()
        logger.info("Conexión cerrada")


if __name__ == "__main__":
    asyncio.run(test_postgres_helpers())

