"""
Script rápido para consultar Neo4j directamente después de hacer reservas.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from db.neo4j import get_client


async def quick_neo4j_check():
    try:
        driver = await get_client()

        print("🔍 CONSULTANDO NEO4J DIRECTAMENTE...")
        print("=" * 40)

        # Verificar usuarios
        result = driver.execute_query(
            "MATCH (u:Usuario) RETURN COUNT(u) as count")
        user_count = result[0][0]['count'] if result and result[0] else 0
        print(f"👤 Total usuarios: {user_count}")

        # Verificar relaciones
        result = driver.execute_query(
            "MATCH ()-[r:INTERACCIONES]->() RETURN COUNT(r) as count")
        rel_count = result[0][0]['count'] if result and result[0] else 0
        print(f"🤝 Relaciones INTERACCIONES: {rel_count}")

        if rel_count > 0:
            # Mostrar detalles de relaciones
            result = driver.execute_query("""
                MATCH (guest:Usuario)-[r:INTERACCIONES]->(host:Usuario)
                RETURN guest.user_id, host.user_id, r.count, r.reservas
                LIMIT 5
            """)

            print("\n📊 Detalles de relaciones:")
            for record in result[0] if result and result[0] else []:
                guest_id = record['guest.user_id']
                host_id = record['host.user_id']
                count = record['r.count']
                reservas = record['r.reservas']
                print(
                    f"   👤 {guest_id} → 🏠 {host_id}: {count} interacciones, reservas: {reservas}")

        # Verificar comunidades
        result = driver.execute_query(
            "MATCH ()-[r:INTERACCIONES]->() WHERE r.count > 3 RETURN COUNT(r) as count")
        comm_count = result[0][0]['count'] if result and result[0] else 0
        print(f"🏘️ Comunidades (>3 interacciones): {comm_count}")

        print("\n" + "=" * 40)
        if rel_count == 0:
            print("💡 PARA VER IMPACTO:")
            print("   1. Ejecuta: python main.py")
            print("   2. Haz al menos una reserva")
            print("   3. Ejecuta este script nuevamente")
        else:
            print("✅ ¡El sistema SÍ está impactando en Neo4j!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_neo4j_check())

