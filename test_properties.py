"""
Script de prueba completo para el servicio de propiedades.
Valida transacciones, relaciones, y manejo de errores.
"""

import asyncio
import sys
from services.properties import PropertyService
from utils.logging import get_logger, configure_logging

configure_logging()
logger = get_logger(__name__)


async def test_properties():
    """Pruebas completas del servicio de propiedades."""
    
    service = PropertyService()
    
    print("\n" + "="*70)
    print("🧪 PRUEBAS COMPLETAS DEL SERVICIO DE PROPIEDADES")
    print("="*70)
    
    # =========== TEST 1: Crear propiedad exitosamente ===========
    print("\n\n✅ TEST 1: Crear propiedad con amenities, servicios y reglas")
    print("-" * 70)
    
    test_data = {
        "nombre": "Depto Palermo Premium " + str(int(__import__('time').time())),
        "descripcion": "Hermoso departamento en el corazón de Palermo con vista a la calle",
        "capacidad": 4,
        "ciudad_id": 1,
        "anfitrion_id": 1,
        "tipo_propiedad_id": 1,
        "amenities": [1, 2],  # IDs que existen
        "servicios": [1],
        "reglas": [1],
        "generar_calendario": True,
        "dias_calendario": 30
    }
    
    result = await service.create_property(**test_data)
    
    if result["success"]:
        property_id = result["property_id"]
        print(f"✅ Propiedad creada exitosamente")
        print(f"   ID: {property_id}")
        print(f"   Nombre: {result['property']['nombre']}")
        print(f"   Capacidad: {result['property']['capacidad']}")
        
        # =========== TEST 2: Obtener propiedad con relaciones ===========
        print(f"\n\n✅ TEST 2: Obtener detalles con amenities, servicios y reglas")
        print("-" * 70)
        
        detail_result = await service.get_property(property_id)
        
        if detail_result["success"]:
            prop = detail_result["property"]
            print(f"✅ Propiedad obtenida:")
            print(f"   Nombre: {prop['nombre']}")
            print(f"   Descripción: {prop.get('descripcion', 'N/A')}")
            print(f"   Capacidad: {prop['capacidad']}")
            print(f"   Ciudad: {prop.get('ciudad', 'N/A')}")
            print(f"   Tipo: {prop.get('tipo_propiedad', 'N/A')}")
            
            # Verificar amenities
            if prop.get('amenities'):
                print(f"\n   📍 Amenities ({len(prop['amenities'])}):")
                for amenity in prop['amenities']:
                    print(f"      - {amenity['descripcion']}")
            
            # Verificar servicios
            if prop.get('servicios'):
                print(f"\n   🔧 Servicios ({len(prop['servicios'])}):")
                for servicio in prop['servicios']:
                    print(f"      - {servicio['descripcion']}")
            
            # Verificar reglas
            if prop.get('reglas'):
                print(f"\n   📋 Reglas ({len(prop['reglas'])}):")
                for regla in prop['reglas']:
                    print(f"      - {regla['descripcion']}")
        else:
            print(f"❌ Error al obtener detalles: {detail_result['error']}")
        
        # =========== TEST 3: Listar por ciudad ===========
        print(f"\n\n✅ TEST 3: Listar propiedades por ciudad")
        print("-" * 70)
        
        list_result = await service.list_properties_by_city(test_data['ciudad_id'])
        
        if list_result["success"]:
            print(f"✅ Total de propiedades en ciudad {test_data['ciudad_id']}: {list_result['total']}")
            for prop in list_result["properties"]:
                print(f"   - {prop['nombre']} (ID: {prop['id']}, Cap: {prop['capacidad']})")
        else:
            print(f"❌ Error: {list_result['error']}")
        
        # =========== TEST 4: Listar por anfitrión ===========
        print(f"\n\n✅ TEST 4: Listar propiedades por anfitrión")
        print("-" * 70)
        
        host_result = await service.list_properties_by_host(test_data['anfitrion_id'])
        
        if host_result["success"]:
            print(f"✅ Total de propiedades del anfitrión: {host_result['total']}")
            for prop in host_result["properties"]:
                print(f"   - {prop['nombre']} (ID: {prop['id']}, Cap: {prop['capacidad']})")
        else:
            print(f"❌ Error: {host_result['error']}")
    
    else:
        print(f"❌ Error al crear propiedad: {result['error']}")
    
    # =========== TEST 5: Validación de IDs inválidos ===========
    print(f"\n\n✅ TEST 5: Validación de IDs inválidos")
    print("-" * 70)
    
    invalid_data = {
        "nombre": "Propiedad con ID inválido",
        "descripcion": "Esta debería fallar",
        "capacidad": 2,
        "ciudad_id": 99999,  # ID inválido
        "anfitrion_id": 1,
        "tipo_propiedad_id": 1,
    }
    
    invalid_result = await service.create_property(**invalid_data)
    
    if not invalid_result["success"]:
        print(f"✅ Validación correcta - Error capturado:")
        print(f"   Mensaje: {invalid_result['error']}")
    else:
        print(f"❌ ERROR: Debería haber fallado con ciudad_id inválido")
    
    # =========== TEST 6: Amenity inválido ===========
    print(f"\n\n✅ TEST 6: Validación de amenity inválido")
    print("-" * 70)
    
    invalid_amenity_data = {
        "nombre": "Propiedad con amenity inválido",
        "descripcion": "Esta debería fallar",
        "capacidad": 2,
        "ciudad_id": 1,
        "anfitrion_id": 1,
        "tipo_propiedad_id": 1,
        "amenities": [99999],  # ID inválido
    }
    
    invalid_amenity_result = await service.create_property(**invalid_amenity_data)
    
    if not invalid_amenity_result["success"]:
        print(f"✅ Validación correcta - Error capturado:")
        print(f"   Mensaje: {invalid_amenity_result['error']}")
    else:
        print(f"❌ ERROR: Debería haber fallado con amenity_id inválido")
    
    print("\n" + "="*70)
    print("✨ Pruebas completadas")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_properties())

