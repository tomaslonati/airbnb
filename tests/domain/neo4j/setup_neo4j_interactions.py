#!/usr/bin/env python3
"""
Script para crear relaciones INTERACCIONES de prueba en Neo4j
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.neo4j_reservations import Neo4jReservationService
import structlog
from datetime import date, timedelta

logger = structlog.get_logger(__name__)


async def create_test_interactions():
    """Crea relaciones INTERACCIONES de prueba en Neo4j."""

    print("🔗 CREANDO RELACIONES INTERACCIONES DE PRUEBA")
    print("=" * 60)

    neo4j_service = None
    try:
        neo4j_service = Neo4jReservationService()

        # 1. Verificar conexión
        print("🔌 Verificando conexión a Neo4j...")

        # 2. Crear algunos nodos de prueba si no existen
        print("\n👥 Creando nodos de prueba...")

        create_nodes_query = """
        // Crear huéspedes si no existen
        MERGE (h1:Huesped {user_id: 14})
        MERGE (h2:Huesped {user_id: 15})  
        MERGE (h3:Huesped {user_id: 16})
        
        // Crear anfitriones si no existen  
        MERGE (a1:Anfitrion {user_id: 1})
        MERGE (a2:Anfitrion {user_id: 2})
        MERGE (a3:Anfitrion {user_id: 3})
        
        RETURN 'Nodos creados' as resultado
        """

        result_nodes = await neo4j_service.execute_query(create_nodes_query)
        if result_nodes['success']:
            print("   ✅ Nodos creados correctamente")
        else:
            print(f"   ❌ Error creando nodos: {result_nodes['error']}")
            return

        # 3. Crear relaciones INTERACCIONES de prueba
        print("\n🔗 Creando relaciones INTERACCIONES...")

        # Fechas para las interacciones
        today = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        interactions_data = [
            # Comunidad fuerte: Huésped 14 ↔ Anfitrión 1 (5 interacciones)
            {"guest_id": 14, "host_id": 1, "count": 5, "date": today.isoformat()},

            # Comunidad media: Huésped 15 ↔ Anfitrión 1 (3 interacciones)
            {"guest_id": 15, "host_id": 1, "count": 3, "date": week_ago.isoformat()},

            # Comunidad media: Huésped 14 ↔ Anfitrión 2 (4 interacciones)
            {"guest_id": 14, "host_id": 2, "count": 4, "date": week_ago.isoformat()},

            # Comunidad límite: Huésped 16 ↔ Anfitrión 3 (3 interacciones)
            {"guest_id": 16, "host_id": 3, "count": 3,
                "date": month_ago.isoformat()},

            # Comunidad pequeña: Huésped 15 ↔ Anfitrión 2 (2 interacciones) - NO debe aparecer
            {"guest_id": 15, "host_id": 2, "count": 2,
                "date": month_ago.isoformat()},

            # Comunidad grande: Huésped 16 ↔ Anfitrión 1 (7 interacciones)
            {"guest_id": 16, "host_id": 1, "count": 7, "date": today.isoformat()},
        ]

        for interaction in interactions_data:
            query = f"""
            MATCH (h:Huesped {{user_id: {interaction['guest_id']}}})
            MATCH (a:Anfitrion {{user_id: {interaction['host_id']}}})
            MERGE (h)-[r:INTERACCIONES]->(a)
            SET r.count = {interaction['count']}, 
                r.last_interaction = '{interaction['date']}',
                r.total_properties = 1,
                r.avg_rating = {4 + (interaction['count'] % 2)}.0
            RETURN h.user_id as guest_id, a.user_id as host_id, r.count as interactions
            """

            result = await neo4j_service.execute_query(query)
            if result['success'] and result['data']:
                data = result['data'][0]
                print(
                    f"   ✅ Huésped {data['guest_id']} ↔ Anfitrión {data['host_id']}: {data['interactions']} interacciones")
            else:
                print(
                    f"   ❌ Error creando relación: {result.get('error', 'Error desconocido')}")

        # 4. Verificar las relaciones creadas
        print("\n📊 Verificando relaciones creadas...")

        verify_query = """
        MATCH (h:Huesped)-[r:INTERACCIONES]->(a:Anfitrion)
        RETURN h.user_id as guest_id, a.user_id as host_id, 
               r.count as interactions, r.last_interaction as last_date
        ORDER BY r.count DESC
        """

        result_verify = await neo4j_service.execute_query(verify_query)
        if result_verify['success'] and result_verify['data']:
            print(f"   📈 Total relaciones: {len(result_verify['data'])}")
            print(
                f"   {'Huésped':<10} {'Anfitrión':<10} {'Interacciones':<13} {'Última':<12}")
            print("   " + "-" * 50)

            for record in result_verify['data']:
                guest = record['guest_id']
                host = record['host_id']
                count = record['interactions']
                last = record['last_date']
                status = "✅ Comunidad" if count >= 3 else "❌ < 3"
                print(
                    f"   {guest:<10} {host:<10} {count:<13} {last:<12} {status}")

        # 5. Probar la consulta de comunidades
        print("\n🏘️ Probando consulta de comunidades (>= 3 interacciones)...")
        result_communities = await neo4j_service.get_all_communities(min_interactions=3)

        if result_communities['success']:
            total = result_communities['total_communities']
            communities = result_communities['communities']
            print(f"   ✅ {total} comunidades encontradas:")

            for i, comm in enumerate(communities[:5], 1):
                guest_id = comm.get('guest_id', 'N/A')
                host_id = comm.get('host_id', 'N/A')
                interactions = comm.get('total_interactions', 0)
                print(
                    f"      {i}. Huésped {guest_id} ↔ Anfitrión {host_id}: {interactions} interacciones")
        else:
            print(
                f"   ❌ Error consultando comunidades: {result_communities.get('error', 'Error desconocido')}")

        print(f"\n✅ Relaciones de prueba creadas exitosamente!")
        print(f"💡 Ahora puedes probar el Caso de Uso 10 en el menú principal")

    except Exception as e:
        print(f"❌ Error creando relaciones: {str(e)}")
        logger.error("Error creando relaciones de prueba", error=str(e))

    finally:
        if neo4j_service:
            neo4j_service.close()


async def cleanup_test_interactions():
    """Limpia las relaciones INTERACCIONES de prueba."""
    print("\n🧹 LIMPIANDO RELACIONES DE PRUEBA...")

    neo4j_service = None
    try:
        neo4j_service = Neo4jReservationService()

        # Eliminar todas las relaciones INTERACCIONES
        cleanup_query = """
        MATCH ()-[r:INTERACCIONES]->()
        DELETE r
        RETURN count(r) as deleted
        """

        result = await neo4j_service.execute_query(cleanup_query)
        if result['success']:
            print("   ✅ Relaciones INTERACCIONES eliminadas")
        else:
            print(f"   ❌ Error limpiando: {result['error']}")

    except Exception as e:
        print(f"❌ Error en limpieza: {str(e)}")

    finally:
        if neo4j_service:
            neo4j_service.close()


async def main():
    """Función principal con menú interactivo."""
    print("🔗 GESTIÓN DE RELACIONES NEO4J - CASO DE USO 10")
    print("=" * 60)

    while True:
        print(f"\n🛠️  OPCIONES:")
        print("1. 🔗 Crear relaciones INTERACCIONES de prueba")
        print("2. 🧹 Limpiar relaciones de prueba")
        print("3. ❌ Salir")

        try:
            choice = input("Selecciona una opción (1-3): ").strip()

            if choice == "1":
                await create_test_interactions()
            elif choice == "2":
                await cleanup_test_interactions()
            elif choice == "3":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Selecciona 1, 2 o 3.")

        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

