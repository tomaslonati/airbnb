"""
Script para poblar datos de muestra en la tabla reservas_por_host_fecha.
"""

import asyncio
from db.cassandra import get_astra_client
from utils.logging import get_logger

logger = get_logger(__name__)

async def populate_host_data():
    """Poblar datos de muestra para tabla de host."""
    try:
        database = await get_astra_client()
        
        print("📊 Poblando datos de muestra para reservas_por_host_fecha...")
        
        # Datos de muestra para reservas por host (esquema correcto)
        sample_reservas_host = [
            {
                "host_id": "1",
                "fecha": "2026-03-15", 
                "reserva_id": "101",
                "propiedad_id": "29",
                "huesped_id": "5",
                "total_price": 225.00,
                "status": "confirmada"
            },
            {
                "host_id": "2",
                "fecha": "2026-03-15",
                "reserva_id": "102", 
                "propiedad_id": "30",
                "huesped_id": "6",
                "total_price": 255.00,
                "status": "confirmada"
            },
            {
                "host_id": "1",
                "fecha": "2026-03-15",
                "reserva_id": "103",
                "propiedad_id": "32",
                "huesped_id": "7",
                "total_price": 180.00,
                "status": "confirmada"
            }
        ]
        
        # Insertar datos de reservas por host
        host_collection = database.get_collection("reservas_por_host_fecha")
        for reserva in sample_reservas_host:
            try:
                host_collection.insert_one(reserva)
                print(f"✅ Insertada reserva {reserva['reserva_id']} para host {reserva['host_id']}")
            except Exception as e:
                print(f"⚠️ Error insertando reserva host {reserva['reserva_id']}: {e}")
        
        print("\n✅ Datos de host insertados exitosamente")
        
    except Exception as e:
        logger.error(f"Error poblando datos de host: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(populate_host_data())