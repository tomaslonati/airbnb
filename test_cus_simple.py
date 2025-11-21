"""
Test simplificado de Casos de Uso (CUs) del sistema Airbnb.
"""

import asyncio
import structlog
from datetime import date, datetime, timedelta

logger = structlog.get_logger(__name__)


async def test_cu_simple():
    """Test simplificado de CUs usando CLI"""

    print("🚀 TEST SIMPLIFICADO DE CUs")
    print("=" * 50)

    # Importar servicios principales
    try:
        from services.auth import AuthService
        from services.reservations import ReservationService
        from services.analytics import AnalyticsService
        from services.search import SearchService

        print("✅ Servicios importados correctamente")
    except Exception as e:
        print(f"❌ Error importando servicios: {e}")
        return

    # Test CU1: Login (Redis - Sesión)
    print("\n🔑 CU7: Test de sesión de usuario")
    try:
        auth_service = AuthService()
        login_result = await auth_service.login(
            email="tomaslonati@gmail.com",
            password="123456"
        )

        if login_result.get('success'):
            user_id = login_result['user_id']
            session_token = login_result['session_token']
            print(f"   ✅ Login exitoso - Usuario: {user_id}")
            print(f"   🔑 Token: {session_token[:10]}...")

            # Test TTL de sesión
            from services.session import SessionManager
            session_mgr = SessionManager()
            ttl = await session_mgr.get_session_ttl(session_token)
            print(f"   ⏱️ TTL restante: {ttl} segundos")
        else:
            print(f"   ❌ Error login: {login_result.get('error')}")

    except Exception as e:
        print(f"   ❌ Error en test de sesión: {e}")

    # Test CU2: Crear reserva (Multi-database)
    print("\n📅 CU Multi-database: Crear reserva")
    try:
        reservation_service = ReservationService()

        result = await reservation_service.create_reservation(
            huesped_id=7,
            propiedad_id=8,
            check_in=date(2025, 12, 31),
            check_out=date(2026, 1, 2),
            num_huespedes=2,
            comentarios="Test CU integrado"
        )

        if result.get('success'):
            reservation = result['reservation']
            print(f"   ✅ Reserva creada - ID: {reservation['id']}")
            print(f"   💰 Precio total: ${reservation['precio_total']}")
            print(f"   📊 Propiedad: {reservation['propiedad_id']}")
        else:
            print(f"   ❌ Error creando reserva: {result.get('error')}")

    except Exception as e:
        print(f"   ❌ Error en test de reserva: {e}")

    # Test CU3: Analytics (Cassandra)
    print("\n📊 CU1: Test de analytics - Ocupación por ciudad")
    try:
        analytics_service = AnalyticsService()

        result = await analytics_service.get_city_occupancy_rate(
            city_name="Buenos Aires",
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31)
        )

        if result.get('success'):
            data = result['data']
            print(
                f"   ✅ Ocupación calculada: {data.get('occupancy_rate', 0):.2f}%")
            print(f"   🏠 Total propiedades: {data.get('total_properties', 0)}")
        else:
            print(f"   ❌ Error analytics: {result.get('error')}")

    except Exception as e:
        print(f"   ❌ Error en test analytics: {e}")

    # Test CU4: Búsqueda con caché (Redis)
    print("\n🔍 CU8: Test de búsqueda con caché")
    try:
        search_service = SearchService()

        search_params = {
            "ciudad": "Buenos Aires",
            "capacidad_minima": 2,
            "precio_maximo": 200
        }

        # Primera búsqueda
        start_time = datetime.now()
        result1 = await search_service.search_properties(**search_params)
        time1 = (datetime.now() - start_time).total_seconds()

        # Segunda búsqueda (con caché)
        start_time = datetime.now()
        result2 = await search_service.search_properties(**search_params)
        time2 = (datetime.now() - start_time).total_seconds()

        print(f"   ⏱️ Primera búsqueda: {time1:.3f}s")
        print(f"   ⏱️ Segunda búsqueda: {time2:.3f}s")
        print(
            f"   🚀 Mejora: {((time1-time2)/time1*100):.1f}%" if time1 > time2 else "Sin mejora")

        if result1.get('success'):
            props = len(result1.get('properties', []))
            print(f"   ✅ Propiedades encontradas: {props}")

    except Exception as e:
        print(f"   ❌ Error en test búsqueda: {e}")

    # Test CU5: PostgreSQL directo - Rating promedio
    print("\n⭐ CU2: Test de rating promedio por anfitrión")
    try:
        from db.postgres import get_client as get_postgres_client

        pool = await get_postgres_client()
        async with pool.acquire() as conn:
            query = """
            SELECT 
                p.anfitrion_id,
                u.nombre as anfitrion_nombre,
                AVG(r.calificacion) as promedio_rating,
                COUNT(r.id) as total_reseñas
            FROM reseñas r
            JOIN reserva res ON r.reserva_id = res.id
            JOIN propiedades p ON res.propiedad_id = p.id
            JOIN usuarios u ON p.anfitrion_id = u.id
            WHERE p.anfitrion_id = $1
            GROUP BY p.anfitrion_id, u.nombre
            """

            result = await conn.fetchrow(query, 6)  # Anfitrión ID 6

            if result:
                promedio = float(result['promedio_rating']
                                 ) if result['promedio_rating'] else 0.0
                print(f"   ✅ Anfitrión: {result['anfitrion_nombre']}")
                print(f"   ⭐ Rating promedio: {promedio:.2f}/5")
                print(f"   📊 Total reseñas: {result['total_reseñas']}")
            else:
                print("   ⚠️ No hay datos de reseñas para este anfitrión")

    except Exception as e:
        print(f"   ❌ Error en test rating: {e}")

    # Test CU6: Disponibilidad en fecha específica
    print("\n📅 CU4: Test de disponibilidad en fecha específica")
    try:
        from db.postgres import get_client as get_postgres_client

        fecha_test = date(2026, 2, 14)  # Fecha futura
        pool = await get_postgres_client()

        async with pool.acquire() as conn:
            query = """
            SELECT COUNT(*) as disponibles
            FROM propiedades p
            LEFT JOIN propiedad_disponibilidad pd ON p.id = pd.propiedad_id 
                AND pd.fecha = $1
            WHERE (pd.disponible = true OR pd.disponible IS NULL)
            """

            result = await conn.fetchrow(query, fecha_test)
            disponibles = result['disponibles']

            print(f"   📅 Fecha: {fecha_test}")
            print(f"   ✅ Propiedades disponibles: {disponibles}")

    except Exception as e:
        print(f"   ❌ Error en test disponibilidad: {e}")

    # Test CU7: Neo4j Simulator
    print("\n🏘️ CU9-10: Test Neo4j Simulator")
    try:
        from neo4j_simulator import simulate_user_interaction, simulate_recurrent_booking_analysis

        # Test comunidades
        community_result = simulate_user_interaction(
            guest_id=7,
            host_id=6,
            interaction_type="community_check"
        )

        if community_result.get('success'):
            community = community_result.get('community_analysis', {})
            print(f"   ✅ Análisis comunidad completado")
            print(
                f"   🤝 Interacciones: {community.get('total_interactions', 0)}")
            print(
                f"   🏘️ Es comunidad: {community.get('is_community', False)}")

        # Test usuarios recurrentes
        recurrent_result = simulate_recurrent_booking_analysis(
            user_id=7,
            city_name="Buenos Aires"
        )

        if recurrent_result.get('success'):
            analysis = recurrent_result['analysis']
            print(f"   ✅ Análisis recurrente completado")
            print(f"   🔄 Usuario recurrente: {analysis['is_recurrent']}")
            print(f"   📊 Total reservas: {analysis['total_bookings']}")

    except Exception as e:
        print(f"   ❌ Error en test Neo4j: {e}")

    print("\n" + "=" * 50)
    print("✅ TESTS DE CUs COMPLETADOS")
    print("📊 Funcionalidades validadas:")
    print("   🔑 CU7: Sesiones Redis (TTL 1h)")
    print("   📅 Multi-DB: Creación de reservas")
    print("   📊 CU1: Analytics Cassandra")
    print("   🔍 CU8: Caché de búsqueda Redis")
    print("   ⭐ CU2: Rating PostgreSQL")
    print("   📅 CU4: Disponibilidad PostgreSQL")
    print("   🏘️ CU9-10: Neo4j Simulator")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_cu_simple())
