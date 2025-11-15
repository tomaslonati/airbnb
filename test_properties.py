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

    # TEST 7: Actualizar propiedad
    print("\n" + "-"*70)
    print("✅ TEST 7: Actualizar propiedad")
    print("-"*70)
    
    property_to_update = property_id  # Usar la ID del TEST 1
    update_result = await service.update_property(
        property_to_update,
        nombre="Depto Actualizado - Palermo",
        capacidad=5,
        descripcion="Departamento mejorado con actualizaciones"
    )
    
    if update_result["success"]:
        print(f"✅ Propiedad actualizada:")
        print(f"   ID: {update_result['property']['id']}")
        print(f"   Nuevo nombre: {update_result['property']['nombre']}")
        print(f"   Nueva capacidad: {update_result['property']['capacidad']}")
    else:
        print(f"❌ ERROR: {update_result['error']}")

    # Verificar que la actualización se guardó
    verify_result = await service.get_property(property_to_update)
    if verify_result["success"] and verify_result["property"]["nombre"] == "Depto Actualizado - Palermo":
        print(f"✅ Actualización verificada en BD")
    else:
        print(f"❌ ERROR: Actualización no se guardó correctamente")

    # TEST 8: Eliminar propiedad
    print("\n" + "-"*70)
    print("✅ TEST 8: Eliminar propiedad")
    print("-"*70)
    
    # Primero crear una propiedad temporal para eliminar
    temp_property_data = {
        "nombre": f"Propiedad Temporal - {hash('delete_test') % 10000}",
        "descripcion": "Esta propiedad será eliminada",
        "capacidad": 2,
        "ciudad_id": 1,
        "anfitrion_id": 1,
        "tipo_propiedad_id": 1,
        "amenities": [1],
        "servicios": [1],
        "generar_calendario": True,
        "dias_calendario": 10
    }
    
    temp_result = await service.create_property(**temp_property_data)
    temp_property_id = temp_result["property_id"]
    print(f"📝 Propiedad temporal creada con ID: {temp_property_id}")
    
    # Eliminar la propiedad temporal
    delete_result = await service.delete_property(temp_property_id)
    
    if delete_result["success"]:
        print(f"✅ Propiedad eliminada:")
        print(f"   {delete_result['message']}")
    else:
        print(f"❌ ERROR: {delete_result['error']}")
    
    # Verificar que se eliminó
    verify_delete = await service.get_property(temp_property_id)
    if not verify_delete["success"] and ("no existe" in verify_delete.get("error", "") or "no encontrada" in verify_delete.get("error", "")):
        print(f"✅ Eliminación verificada - Propiedad no existe en BD")
    else:
        print(f"❌ ERROR: Propiedad aún existe en BD después de eliminar (respuesta: {verify_delete})")
    
    print("\n" + "="*70)
    print("✨ Pruebas completadas")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_properties())

