"""
Script de diagnóstico detallado para verificar la integración Neo4j.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.reservations import ReservationService
from datetime import date
import logging

# Configurar logging para ver todo
logging.basicConfig(level=logging.DEBUG)


async def detailed_neo4j_test():
    print("🔍 DIAGNÓSTICO DETALLADO DE INTEGRACIÓN NEO4J")
    print("=" * 60)

    try:
        # 1. Crear servicio de reservas
        print("1️⃣ Creando ReservationService...")
        service = ReservationService()
        print(f"   ✅ Servicio creado: {service}")

        # 2. Verificar lazy loading de Neo4j
        print("\n2️⃣ Verificando lazy loading Neo4j...")
        neo4j_service = service.neo4j_service
        print(f"   ✅ Neo4j service: {neo4j_service}")
        print(f"   ✅ Tipo: {type(neo4j_service)}")

        if neo4j_service is None:
            print("   ❌ Neo4j service es None - hay un problema de importación")
            return

        # 3. Verificar que el método existe
        print("\n3️⃣ Verificando método create_host_guest_interaction...")
        method = getattr(neo4j_service, 'create_host_guest_interaction', None)
        if method:
            print("   ✅ Método existe")
        else:
            print("   ❌ Método no existe")
            return

        # 4. Probar conexión Neo4j directa
        print("\n4️⃣ Probando conexión Neo4j directa...")
        try:
            driver = await neo4j_service._get_driver()
            print(f"   ✅ Driver obtenido: {driver}")
        except Exception as e:
            print(f"   ❌ Error obteniendo driver: {e}")
            return

        # 5. Simular creación de relación
        print("\n5️⃣ Simulando creación de relación...")
        try:
            result = await neo4j_service.create_host_guest_interaction(
                host_user_id="5",  # Un ID que sabemos que existe
                guest_user_id="14",  # El usuario huésped que usaste
                reservation_id="test_reservation_001",
                property_id="20",
                reservation_date=date.today()
            )
            print(f"   ✅ Resultado: {result}")

            if result.get('success'):
                print(
                    f"   🎉 ¡Éxito! Total interacciones: {result['total_interactions']}")
            else:
                print(f"   ❌ Error: {result.get('error')}")

        except Exception as e:
            print(f"   ❌ Excepción creando relación: {e}")
            import traceback
            traceback.print_exc()

        # 6. Verificar si se creó en Neo4j
        print("\n6️⃣ Verificando en Neo4j...")
        try:
            from db.neo4j import get_client
            driver = await get_client()
            result = driver.execute_query("""
                MATCH ()-[r:INTERACCIONES]->() 
                RETURN COUNT(r) as count
            """)

            count = result[0][0]['count'] if result and result[0] else 0
            print(f"   📊 Total relaciones INTERACCIONES en Neo4j: {count}")

            if count > 0:
                # Mostrar detalles
                result = driver.execute_query("""
                    MATCH (guest:Usuario)-[r:INTERACCIONES]->(host:Usuario)
                    RETURN guest.user_id, host.user_id, r.count, r.reservas
                    LIMIT 5
                """)

                print("   📋 Detalles de relaciones:")
                for record in result[0] if result and result[0] else []:
                    print(
                        f"      👤 {record['guest.user_id']} → 🏠 {record['host.user_id']}: {record['r.count']} interacciones")

        except Exception as e:
            print(f"   ❌ Error verificando Neo4j: {e}")

        # 7. Limpiar datos de prueba
        print("\n7️⃣ Limpiando datos de prueba...")
        try:
            driver = await get_client()
            result = driver.execute_query("""
                MATCH ()-[r:INTERACCIONES]->()
                WHERE 'test_reservation_001' IN r.reservas
                DELETE r
                RETURN COUNT(*) as deleted
            """)
            deleted = result[0][0]['deleted'] if result and result[0] else 0
            if deleted > 0:
                print(f"   🧹 Eliminadas {deleted} relaciones de prueba")
            else:
                print("   ℹ️ No había datos de prueba para eliminar")
        except Exception as e:
            print(f"   ⚠️ Error limpiando: {e}")

        print("\n" + "=" * 60)
        print("✅ Diagnóstico completado")

    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(detailed_neo4j_test())

