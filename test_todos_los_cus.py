"""
Test completo de todos los Casos de Uso (CUs) del sistema Airbnb.

CUs a testear:
1. Tasa de ocupación por ciudad en un rango de fechas (Cassandra)
2. Promedio de rating por anfitrión (PostgreSQL)
3. Alojamientos en una ciudad específica con capacidad ≥3 y wifi (Cassandra)
4. Disponibles en una fecha específica (PostgreSQL/Cassandra)
5. Reservas por (fecha, ciudad) (Cassandra)
6. Reservas por (host, fecha) (Cassandra)
7. Sesión de un huésped (1h) (Redis)
8. Caché de resultados de búsqueda con filtros (TTL 5 min) (Redis)
9. Usuarios que regresaron a la misma ciudad (≥2 reservas) (Neo4j/Simulator)
10. Comunidades de host–huésped con ≥3 interacciones (Neo4j/Simulator)
"""

import asyncio
import structlog
from datetime import date, datetime, timedelta
import json
from typing import Dict, Any, List

# Servicios
from services.auth import AuthService
from services.session import SessionManager
from services.reservations import ReservationService
from services.analytics import AnalyticsService
from services.search import SearchService
from services.properties import PropertyService

# Bases de datos directas
from db.postgres import get_client as get_postgres_client
from db.cassandra import get_astra_client, find_documents, insert_document
from db.redisdb import get_client as get_redis_client
from db.mongo import MongoService

logger = structlog.get_logger(__name__)


