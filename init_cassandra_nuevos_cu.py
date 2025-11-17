"""
Script para crear las tablas de Cassandra para los nuevos casos de uso.
"""

import asyncio
from db.cassandra import get_astra_client
from utils.logging import get_logger

logger = get_logger(__name__)


async def create_nuevas_tablas_cassandra():
    """Crea las 3 nuevas tablas/colecciones de Cassandra para los CU 4, 5, 6."""
    try:
        database = await get_astra_client()
        
        # 1. Crear tabla propiedades_disponibles_por_fecha (CU 4)
        print("🔨 Creando tabla: propiedades_disponibles_por_fecha")
        try:
            collection = database.create_collection("propiedades_disponibles_por_fecha")
            logger.info("✅ Tabla 'propiedades_disponibles_por_fecha' creada exitosamente")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ℹ️ Tabla 'propiedades_disponibles_por_fecha' ya existe")
            else:
                logger.error(f"Error creando 'propiedades_disponibles_por_fecha': {e}")
        
        # 2. Crear tabla reservas_por_ciudad_fecha (CU 5)
        print("🔨 Creando tabla: reservas_por_ciudad_fecha")
        try:
            collection = database.create_collection("reservas_por_ciudad_fecha")
            logger.info("✅ Tabla 'reservas_por_ciudad_fecha' creada exitosamente")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ℹ️ Tabla 'reservas_por_ciudad_fecha' ya existe")
            else:
                logger.error(f"Error creando 'reservas_por_ciudad_fecha': {e}")
        
        # 3. Crear tabla reservas_por_host_fecha (CU 6)
        print("🔨 Creando tabla: reservas_por_host_fecha")
        try:
            collection = database.create_collection("reservas_por_host_fecha")
            logger.info("✅ Tabla 'reservas_por_host_fecha' creada exitosamente")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ℹ️ Tabla 'reservas_por_host_fecha' ya existe")
            else:
                logger.error(f"Error creando 'reservas_por_host_fecha': {e}")
        
        # Verificar colecciones existentes
        collections = database.list_collection_names()
        print(f"\n📋 Colecciones existentes: {collections}")
        
        print("\n✅ Proceso de creación de tablas completado")
        
    except Exception as e:
        logger.error(f"Error general creando tablas: {e}")
        print(f"❌ Error: {e}")


async def populate_sample_data():
    """Poblar con datos de muestra para pruebas."""
    try:
        database = await get_astra_client()
        
        print("\n📊 Poblando datos de muestra...")
        
        # Datos de muestra para propiedades disponibles
        sample_propiedades = [
            {
                "_id": "2026-03-15_29",
                "fecha": "2026-03-15",
                "propiedad_id": 29,
                "ciudad_id": 1,
                "ciudad_nombre": "Buenos Aires",
                "precio_noche": 75.00,
                "capacidad_huespedes": 4,
                "wifi": True,
                "disponible": True
            },
            {
                "_id": "2026-03-15_30",
                "fecha": "2026-03-15",
                "propiedad_id": 30,
                "ciudad_id": 1,
                "ciudad_nombre": "Buenos Aires", 
                "precio_noche": 85.00,
                "capacidad_huespedes": 2,
                "wifi": True,
                "disponible": True
            },
            {
                "_id": "2026-03-15_31",
                "fecha": "2026-03-15",
                "propiedad_id": 31,
                "ciudad_id": 2,
                "ciudad_nombre": "Madrid",
                "precio_noche": 95.00,
                "capacidad_huespedes": 6,
                "wifi": False,
                "disponible": True
            }
        ]
        
        # Insertar datos de propiedades disponibles
        propiedades_collection = database.get_collection("propiedades_disponibles_por_fecha")
        for prop in sample_propiedades:
            try:
                propiedades_collection.insert_one(prop)
                print(f"✅ Insertada propiedad {prop['propiedad_id']} para {prop['fecha']}")
            except Exception as e:
                print(f"⚠️ Error insertando propiedad {prop['propiedad_id']}: {e}")
        
        # Datos de muestra para reservas por ciudad
        sample_reservas_ciudad = [
            {
                "_id": "1_2026-03-15_101",
                "ciudad_id": 1,
                "fecha": "2026-03-15",
                "reserva_id": 101,
                "propiedad_id": 29,
                "host_id": 1,
                "huesped_id": 5,
                "precio_total": 225.00,
                "estado": "confirmada"
            },
            {
                "_id": "1_2026-03-15_102", 
                "ciudad_id": 1,
                "fecha": "2026-03-15",
                "reserva_id": 102,
                "propiedad_id": 30,
                "host_id": 2,
                "huesped_id": 6,
                "precio_total": 255.00,
                "estado": "confirmada"
            }
        ]
        
        # Insertar datos de reservas por ciudad
        ciudad_collection = database.get_collection("reservas_por_ciudad_fecha")
        for reserva in sample_reservas_ciudad:
            try:
                ciudad_collection.insert_one(reserva)
                print(f"✅ Insertada reserva {reserva['reserva_id']} para ciudad {reserva['ciudad_id']}")
            except Exception as e:
                print(f"⚠️ Error insertando reserva ciudad {reserva['reserva_id']}: {e}")
        
        # Datos de muestra para reservas por host
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
        
        print("\n✅ Datos de muestra insertados exitosamente")
        
    except Exception as e:
        logger.error(f"Error poblando datos de muestra: {e}")
        print(f"❌ Error: {e}")


async def main():
    """Función principal."""
    print("🚀 INICIALIZANDO TABLAS CASSANDRA PARA NUEVOS CU")
    print("=" * 60)
    
    # Crear tablas
    await create_nuevas_tablas_cassandra()
    
    # Preguntar si poblar con datos de muestra
    response = input("\n¿Desea poblar con datos de muestra para pruebas? (s/n): ").lower().strip()
    if response == 's':
        await populate_sample_data()
    
    print("\n🎉 ¡Proceso completado!")


if __name__ == "__main__":
    asyncio.run(main())