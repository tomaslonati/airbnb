"""
Script para crear reservas de prueba completadas para testing del sistema de reseñas.
Crea reservas con fechas pasadas para permitir la creación de reseñas.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import date, timedelta
from db.postgres import execute_query
from services.reservations import ReservationService
from utils.logging import get_logger

logger = get_logger(__name__)


async def create_completed_reservations():
    """Crea reservas completadas de prueba para testing de reseñas."""
    print("🏗️  CREANDO RESERVAS COMPLETADAS PARA TESTING")
    print("=" * 50)

    try:
        # Datos de prueba
        test_reservations = [
            {
                "propiedad_id": 20,
                "huesped_id": 14,  # ID del huésped de prueba
                "check_in": date.today() - timedelta(days=20),  # Hace 20 días
                "check_out": date.today() - timedelta(days=17),  # Hace 17 días
                "num_huespedes": 2,
                "comentarios": "Reserva de prueba #1 - Completada"
            },
            {
                "propiedad_id": 21,
                "huesped_id": 14,
                "check_in": date.today() - timedelta(days=15),  # Hace 15 días
                "check_out": date.today() - timedelta(days=12),  # Hace 12 días
                "num_huespedes": 1,
                "comentarios": "Reserva de prueba #2 - Completada"
            },
            {
                "propiedad_id": 22,
                "huesped_id": 14,
                "check_in": date.today() - timedelta(days=10),  # Hace 10 días
                "check_out": date.today() - timedelta(days=7),  # Hace 7 días
                "num_huespedes": 3,
                "comentarios": "Reserva de prueba #3 - Completada"
            }
        ]

        # Verificar qué propiedades existen
        print("🔍 Verificando propiedades disponibles...")
        propiedades_query = "SELECT id, nombre FROM propiedad LIMIT 10"
        propiedades = await execute_query(propiedades_query)

        if propiedades:
            print("   Propiedades encontradas:")
            for prop in propiedades[:5]:
                print(f"      ID {prop['id']}: {prop['nombre']}")
        else:
            print("   ❌ No se encontraron propiedades")
            return

        # Usar propiedades reales
        available_property_ids = [prop['id'] for prop in propiedades]

        print(
            f"\n🏗️  Creando {len(test_reservations)} reservas completadas...")
        created_count = 0

        for i, reserva_data in enumerate(test_reservations, 1):
            # Usar propiedad válida
            if len(available_property_ids) >= i:
                reserva_data['propiedad_id'] = available_property_ids[i-1]
            else:
                reserva_data['propiedad_id'] = available_property_ids[0]

            print(f"\n   Creando reserva {i}...")
            print(f"      Propiedad: {reserva_data['propiedad_id']}")
            print(
                f"      Fechas: {reserva_data['check_in']} → {reserva_data['check_out']}")

            try:
                # Insertar reserva directamente en PostgreSQL con fechas pasadas
                insert_query = """
                    INSERT INTO reserva (
                        propiedad_id, 
                        huesped_id, 
                        fecha_check_in, 
                        fecha_check_out, 
                        monto_final,
                        estado_reserva_id,
                        politica_cancelacion_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """

                # Calcular monto simulado
                dias = (reserva_data['check_out'] -
                        reserva_data['check_in']).days
                monto_final = 100.00 * dias  # $100 por día

                result = await execute_query(
                    insert_query,
                    reserva_data['propiedad_id'],
                    reserva_data['huesped_id'],
                    reserva_data['check_in'],
                    reserva_data['check_out'],
                    monto_final,
                    2,  # Estado "Completada" (asumiendo ID=2)
                    1   # Política de cancelación por defecto
                )

                if result:
                    reserva_id = result[0]['id']
                    print(f"      ✅ Reserva #{reserva_id} creada exitosamente")
                    created_count += 1

                    # También crear la relación en Neo4j para consistencia
                    try:
                        from services.neo4j_reservations import Neo4jReservationService
                        neo4j_service = Neo4jReservationService()

                        # Obtener anfitrión_id de la propiedad
                        prop_query = "SELECT anfitrion_id FROM propiedad WHERE id = $1"
                        prop_result = await execute_query(prop_query, reserva_data['propiedad_id'])

                        if prop_result:
                            anfitrion_id = prop_result[0]['anfitrion_id']

                            # Crear relación Neo4j
                            neo4j_result = await neo4j_service.create_host_guest_interaction(
                                host_user_id=str(anfitrion_id),
                                guest_user_id=str(reserva_data['huesped_id']),
                                reservation_id=str(reserva_id),
                                property_id=str(reserva_data['propiedad_id']),
                                reservation_date=reserva_data['check_in']
                            )

                            if neo4j_result.get('success'):
                                print(f"      🔗 Relación Neo4j creada")
                            else:
                                print(
                                    f"      ⚠️  Neo4j: {neo4j_result.get('error', 'Error desconocido')}")

                        neo4j_service.close()

                    except Exception as e:
                        print(f"      ⚠️  Error Neo4j: {e}")

                else:
                    print(f"      ❌ Error creando reserva")

            except Exception as e:
                print(f"      ❌ Error: {e}")

        print(f"\n✅ RESUMEN:")
        print(f"   Reservas creadas: {created_count}/{len(test_reservations)}")

        if created_count > 0:
            print(f"\n🎯 PARA PROBAR RESEÑAS:")
            print(f"   1. Ejecuta: python main.py")
            print(f"   2. Login como: huesped@gmail.com")
            print(f"   3. Ve a: ⭐ Gestionar mis reseñas")
            print(f"   4. Selecciona: ✍️ Crear nueva reseña")
            print(
                f"   5. ¡Deberías ver {created_count} reservas disponibles para reseñar!")

    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()


async def show_current_reservations():
    """Muestra las reservas actuales del huésped para verificar."""
    print("\n📋 VERIFICANDO RESERVAS ACTUALES DEL HUÉSPED")
    print("-" * 50)

    try:
        huesped_id = 14

        # Todas las reservas
        query_all = """
            SELECT 
                r.id,
                r.fecha_check_in,
                r.fecha_check_out,
                r.estado_reserva_id,
                p.nombre as propiedad_nombre,
                CASE 
                    WHEN r.fecha_check_out < CURRENT_DATE THEN 'Completada'
                    WHEN r.fecha_check_in > CURRENT_DATE THEN 'Futura'
                    ELSE 'En curso'
                END as estado_calculado
            FROM reserva r
            JOIN propiedad p ON r.propiedad_id = p.id
            WHERE r.huesped_id = $1
            ORDER BY r.fecha_check_out DESC
        """

        reservas = await execute_query(query_all, huesped_id)

        if reservas:
            print(f"📊 Total reservas encontradas: {len(reservas)}")
            print("-" * 80)

            completadas = 0
            for reserva in reservas:
                estado = reserva['estado_calculado']
                if estado == 'Completada':
                    completadas += 1
                    emoji = "✅"
                elif estado == 'Futura':
                    emoji = "🔮"
                else:
                    emoji = "🔄"

                print(
                    f"{emoji} Reserva #{reserva['id']}: {reserva['propiedad_nombre']}")
                print(
                    f"    📅 {reserva['fecha_check_in']} → {reserva['fecha_check_out']} ({estado})")

            print(f"\n📊 RESUMEN:")
            print(f"    ✅ Completadas (elegibles para reseña): {completadas}")
            print(f"    📝 Total reservas: {len(reservas)}")
        else:
            print("❌ No se encontraron reservas para el huésped")

        # Verificar reseñas existentes
        reseñas_query = "SELECT COUNT(*) as count FROM resenia WHERE huesped_id = $1"
        reseñas_result = await execute_query(reseñas_query, huesped_id)
        reseñas_count = reseñas_result[0]['count'] if reseñas_result else 0

        print(f"    ⭐ Reseñas ya enviadas: {reseñas_count}")

    except Exception as e:
        print(f"❌ Error verificando reservas: {e}")


async def cleanup_test_reservations():
    """Limpia las reservas de prueba creadas."""
    print("\n🧹 LIMPIAR RESERVAS DE PRUEBA")
    print("-" * 30)

    try:
        # Eliminar reservas de prueba (con comentarios que contengan "prueba")
        cleanup_query = """
            DELETE FROM reserva 
            WHERE huesped_id = $1 
            AND (
                fecha_check_in < CURRENT_DATE - INTERVAL '5 days'
                OR monto_final = 300.00  -- Monto específico de prueba
                OR monto_final = 400.00
                OR monto_final = 500.00
            )
            RETURNING id
        """

        result = await execute_query(cleanup_query, 14)

        if result:
            print(f"✅ Eliminadas {len(result)} reservas de prueba")
            for row in result:
                print(f"    - Reserva #{row['id']}")
        else:
            print("ℹ️  No se encontraron reservas de prueba para eliminar")

    except Exception as e:
        print(f"❌ Error limpiando: {e}")


async def main():
    """Función principal con menú interactivo."""
    print("🧪 HERRAMIENTAS PARA TESTING DE RESEÑAS")
    print("=" * 50)

    while True:
        print("\n📋 OPCIONES:")
        print("1. 🏗️  Crear reservas completadas de prueba")
        print("2. 📋 Ver reservas actuales del huésped")
        print("3. 🧹 Limpiar reservas de prueba")
        print("4. ❌ Salir")

        try:
            choice = input("\nSelecciona una opción (1-4): ").strip()

            if choice == "1":
                await create_completed_reservations()
            elif choice == "2":
                await show_current_reservations()
            elif choice == "3":
                await cleanup_test_reservations()
            elif choice == "4":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida")

        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

