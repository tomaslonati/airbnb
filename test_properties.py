"""
Script de prueba para el servicio de propiedades.
"""

import asyncio
import sys
from services.properties import PropertyService
from utils.logging import get_logger, configure_logging

configure_logging()
logger = get_logger(__name__)


async def test_properties():
    """Prueba el servicio de propiedades."""
    
    service = PropertyService()
    
    print("\n" + "="*60)
    print("🧪 PRUEBA DEL SERVICIO DE PROPIEDADES")
    print("="*60)
    
    # Datos de prueba
    test_data = {
        "nombre": "Departamento en Palermo - Test " + str(int(__import__('time').time())),
        "descripcion": "Hermoso departamento en el corazón de Palermo con vista a la calle",
        "capacidad": 4,
        "ciudad_id": 1,
        "anfitrion_id": 1,
        "tipo_propiedad_id": 1,
        "imagenes": ["https://example.com/imagen1.jpg", "https://example.com/imagen2.jpg"]
    }
    
    print(f"\n📝 Creando propiedad de prueba...")
    print(f"   Nombre: {test_data['nombre']}")
    print(f"   Capacidad: {test_data['capacidad']} personas")
    
    # Crear propiedad
    result = await service.create_property(**test_data)
    
    if result["success"]:
        print(f"\n✅ {result['message']}")
        property_id = result["property_id"]
        print(f"   ID creado: {property_id}")
        
        # Obtener detalles de la propiedad
        print(f"\n📖 Obteniendo detalles de la propiedad {property_id}...")
        detail_result = await service.get_property(property_id)
        
        if detail_result["success"]:
            prop = detail_result["property"]
            print(f"✅ Propiedad obtenida:")
            print(f"   ID: {prop['id']}")
            print(f"   Nombre: {prop['nombre']}")
            print(f"   Descripción: {prop.get('descripcion', 'N/A')}")
            print(f"   Capacidad: {prop['capacidad']} personas")
        else:
            print(f"❌ Error al obtener detalles: {detail_result['error']}")
        
        # Listar propiedades por ciudad
        print(f"\n📍 Listando propiedades de la ciudad {test_data['ciudad_id']}...")
        list_result = await service.list_properties_by_city(test_data['ciudad_id'])
        
        if list_result["success"]:
            print(f"✅ Total de propiedades: {list_result['total']}")
            for prop in list_result["properties"]:
                print(f"   - {prop['nombre']} (ID: {prop['id']}, Capacidad: {prop['capacidad']})")
        else:
            print(f"❌ Error al listar: {list_result['error']}")
        
        # Listar propiedades por anfitrión
        print(f"\n👤 Listando propiedades del anfitrión {test_data['anfitrion_id']}...")
        host_result = await service.list_properties_by_host(test_data['anfitrion_id'])
        
        if host_result["success"]:
            print(f"✅ Total de propiedades: {host_result['total']}")
            for prop in host_result["properties"]:
                print(f"   - {prop['nombre']} (ID: {prop['id']}, Capacidad: {prop['capacidad']})")
        else:
            print(f"❌ Error al listar: {host_result['error']}")
        
    else:
        print(f"❌ Error al crear propiedad: {result['error']}")
    
    print("\n" + "="*60)
    print("✨ Pruebas completadas")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_properties())