class CUTester:
    """Tester completo de todos los Casos de Uso"""

    def __init__(self):
        self.results = {}
        self.test_user_email = "tomaslonati@gmail.com"
        self.test_user_id = None
        self.session_token = None
        self.services = {}

    async def initialize_services(self):
        """Inicializar todos los servicios necesarios"""
        try:
            print("🔧 Inicializando servicios...")

            # Servicios principales
            self.services['auth'] = AuthService()
            self.services['session'] = SessionManager()
            self.services['reservations'] = ReservationService()
            self.services['analytics'] = AnalyticsService()
            self.services['search'] = SearchService()
            self.services['properties'] = PropertyService()

            # Bases de datos directas
            self.services['cassandra'] = await get_astra_client()
            self.services['redis'] = await get_redis_client()
            self.services['mongo'] = MongoService()

            print("✅ Servicios inicializados")
            return True

        except Exception as e:
            print(f"❌ Error inicializando servicios: {e}")
            return False

    async def setup_test_session(self):
        """Configurar sesión de test"""
        try:
            print(f"🔑 Configurando sesión para {self.test_user_email}...")

            # Login para obtener sesión
            login_result = await self.services['auth'].login(
                email=self.test_user_email,
                password="123456"
            )

            if login_result.get('success'):
                self.test_user_id = login_result['user_id']
                self.session_token = login_result['session_token']
                print(f"✅ Sesión creada: Usuario {self.test_user_id}")
                return True
            else:
                print(f"❌ Error en login: {login_result.get('error')}")
                return False

        except Exception as e:
            print(f"❌ Error configurando sesión: {e}")
            return False

    async def test_cu1_ocupacion_por_ciudad(self) -> Dict[str, Any]:
        """CU1: Tasa de ocupación por ciudad en un rango de fechas"""
        print("\n📊 CU1: Tasa de ocupación por ciudad en un rango de fechas")

        try:
            # Fechas de test
            fecha_inicio = date(2025, 12, 1)
            fecha_fin = date(2025, 12, 31)
            ciudad = "Buenos Aires"

            print(f"   📅 Rango: {fecha_inicio} - {fecha_fin}")
            print(f"   🏙️ Ciudad: {ciudad}")

            # Llamar al servicio de analytics
            result = await self.services['analytics'].get_city_occupancy_rate(
                city_name=ciudad,
                start_date=fecha_inicio,
                end_date=fecha_fin
            )

            if result.get('success'):
                occupancy_data = result['data']
                print(
                    f"   ✅ Tasa de ocupación: {occupancy_data.get('occupancy_rate', 0):.2f}%")
                print(
                    f"   🏠 Propiedades totales: {occupancy_data.get('total_properties', 0)}")
                print(
                    f"   📊 Días ocupados: {occupancy_data.get('occupied_days', 0)}")

                return {
                    "success": True,
                    "data": occupancy_data
                }
            else:
                print(f"   ❌ Error: {result.get('error')}")
                return {"success": False, "error": result.get('error')}

        except Exception as e:
            error_msg = f"Error en CU1: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu2_promedio_rating_anfitrion(self) -> Dict[str, Any]:
        """CU2: Promedio de rating por anfitrión"""
        print("\n⭐ CU2: Promedio de rating por anfitrión")

        try:
            # Test con anfitrión ID 6 (que sabemos que existe)
            anfitrion_id = 6
            print(f"   👤 Anfitrión ID: {anfitrion_id}")

            # Query directa a PostgreSQL para obtener ratings
            pool = await get_postgres_client()
            async with pool.acquire() as conn:
                query = """
                SELECT 
                    AVG(r.calificacion) as promedio_rating,
                    COUNT(r.id) as total_reseñas,
                    u.nombre as anfitrion_nombre
                FROM reseñas r
                JOIN reserva res ON r.reserva_id = res.id
                JOIN propiedades p ON res.propiedad_id = p.id
                JOIN usuarios u ON p.anfitrion_id = u.id
                WHERE p.anfitrion_id = $1
                GROUP BY p.anfitrion_id, u.nombre
                """

                result = await conn.fetchrow(query, anfitrion_id)

                if result:
                    promedio = float(
                        result['promedio_rating']) if result['promedio_rating'] else 0.0
                    total = result['total_reseñas']
                    nombre = result['anfitrion_nombre']

                    print(f"   ✅ Anfitrión: {nombre}")
                    print(f"   ⭐ Promedio: {promedio:.2f}/5")
                    print(f"   📊 Total reseñas: {total}")

                    return {
                        "success": True,
                        "data": {
                            "anfitrion_id": anfitrion_id,
                            "anfitrion_nombre": nombre,
                            "promedio_rating": promedio,
                            "total_reseñas": total
                        }
                    }
                else:
                    print(
                        f"   ⚠️ No hay reseñas para anfitrión {anfitrion_id}")
                    return {
                        "success": True,
                        "data": {
                            "anfitrion_id": anfitrion_id,
                            "promedio_rating": 0.0,
                            "total_reseñas": 0
                        }
                    }

        except Exception as e:
            error_msg = f"Error en CU2: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu3_propiedades_filtros(self) -> Dict[str, Any]:
        """CU3: Alojamientos en una ciudad específica con capacidad ≥3 y wifi"""
        print("\n🏠 CU3: Alojamientos con capacidad ≥3 y wifi")

        try:
            ciudad = "Buenos Aires"
            min_capacity = 3

            print(f"   🏙️ Ciudad: {ciudad}")
            print(f"   👥 Capacidad mínima: {min_capacity}")
            print(f"   📶 Con WiFi: Sí")

            # Buscar en Cassandra
            cassandra_db = self.services['cassandra']
            collection = cassandra_db.get_collection(
                "properties_by_city_wifi_capacity")

            # Query a la colección properties_by_city_wifi_capacity
            filter_query = {
                "ciudad": ciudad,
                "tiene_wifi": True,
                "capacidad_maxima": {"$gte": min_capacity}
            }

            cursor = collection.find(filter_query, limit=50)
            properties = list(cursor)

            print(f"   ✅ Propiedades encontradas: {len(properties)}")

            if properties:
                # Mostrar solo las primeras 3
                for i, prop in enumerate(properties[:3]):
                    print(f"      🏠 {i+1}. ID: {prop.get('propiedad_id')}, "
                          f"Capacidad: {prop.get('capacidad_maxima')}, "
                          f"WiFi: {prop.get('tiene_wifi')}")

            return {
                "success": True,
                "data": {
                    "ciudad": ciudad,
                    "propiedades_encontradas": len(properties),
                    "propiedades": properties[:10]  # Primeras 10
                }
            }

        except Exception as e:
            error_msg = f"Error en CU3: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu4_disponibles_fecha(self) -> Dict[str, Any]:
        """CU4: Disponibles en una fecha específica"""
        print("\n📅 CU4: Propiedades disponibles en fecha específica")

        try:
            fecha_test = date(2026, 1, 15)  # Fecha futura
            print(f"   📅 Fecha: {fecha_test}")

            # Buscar en PostgreSQL
            pool = await get_postgres_client()
            async with pool.acquire() as conn:
                query = """
                SELECT 
                    p.id,
                    p.nombre,
                    p.ciudad,
                    p.precio_por_noche,
                    pd.disponible
                FROM propiedades p
                LEFT JOIN propiedad_disponibilidad pd ON p.id = pd.propiedad_id 
                    AND pd.fecha = $1
                WHERE (pd.disponible = true OR pd.disponible IS NULL)
                LIMIT 20
                """

                results = await conn.fetch(query, fecha_test)

                print(f"   ✅ Propiedades disponibles: {len(results)}")

                if results:
                    # Mostrar solo las primeras 5
                    for i, prop in enumerate(results[:5]):
                        print(f"      🏠 {i+1}. {prop['nombre']} - {prop['ciudad']} "
                              f"(${prop['precio_por_noche']}/noche)")

                return {
                    "success": True,
                    "data": {
                        "fecha": fecha_test.isoformat(),
                        "propiedades_disponibles": len(results),
                        "propiedades": [dict(r) for r in results[:10]]
                    }
                }

        except Exception as e:
            error_msg = f"Error en CU4: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu5_reservas_fecha_ciudad(self) -> Dict[str, Any]:
        """CU5: Reservas por (fecha, ciudad)"""
        print("\n📊 CU5: Reservas por fecha y ciudad")

        try:
            fecha_test = date(2025, 12, 25)
            ciudad = "Buenos Aires"

            print(f"   📅 Fecha: {fecha_test}")
            print(f"   🏙️ Ciudad: {ciudad}")

            # Buscar en Cassandra
            cassandra_db = self.services['cassandra']
            collection = cassandra_db.get_collection(
                "reservas_por_ciudad_fecha")

            filter_query = {
                "fecha": fecha_test.isoformat(),
                "ciudad": ciudad
            }

            cursor = collection.find(filter_query, limit=50)
            reservas = list(cursor)

            print(f"   ✅ Reservas encontradas: {len(reservas)}")

            if reservas:
                for i, res in enumerate(reservas[:3]):
                    print(f"      📋 {i+1}. Reserva ID: {res.get('reserva_id')}, "
                          f"Huésped: {res.get('huesped_id')}")

            return {
                "success": True,
                "data": {
                    "fecha": fecha_test.isoformat(),
                    "ciudad": ciudad,
                    "reservas_encontradas": len(reservas),
                    "reservas": reservas[:10]
                }
            }

        except Exception as e:
            error_msg = f"Error en CU5: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu6_reservas_host_fecha(self) -> Dict[str, Any]:
        """CU6: Reservas por (host, fecha)"""
        print("\n👤 CU6: Reservas por host y fecha")

        try:
            fecha_test = date(2025, 12, 25)
            host_id = 6  # Host de test

            print(f"   📅 Fecha: {fecha_test}")
            print(f"   👤 Host ID: {host_id}")

            # Buscar en Cassandra
            cassandra_db = self.services['cassandra']
            collection = cassandra_db.get_collection("reservas_por_host_fecha")

            filter_query = {
                "host_id": host_id,
                "fecha": fecha_test.isoformat()
            }

            cursor = collection.find(filter_query, limit=50)
            reservas = list(cursor)

            print(f"   ✅ Reservas encontradas: {len(reservas)}")

            if reservas:
                for i, res in enumerate(reservas[:3]):
                    print(f"      📋 {i+1}. Reserva ID: {res.get('reserva_id')}, "
                          f"Propiedad: {res.get('propiedad_id')}")

            return {
                "success": True,
                "data": {
                    "fecha": fecha_test.isoformat(),
                    "host_id": host_id,
                    "reservas_encontradas": len(reservas),
                    "reservas": reservas[:10]
                }
            }

        except Exception as e:
            error_msg = f"Error en CU6: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu7_sesion_huesped(self) -> Dict[str, Any]:
        """CU7: Sesión de un huésped (1h)"""
        print("\n🔑 CU7: Sesión de huésped (1h TTL)")

        try:
            if not self.session_token:
                return {"success": False, "error": "No hay sesión activa"}

            print(f"   🔑 Token: {self.session_token[:10]}...")

            # Verificar sesión en Redis
            session_data = await self.services['session'].get_session(self.session_token)

            if session_data:
                ttl = await self.services['session'].get_session_ttl(self.session_token)
                print(f"   ✅ Sesión activa")
                print(f"   👤 Usuario ID: {session_data.get('user_id')}")
                print(f"   ⏱️ TTL restante: {ttl} segundos")

                return {
                    "success": True,
                    "data": {
                        "session_token": self.session_token,
                        "user_id": session_data.get('user_id'),
                        "ttl_seconds": ttl,
                        "session_data": session_data
                    }
                }
            else:
                print(f"   ❌ Sesión no encontrada o expirada")
                return {"success": False, "error": "Sesión no encontrada"}

        except Exception as e:
            error_msg = f"Error en CU7: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu8_cache_busqueda(self) -> Dict[str, Any]:
        """CU8: Caché de resultados de búsqueda con filtros (TTL 5 min)"""
        print("\n🔍 CU8: Caché de búsqueda (TTL 5 min)")

        try:
            # Realizar búsqueda que debería usar caché
            search_params = {
                "ciudad": "Buenos Aires",
                "capacidad_minima": 2,
                "precio_maximo": 200
            }

            print(f"   🔍 Parámetros: {search_params}")

            # Primera búsqueda (debería crear caché)
            start_time = datetime.now()
            result1 = await self.services['search'].search_properties(**search_params)
            time1 = (datetime.now() - start_time).total_seconds()

            # Segunda búsqueda (debería usar caché)
            start_time = datetime.now()
            result2 = await self.services['search'].search_properties(**search_params)
            time2 = (datetime.now() - start_time).total_seconds()

            print(f"   ✅ Primera búsqueda: {time1:.3f}s")
            print(f"   ✅ Segunda búsqueda: {time2:.3f}s")
            print(
                f"   📊 Mejora: {((time1 - time2) / time1 * 100):.1f}%" if time1 > time2 else "No hay mejora")

            if result1.get('success'):
                properties_count = len(result1.get('properties', []))
                print(f"   🏠 Propiedades encontradas: {properties_count}")

            return {
                "success": True,
                "data": {
                    "search_params": search_params,
                    "first_search_time": time1,
                    "second_search_time": time2,
                    "cache_improvement": time1 > time2,
                    "properties_count": len(result1.get('properties', []))
                }
            }

        except Exception as e:
            error_msg = f"Error en CU8: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu9_usuarios_recurrentes(self) -> Dict[str, Any]:
        """CU9: Usuarios que regresaron a la misma ciudad (≥2 reservas)"""
        print("\n🔄 CU9: Usuarios recurrentes (≥2 reservas misma ciudad)")

        try:
            # Este CU usa Neo4j/Simulator
            print(f"   👤 Usuario test: {self.test_user_id}")

            # Simular análisis de reservas recurrentes
            from neo4j_simulator import simulate_recurrent_booking_analysis

            result = simulate_recurrent_booking_analysis(
                user_id=self.test_user_id,
                city_name="Buenos Aires"
            )

            if result.get('success'):
                analysis = result['analysis']
                print(
                    f"   ✅ Usuario recurrente detectado: {analysis['is_recurrent']}")
                print(f"   📊 Total reservas: {analysis['total_bookings']}")
                print(f"   🏙️ Ciudades únicas: {analysis['unique_cities']}")
                print(
                    f"   🔄 Reservas recurrentes: {analysis['recurrent_bookings']}")

                return {
                    "success": True,
                    "data": result
                }
            else:
                print(f"   ❌ Error en simulación: {result.get('error')}")
                return {"success": False, "error": result.get('error')}

        except Exception as e:
            error_msg = f"Error en CU9: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def test_cu10_comunidades_interacciones(self) -> Dict[str, Any]:
        """CU10: Comunidades de host–huésped con ≥3 interacciones"""
        print("\n🏘️ CU10: Comunidades host-huésped (≥3 interacciones)")

        try:
            # Este CU usa Neo4j/Simulator
            host_id = 6
            guest_id = self.test_user_id

            print(f"   👤 Host: {host_id}, Huésped: {guest_id}")

            # Simular análisis de comunidades
            from neo4j_simulator import simulate_user_interaction

            result = simulate_user_interaction(
                guest_id=guest_id,
                host_id=host_id,
                interaction_type="community_check"
            )

            if result.get('success'):
                community_data = result.get('community_analysis', {})
                print(f"   ✅ Análisis completado")
                print(
                    f"   🤝 Total interacciones: {community_data.get('total_interactions', 0)}")
                print(
                    f"   🏘️ Es comunidad: {community_data.get('is_community', False)}")

                return {
                    "success": True,
                    "data": {
                        "host_id": host_id,
                        "guest_id": guest_id,
                        "community_analysis": community_data
                    }
                }
            else:
                print(f"   ❌ Error en simulación: {result.get('error')}")
                return {"success": False, "error": result.get('error')}

        except Exception as e:
            error_msg = f"Error en CU10: {e}"
            print(f"   ❌ {error_msg}")
            return {"success": False, "error": error_msg}

    async def run_all_tests(self):
        """Ejecutar todos los tests de CUs"""
        print("🚀 INICIANDO TESTS DE TODOS LOS CUs")
        print("=" * 60)

        # Inicializar
        if not await self.initialize_services():
            return

        if not await self.setup_test_session():
            return

        # Lista de tests
        tests = [
            ("CU1", self.test_cu1_ocupacion_por_ciudad),
            ("CU2", self.test_cu2_promedio_rating_anfitrion),
            ("CU3", self.test_cu3_propiedades_filtros),
            ("CU4", self.test_cu4_disponibles_fecha),
            ("CU5", self.test_cu5_reservas_fecha_ciudad),
            ("CU6", self.test_cu6_reservas_host_fecha),
            ("CU7", self.test_cu7_sesion_huesped),
            ("CU8", self.test_cu8_cache_busqueda),
            ("CU9", self.test_cu9_usuarios_recurrentes),
            ("CU10", self.test_cu10_comunidades_interacciones),
        ]

        # Ejecutar tests
        for test_name, test_func in tests:
            try:
                result = await test_func()
                self.results[test_name] = result
            except Exception as e:
                print(f"❌ Error ejecutando {test_name}: {e}")
                self.results[test_name] = {"success": False, "error": str(e)}

        # Resumen final
        await self.print_summary()
        await self.cleanup()

    async def print_summary(self):
        """Imprimir resumen de resultados"""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE TESTS DE CUs")
        print("=" * 60)

        success_count = 0
        total_count = len(self.results)

        for test_name, result in self.results.items():
            status = "✅" if result.get('success') else "❌"
            print(
                f"{status} {test_name}: {'ÉXITO' if result.get('success') else 'FALLO'}")

            if not result.get('success'):
                print(f"   Error: {result.get('error', 'Desconocido')}")
            else:
                success_count += 1

        print(
            f"\n📈 RESULTADO FINAL: {success_count}/{total_count} tests exitosos")
        success_rate = (success_count / total_count) * \
            100 if total_count > 0 else 0
        print(f"📊 Tasa de éxito: {success_rate:.1f}%")

    async def cleanup(self):
        """Limpiar recursos"""
        try:
            print("\n🧹 Limpiando recursos...")

            # Cerrar servicios que lo requieran
            for service_name, service in self.services.items():
                if hasattr(service, 'close') and callable(service.close):
                    try:
                        await service.close()
                    except Exception as e:
                        print(f"⚠️ Error cerrando {service_name}: {e}")

            print("✅ Limpieza completada")

        except Exception as e:
            print(f"⚠️ Error en limpieza: {e}")


async def main():
    """Función principal"""
    tester = CUTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
