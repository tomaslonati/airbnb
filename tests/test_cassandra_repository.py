"""
Test de conexión y operaciones básicas para el repositorio de Cassandra.
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal
from repositories.cassandra_reservation_repository import get_cassandra_reservation_repository
from utils.logging import get_logger
from concurrent.futures import ThreadPoolExecutor

logger = get_logger(__name__)


async def test_cassandra_repository():
    """Prueba las operaciones básicas del repositorio Cassandra."""
    
    print("🧪 Probando repositorio de Cassandra...")
    
    try:
        # Obtener instancia del repositorio
        repo = await get_cassandra_reservation_repository()
        
        print("✅ Conexión establecida")
        
        # Datos de prueba
        ciudad_id = 1
        propiedad_id = 101
        host_id = "550e8400-e29b-41d4-a716-446655440000"
        huesped_id = "550e8400-e29b-41d4-a716-446655440001" 
        reserva_id = "550e8400-e29b-41d4-a716-446655440002"
        fecha_inicio = date.today() + timedelta(days=7)
        fecha_fin = fecha_inicio + timedelta(days=3)
        monto = Decimal('150.00')
        
        print(f"📅 Testeo para fechas: {fecha_inicio} a {fecha_fin}")
        
        # Usar ThreadPoolExecutor para ejecutar métodos síncronos
        executor = ThreadPoolExecutor()
        loop = asyncio.get_event_loop()
        
        # Test 1: Sincronizar creación de reserva
        print("\n1️⃣ Probando creación de reserva...")
        await loop.run_in_executor(
            executor,
            repo.sync_reservation_creation,
            ciudad_id, host_id, str(propiedad_id), huesped_id, reserva_id,
            fecha_inicio, fecha_fin, monto
        )
        print("✅ Reserva creada")
        
        # Test 2: Sincronizar cancelación de reserva
        print("\n2️⃣ Probando cancelación de reserva...")
        await loop.run_in_executor(
            executor,
            repo.sync_reservation_cancellation,
            ciudad_id, host_id, str(propiedad_id), reserva_id,
            fecha_inicio, fecha_fin
        )
        print("✅ Reserva cancelada")
        
        # Test 3: Generar disponibilidad
        print("\n3️⃣ Probando generación de disponibilidad...")
        await loop.run_in_executor(
            executor,
            repo.sync_availability_generation,
            ciudad_id, propiedad_id, fecha_inicio, 7
        )
        print("✅ Disponibilidad generada")
        
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        print(f"❌ Error: {e}")
        raise
    
    finally:
        if 'repo' in locals() and repo:
            repo.close()
            print("🔌 Conexión cerrada")


async def main():
    """Función principal del test."""
    await test_cassandra_repository()


if __name__ == "__main__":
    asyncio.run(main())