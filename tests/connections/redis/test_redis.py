"""
Script de prueba para verificar la conexión a Redis.
"""
import asyncio
from db.redisdb import get_client, set_key, get_key, close_client
from utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def test_redis_connection():
    """Prueba la conexión a Redis."""
    try:
        logger.info("=== Iniciando prueba de Redis ===")
        
        # Test 1: Ping
        logger.info("Test 1: Verificando conexión con PING...")
        client = await get_client()
        response = await client.ping()
        logger.info(f"✓ PING exitoso: {response}")
        
        # Test 2: SET y GET (como en el ejemplo oficial)
        logger.info("\nTest 2: SET y GET básico...")
        success = await set_key('foo', 'bar')
        logger.info(f"✓ SET 'foo' = 'bar': {success}")
        
        result = await get_key('foo')
        logger.info(f"✓ GET 'foo' = '{result}'")
        
        if result == 'bar':
            logger.info("✓ ¡Valor correcto!")
        else:
            logger.error(f"✗ Error: se esperaba 'bar', se obtuvo '{result}'")
        
        # Test 3: SET con expiración
        logger.info("\nTest 3: SET con expiración (5 segundos)...")
        await set_key('temp_key', 'temporal', expire=5)
        value = await get_key('temp_key')
        logger.info(f"✓ Valor temporal guardado: '{value}'")
        ttl = await client.ttl('temp_key')
        logger.info(f"✓ TTL restante: {ttl} segundos")
        
        # Test 4: Contador
        logger.info("\nTest 4: Contador (INCR)...")
        await client.set('counter', 0)
        for i in range(1, 4):
            new_value = await client.incr('counter')
            logger.info(f"✓ Contador incrementado: {new_value}")
        
        # Test 5: Sets (conjuntos)
        logger.info("\nTest 5: Operaciones con Sets...")
        await client.sadd('colors', 'red', 'blue', 'green')
        logger.info("✓ Agregados elementos al set 'colors'")
        
        # Obtener todos los elementos
        members = await client.smembers('colors')
        logger.info(f"✓ Elementos en 'colors': {members}")
        
        # Verificar si existe un elemento
        exists_red = await client.sismember('colors', 'red')
        exists_yellow = await client.sismember('colors', 'yellow')
        logger.info(f"✓ ¿'red' está en el set?: {exists_red}")
        logger.info(f"✓ ¿'yellow' está en el set?: {exists_yellow}")
        
        # Contar elementos
        count = await client.scard('colors')
        logger.info(f"✓ Cantidad de elementos en el set: {count}")
        
        # Agregar más elementos
        await client.sadd('colors', 'yellow', 'red')  # red ya existe, no se duplica
        members_after = await client.smembers('colors')
        logger.info(f"✓ Después de agregar 'yellow' y 'red': {members_after}")
        
        # Remover un elemento
        await client.srem('colors', 'blue')
        members_final = await client.smembers('colors')
        logger.info(f"✓ Después de remover 'blue': {members_final}")
        
        # Test 6: Lista de claves
        logger.info("\nTest 6: Listar claves creadas...")
        keys = await client.keys('*')
        logger.info(f"✓ Claves en Redis: {keys}")
        
        # Limpiar (comentado para verificar en Redis Cloud)
        # logger.info("\nLimpiando claves de prueba...")
        # await client.delete('foo', 'temp_key', 'counter', 'colors')
        # logger.info("✓ Claves eliminadas")
        logger.info("\n💾 Datos guardados en Redis Cloud para verificación")
        
        logger.info("\n=== ✓ Todas las pruebas exitosas ===")
        
    except Exception as e:
        logger.error(f"✗ Error durante las pruebas: {e}", exc_info=True)
        raise
    finally:
        await close_client()
        logger.info("Conexión cerrada")


if __name__ == "__main__":
    asyncio.run(test_redis_connection())

