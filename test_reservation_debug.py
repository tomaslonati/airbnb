import asyncio
import structlog
from datetime import date
from services.reservations import ReservationService

logger = structlog.get_logger()


async def test_reservation_creation():
    """Test específico para debug de creación de reserva"""

    print("🔍 Iniciando test de creación de reserva...")

    try:
        # Inicializar servicio
        service = ReservationService()

        print(f"✅ Servicio inicializado")

        # Datos de test
        huesped_id = 7
        propiedad_id = 8
        check_in = date(2025, 12, 28)
        check_out = date(2025, 12, 30)
        num_huespedes = 2
        comentarios = "Test para debug"

        print(f"📊 Creando reserva:")
        print(f"   👤 Huésped: {huesped_id}")
        print(f"   🏠 Propiedad: {propiedad_id}")
        print(f"   📅 Check-in: {check_in}")
        print(f"   📅 Check-out: {check_out}")
        print(f"   👥 Huéspedes: {num_huespedes}")

        # Crear reserva
        result = await service.create_reservation(
            huesped_id=huesped_id,
            propiedad_id=propiedad_id,
            check_in=check_in,
            check_out=check_out,
            num_huespedes=num_huespedes,
            comentarios=comentarios
        )

        print(f"\n🔍 Resultado completo:")
        print(f"   Success: {result.get('success')}")

        if result.get('success'):
            reservation = result.get('reservation', {})
            print(f"   🆔 ID: {reservation.get('id')}")
            print(f"   🆔 Tipo ID: {type(reservation.get('id'))}")
            print(f"   💰 Precio total: {reservation.get('precio_total')}")
            print(f"   💰 Tipo precio: {type(reservation.get('precio_total'))}")
            print(f"   📊 Reserva completa: {reservation}")
        else:
            print(f"   ❌ Error: {result.get('error')}")

        await service.close()

    except Exception as e:
        print(f"❌ Error en test: {e}")
        logger.error("Error en test de creación", error=str(e))

if __name__ == "__main__":
    asyncio.run(test_reservation_creation())
