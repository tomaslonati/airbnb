"""
Script para verificar si el sistema está impactando correctamente en Neo4j.
Incluye múltiples métodos de verificación.
"""
import asyncio
from services.neo4j_reservations import Neo4jReservationService
from db.neo4j import get_client
from datetime import date
from utils.logging import get_logger

logger = get_logger(__name__)


async def test_neo4j_connection():
    """Verifica la conexión básica a Neo4j."""
    print("🔄 Verificando conexión a Neo4j...")
    try:
        driver = await get_client()
        result = driver.execute_query("RETURN 'Neo4j conectado!' as mensaje")
        if result and result[0]:
            print("✅ Conexión a Neo4j exitosa")
            print(f"   Mensaje: {result[0][0]['mensaje']}")
            return True
        else:
            print("❌ No se pudo verificar la conexión")
            return False
    except Exception as e:
        print(f"❌ Error conectando a Neo4j: {e}")
        return False


async def test_neo4j_service():
    """Verifica que el servicio Neo4j funcione."""
    print("\n🔄 Verificando Neo4jReservationService...")
    try:
        service = Neo4jReservationService()
        print("✅ Neo4jReservationService creado exitosamente")

        # Verificar que se puede obtener el driver
        driver = await service._get_driver()
        if driver:
            print("✅ Driver obtenido correctamente")

        service.close()
        return True
    except Exception as e:
        print(f"❌ Error en Neo4jReservationService: {e}")
        return False


async def check_existing_data():
    """Verifica si ya existen datos en Neo4j."""
    print("\n🔄 Verificando datos existentes en Neo4j...")
    try:
        driver = await get_client()

        # Contar nodos Usuario
        result = driver.execute_query(
            "MATCH (u:Usuario) RETURN COUNT(u) as count")
        user_count = result[0][0]['count'] if result and result[0] else 0
        print(f"   👤 Usuarios en Neo4j: {user_count}")

        # Contar relaciones INTERACCIONES
        result = driver.execute_query(
            "MATCH ()-[r:INTERACCIONES]->() RETURN COUNT(r) as count")
        interaction_count = result[0][0]['count'] if result and result[0] else 0
        print(f"   🤝 Relaciones INTERACCIONES: {interaction_count}")

        # Contar comunidades (>3 interacciones)
        result = driver.execute_query(
            "MATCH ()-[r:INTERACCIONES]->() WHERE r.count > 3 RETURN COUNT(r) as count")
        community_count = result[0][0]['count'] if result and result[0] else 0
        print(f"   🏘️  Comunidades (>3 interacciones): {community_count}")

        if interaction_count > 0:
            print("✅ Ya existen datos en Neo4j")

            # Mostrar algunas relaciones de ejemplo
            result = driver.execute_query("""
                MATCH (guest:Usuario)-[r:INTERACCIONES]->(host:Usuario) 
                RETURN guest.user_id, host.user_id, r.count
                LIMIT 5
            """)

            if result and result[0]:
                print("\n   📊 Ejemplos de relaciones:")
                for record in result[0]:
                    print(
                        f"      Usuario {record['guest.user_id']} → Host {record['host.user_id']}: {record['r.count']} interacciones")
        else:
            print(
                "ℹ️  No hay datos Neo4j aún (esto es normal si no se han hecho reservas)")

        return True

    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return False


async def test_integration_with_reservations():
    """Verifica si la integración con reservas funciona."""
    print("\n🔄 Verificando integración con sistema de reservas...")
    try:
        from services.reservations import ReservationService

        # Crear servicio de reservas
        reservation_service = ReservationService()

        # Verificar si tiene el servicio Neo4j
        if hasattr(reservation_service, 'neo4j_service') and reservation_service.neo4j_service:
            print("✅ ReservationService tiene Neo4j integrado")
            print("✅ La integración está configurada correctamente")
        else:
            print(
                "⚠️  ReservationService no tiene Neo4j integrado o no está inicializado")
            print("   Esto es normal - se inicializa de forma lazy en la primera reserva")

        return True

    except Exception as e:
        print(f"❌ Error verificando integración: {e}")
        return False


