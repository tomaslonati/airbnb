import asyncio
import structlog
from datetime import date
from services.reservations import ReservationService

logger = structlog.get_logger()


async def test_price_calculation():
    """Test específico para debug de precios"""

    print("🔍 Iniciando test de cálculo de precios...")

    try:
        # Inicializar servicio
        service = ReservationService()

        # Test 1: Verificar que el servicio esté funcionando
        print(f"✅ Servicio inicializado: {type(service)}")

        # Test 2: Revisar la propiedad 8
        property_id = 8
        fecha_inicio = date(2025, 12, 25)
        fecha_fin = date(2025, 12, 27)

        print(f"📊 Calculando precio para propiedad {property_id}")
        print(f"📅 Fechas: {fecha_inicio} a {fecha_fin}")

        # Llamar función de cálculo
        precio_total = await service._calculate_total_price(property_id, fecha_inicio, fecha_fin)

        print(f"💰 Precio calculado: {precio_total}")
        print(f"🔍 Tipo de dato: {type(precio_total)}")

        # Test 3: Verificar disponibilidad base
        print(f"\n🔍 Verificando disponibilidad directa...")

        # Verificar si hay conexión a postgres
        if hasattr(service, 'postgres_db') and service.postgres_db:
            print("✅ Conexión PostgreSQL disponible")

            # Query directa para verificar disponibilidad
            query = """
            SELECT precio_por_noche, disponible 
            FROM propiedad_disponibilidad 
            WHERE propiedad_id = $1 
            AND fecha BETWEEN $2 AND $3
            ORDER BY fecha
            """

            try:
                async with service.postgres_db.pool.acquire() as conn:
                    rows = await conn.fetch(query, property_id, fecha_inicio, fecha_fin)
                    print(f"📊 Registros encontrados: {len(rows)}")

                    if rows:
                        for row in rows:
                            print(
                                f"   💰 Precio: {row['precio_por_noche']}, Disponible: {row['disponible']}")
                    else:
                        print(
                            "⚠️ No hay registros en propiedad_disponibilidad para estas fechas")

                        # Verificar si existe la propiedad
                        prop_query = "SELECT id, precio_por_noche FROM propiedades WHERE id = $1"
                        prop_result = await conn.fetchrow(prop_query, property_id)

                        if prop_result:
                            print(
                                f"🏠 Propiedad encontrada: ID {prop_result['id']}, Precio base: ${prop_result['precio_por_noche']}")
                        else:
                            print(f"❌ Propiedad {property_id} no existe")

            except Exception as e:
                print(f"❌ Error consultando base: {e}")
        else:
            print("❌ No hay conexión PostgreSQL disponible")

        await service.close()

    except Exception as e:
        print(f"❌ Error en test: {e}")
        logger.error("Error en test de precios", error=str(e))

if __name__ == "__main__":
    asyncio.run(test_price_calculation())
