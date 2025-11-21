"""
Script de prueba para verificar que Neo4j está escribiendo datos correctamente.
"""
import asyncio
from db import neo4j
from utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


async def test_neo4j_connection():
    """Prueba de conexión básica a Neo4j"""
    try:
        logger.info("🔍 Probando conexión a Neo4j...")

        # Obtener driver
        driver = await neo4j.get_client()
        if not driver:
            logger.error("❌ No se pudo obtener el driver de Neo4j")
            return False

        logger.info("✅ Driver obtenido correctamente")

        # Probar query simple
        logger.info("🔍 Ejecutando query de prueba...")
        result = neo4j.execute_query("RETURN 1 as test")

        if result:
            logger.info(f"✅ Query ejecutada: {result}")
            return True
        else:
            logger.error("❌ Query no retornó resultados")
            return False

    except Exception as e:
        logger.error(f"❌ Error en test de conexión: {e}")
        return False


async def test_neo4j_write():
    """Prueba de escritura en Neo4j"""
    try:
        logger.info("🔍 Probando escritura en Neo4j...")

        # Obtener driver
        driver = await neo4j.get_client()
        if not driver:
            logger.error("❌ No se pudo obtener el driver de Neo4j")
            return False

        # Crear nodo de prueba
        logger.info("🔍 Creando nodo de prueba...")
        query = """
        MERGE (test:TestNode {id: 'test-123'})
        ON CREATE SET test.created_at = datetime()
        ON MATCH SET test.updated_at = datetime()
        RETURN test.id as id, test.created_at as created_at
        """

        result = neo4j.execute_query(query)

        if result and result.get("records"):
            logger.info(f"✅ Nodo creado: {result['records'][0]}")

            # Verificar que el nodo existe
            logger.info("🔍 Verificando que el nodo existe...")
            verify_query = """
            MATCH (test:TestNode {id: 'test-123'})
            RETURN test.id as id, test.created_at as created_at
            """

            verify_result = neo4j.execute_query(verify_query)

            if verify_result and verify_result.get("records"):
                logger.info(f"✅✅✅ ¡NODO VERIFICADO! Existe en la base de datos")
                logger.info(f"   Datos: {verify_result['records'][0]}")

                # Limpiar nodo de prueba
                logger.info("🧹 Limpiando nodo de prueba...")
                delete_query = "MATCH (test:TestNode {id: 'test-123'}) DELETE test"
                neo4j.execute_query(delete_query)
                logger.info("✅ Nodo de prueba eliminado")

                return True
            else:
                logger.error("❌ El nodo no se encontró después de crearlo")
                return False
        else:
            logger.error("❌ No se pudo crear el nodo")
            return False

    except Exception as e:
        logger.error(f"❌ Error en test de escritura: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_user_city_relationship():
    """Prueba la creación de relación Usuario-[:BOOKED_IN]->City (CU 9)"""
    try:
        logger.info("🔍 Probando relación Usuario-City (CU 9)...")

        # Obtener driver
        driver = await neo4j.get_client()
        if not driver:
            logger.error("❌ No se pudo obtener el driver de Neo4j")
            return False

        # Crear relación de prueba con el formato CORRECTO
        logger.info("🔍 Creando relación Usuario-City de prueba...")
        query = """
        MERGE (u:Usuario {user_id: 999})
        MERGE (c:City {name: 'Test City'})
        MERGE (u)-[r:BOOKED_IN]->(c)
        ON CREATE SET r.count = 1
        ON MATCH SET r.count = r.count + 1
        RETURN r.count as count
        """

        result = neo4j.execute_query(query, parameters={})

        if result and result.get("records"):
            count = result["records"][0]["count"]
            logger.info(f"✅ Relación creada con count: {count}")

            # Verificar relación
            logger.info("🔍 Verificando relación...")
            verify_query = """
            MATCH (u:Usuario {user_id: 999})-[r:BOOKED_IN]->(c:City {name: 'Test City'})
            RETURN r.count as count, u.user_id as user_id, c.name as city_name
            """

            verify_result = neo4j.execute_query(verify_query, parameters={})

            if verify_result and verify_result.get("records"):
                record = verify_result['records'][0]
                logger.info(f"✅✅✅ ¡RELACIÓN VERIFICADA EN NEO4J!")
                logger.info(f"   Usuario: {record['user_id']}")
                logger.info(f"   Ciudad: {record['city_name']}")
                logger.info(f"   Count: {record['count']}")

                # Limpiar datos de prueba
                logger.info("🧹 Limpiando datos de prueba...")
                delete_all = """
                MATCH (u:Usuario {user_id: 999})-[r:BOOKED_IN]->(c:City {name: 'Test City'})
                DELETE r, u, c
                """
                neo4j.execute_query(delete_all, parameters={})

                logger.info("✅ Datos de prueba eliminados")
                return True
            else:
                logger.error("❌ La relación no se encontró después de crearla")
                logger.error("⚠️  Esto significa que la query NO está escribiendo en Neo4j")
                return False
        else:
            logger.error("❌ No se pudo crear la relación")
            return False

    except Exception as e:
        logger.error(f"❌ Error en test de relación: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_host_guest_interaction():
    """Prueba la creación de interacción Host-Guest (CU 10)"""
    try:
        logger.info("🔍 Probando interacción Host-Guest (CU 10)...")

        # Obtener driver
        driver = await neo4j.get_client()
        if not driver:
            logger.error("❌ No se pudo obtener el driver de Neo4j")
            return False

        # Crear interacción de prueba
        logger.info("🔍 Creando interacción Host-Guest de prueba...")
        query = """
        MERGE (host:Usuario {user_id: 888})
        MERGE (guest:Usuario {user_id: 777})
        MERGE (guest)-[rel:INTERACCIONES]->(host)
        ON CREATE SET
            rel.count = 1,
            rel.reservas = [123],
            rel.propiedades = [456],
            rel.created_at = datetime()
        ON MATCH SET
            rel.count = rel.count + 1,
            rel.reservas = rel.reservas + 124,
            rel.propiedades = rel.propiedades + 457
        RETURN
            rel.count as total_interacciones,
            size(rel.propiedades) as propiedades_distintas
        """

        result = neo4j.execute_query(query, parameters={})

        if result and result.get("records"):
            record = result["records"][0]
            logger.info(f"✅ Interacción creada:")
            logger.info(f"   Total interacciones: {record['total_interacciones']}")
            logger.info(f"   Propiedades distintas: {record['propiedades_distintas']}")

            # Verificar interacción
            logger.info("🔍 Verificando interacción...")
            verify_query = """
            MATCH (guest:Usuario {user_id: 777})-[rel:INTERACCIONES]->(host:Usuario {user_id: 888})
            RETURN
                guest.user_id as guest_id,
                host.user_id as host_id,
                rel.count as count,
                rel.reservas as reservas
            """

            verify_result = neo4j.execute_query(verify_query, parameters={})

            if verify_result and verify_result.get("records"):
                vr = verify_result['records'][0]
                logger.info(f"✅✅✅ ¡INTERACCIÓN VERIFICADA EN NEO4J!")
                logger.info(f"   Guest: {vr['guest_id']} -> Host: {vr['host_id']}")
                logger.info(f"   Count: {vr['count']}")
                logger.info(f"   Reservas: {vr['reservas']}")

                # Limpiar datos de prueba
                logger.info("🧹 Limpiando datos de prueba...")
                delete_all = """
                MATCH (guest:Usuario {user_id: 777})-[rel:INTERACCIONES]->(host:Usuario {user_id: 888})
                DELETE rel, guest, host
                """
                neo4j.execute_query(delete_all, parameters={})

                logger.info("✅ Datos de prueba eliminados")
                return True
            else:
                logger.error("❌ La interacción no se encontró después de crearla")
                return False
        else:
            logger.error("❌ No se pudo crear la interacción")
            return False

    except Exception as e:
        logger.error(f"❌ Error en test de interacción: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    logger.info("=" * 70)
    logger.info("TEST DE ESCRITURA A NEO4J - CASOS DE USO 9 Y 10")
    logger.info("=" * 70)

    # Test 1: Conexión
    logger.info("\n📍 TEST 1: CONEXIÓN A NEO4J")
    logger.info("-" * 70)
    connection_ok = await test_neo4j_connection()

    if not connection_ok:
        logger.error("❌ FALLO: No se pudo conectar a Neo4j")
        logger.error("Verifica las credenciales en .env")
        return

    # Test 2: Escritura simple
    logger.info("\n📍 TEST 2: ESCRITURA SIMPLE (NODO DE PRUEBA)")
    logger.info("-" * 70)
    write_ok = await test_neo4j_write()

    if not write_ok:
        logger.error("❌ FALLO: No se pudo escribir en Neo4j")
        logger.error("El driver está conectado pero las queries no persisten")
        return

    # Test 3: Relación Usuario-City (CU 9)
    logger.info("\n📍 TEST 3: CU 9 - USUARIOS RECURRENTES (Usuario-City)")
    logger.info("-" * 70)
    relation_ok = await test_user_city_relationship()

    if not relation_ok:
        logger.error("❌ FALLO: No se pudo crear relación Usuario-City")
        logger.error("CU 9 no funcionará correctamente")
        return

    # Test 4: Interacción Host-Guest (CU 10)
    logger.info("\n📍 TEST 4: CU 10 - COMUNIDADES HOST-HUÉSPED")
    logger.info("-" * 70)
    interaction_ok = await test_host_guest_interaction()

    if not interaction_ok:
        logger.error("❌ FALLO: No se pudo crear interacción Host-Guest")
        logger.error("CU 10 no funcionará correctamente")
        return

    # Resumen
    logger.info("\n" + "=" * 70)
    logger.info("✅✅✅ TODOS LOS TESTS PASARON")
    logger.info("=" * 70)
    logger.info("🎉 Neo4j está funcionando correctamente!")
    logger.info("")
    logger.info("✅ Escritura simple: OK")
    logger.info("✅ CU 9 (Usuarios recurrentes): OK")
    logger.info("✅ CU 10 (Comunidades): OK")
    logger.info("")
    logger.info("💡 Los datos SE ESTÁN GUARDANDO en Neo4j")
    logger.info("💡 Puedes verificarlo en Neo4j Browser con:")
    logger.info("   MATCH (n) RETURN n LIMIT 25")

    await neo4j.close_client()


if __name__ == "__main__":
    asyncio.run(main())