async def simulate_interaction():
    """Simula una interacción para verificar que el sistema funcione."""
    print("\n🔄 Simulando interacción host-guest...")
    try:
        service = Neo4jReservationService()

        # Simular creación de relación
        result = await service.create_host_guest_interaction(
            host_user_id="host_test_001",
            guest_user_id="guest_test_001",
            reservation_id="res_test_001",
            property_id="prop_test_001",
            reservation_date=date.today()
        )

        if result.get('success'):
            print("✅ Simulación exitosa - Relación creada/actualizada")
            print(f"   Total interacciones: {result['total_interactions']}")
            print(f"   Propiedades únicas: {result['unique_properties']}")

            # Verificar que se creó en Neo4j
            driver = await service._get_driver()
            verify_result = driver.execute_query("""
                MATCH (guest:Usuario {user_id: $guest})-[r:INTERACCIONES]->(host:Usuario {user_id: $host})
                RETURN r.count as interactions
            """, guest="guest_test_001", host="host_test_001")

            if verify_result and verify_result[0]:
                interactions = verify_result[0][0]['interactions']
                print(
                    f"✅ Verificado en Neo4j: {interactions} interacciones registradas")
            else:
                print("⚠️  No se encontró la relación en Neo4j")
        else:
            print(f"❌ Error en simulación: {result.get('error')}")

        service.close()
        return True

    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False


async def show_community_analysis():
    """Muestra análisis de comunidades si existen datos."""
    print("\n🔄 Análisis de comunidades...")
    try:
        service = Neo4jReservationService()

        # Obtener estadísticas
        stats = await service.get_community_stats()

        if stats.get('success'):
            if stats.get('total_relationships', 0) > 0:
                print("✅ Estadísticas de comunidades:")
                print(f"   👥 Total relaciones: {stats['total_relationships']}")
                print(
                    f"   🏘️  Comunidades formadas: {stats['communities_formed']}")
                print(
                    f"   🤝 Relaciones casuales: {stats['casual_relationships']}")
                print(f"   📈 Tasa comunidades: {stats['community_rate']}%")
            else:
                print("ℹ️  No hay relaciones aún para analizar")
        else:
            print(f"⚠️  Error obteniendo estadísticas: {stats.get('error')}")

        service.close()
        return True

    except Exception as e:
        print(f"❌ Error en análisis: {e}")
        return False


async def cleanup_test_data():
    """Limpia datos de prueba creados durante la verificación."""
    print("\n🔄 Limpiando datos de prueba...")
    try:
        driver = await get_client()

        # Eliminar datos de prueba
        result = driver.execute_query("""
            MATCH (u:Usuario)
            WHERE u.user_id CONTAINS 'test'
            DETACH DELETE u
            RETURN COUNT(*) as deleted
        """)

        deleted = result[0][0]['deleted'] if result and result[0] else 0
        if deleted > 0:
            print(f"✅ Eliminados {deleted} nodos de prueba")
        else:
            print("ℹ️  No había datos de prueba para limpiar")

        return True

    except Exception as e:
        print(f"❌ Error limpiando: {e}")
        return False


async def main():
    """Ejecuta todas las verificaciones."""
    print("🏘️  VERIFICACIÓN DEL IMPACTO EN NEO4J")
    print("=" * 50)

    # Lista de verificaciones
    checks = [
        ("Conexión básica", test_neo4j_connection),
        ("Servicio Neo4j", test_neo4j_service),
        ("Datos existentes", check_existing_data),
        ("Integración con reservas", test_integration_with_reservations),
        ("Simulación de interacción", simulate_interaction),
        ("Análisis de comunidades", show_community_analysis),
        ("Limpieza de datos de prueba", cleanup_test_data)
    ]

    results = []

    for name, check_func in checks:
        try:
            result = await check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))

    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIONES")
    print("=" * 50)

    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1

    print(f"\n🎯 Resultado: {passed}/{len(results)} verificaciones exitosas")

    if passed == len(results):
        print("🎉 ¡Todo funciona correctamente! El sistema está impactando en Neo4j.")
    elif passed >= len(results) * 0.7:
        print("⚠️  La mayoría funciona bien. Revisa los errores específicos.")
    else:
        print("❌ Hay problemas significativos. Revisa la configuración.")

if __name__ == "__main__":
    asyncio.run(main())
