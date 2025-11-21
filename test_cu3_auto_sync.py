#!/usr/bin/env python3
"""
Script para probar que las propiedades que cumplen criterios CU3 se sincronicen automáticamente con Cassandra.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from services.properties import PropertyService
from db.cassandra import find_documents, get_astra_client
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def test_cu3_auto_sync():
    """Probar que las propiedades CU3 se sincronicen automáticamente."""
    try:
        print("\n🧪 PRUEBA: SINCRONIZACIÓN AUTOMÁTICA CU3")
        print("=" * 70)

        # Inicializar servicios
        property_service = PropertyService()
        await get_astra_client()

        print("📊 Estado inicial de la colección CU3...")
        docs_antes = await find_documents("properties_by_city_wifi_capacity", {}, limit=100)
        print(f"   Propiedades en CU3 antes: {len(docs_antes)}")

        # Caso 1: Crear propiedad que SÍ cumple criterios CU3 (capacidad ≥3 y WiFi)
        print(f"\n🏠 CASO 1: Propiedad que cumple CU3 (capacidad=4, WiFi=Sí)")
        print("-" * 50)

        propiedad_cu3_si = await property_service.create_property(
            nombre="Casa de Prueba CU3 - Cumple",
            descripcion="Casa con capacidad para 4 y WiFi",
            capacidad=4,  # ≥3 ✅
            ciudad_id=1,  # Buenos Aires
            anfitrion_id=1,
            tipo_propiedad_id=1,
            servicios=[1],  # WiFi ✅
            amenities=[1, 2],
            reglas=[1],
            generar_calendario=False
        )

        if propiedad_cu3_si.get("success"):
            prop_id_1 = propiedad_cu3_si["property_id"]
            print(f"✅ Propiedad creada: ID {prop_id_1}")
            
            # Verificar que se agregó a CU3
            await asyncio.sleep(0.5)  # Pequeña pausa para sincronización
            docs_cu3_si = await find_documents("properties_by_city_wifi_capacity", {"propiedad_id": prop_id_1})
            if docs_cu3_si:
                print(f"🎯 ✅ Propiedad {prop_id_1} agregada automáticamente a CU3")
                doc = docs_cu3_si[0]
                print(f"   📄 Datos: ciudad={doc.get('ciudad_nombre')}, capacidad={doc.get('capacidad')}, wifi={doc.get('tiene_wifi')}")
            else:
                print(f"❌ Propiedad {prop_id_1} NO se agregó a CU3")
        else:
            print(f"❌ Error creando propiedad CU3-SÍ: {propiedad_cu3_si.get('error')}")

        # Caso 2: Crear propiedad que NO cumple criterios CU3 (capacidad <3)
        print(f"\n🏠 CASO 2: Propiedad que NO cumple CU3 (capacidad=2, WiFi=Sí)")
        print("-" * 50)

        propiedad_cu3_no_cap = await property_service.create_property(
            nombre="Departamento de Prueba - No cumple capacidad",
            descripcion="Depto con capacidad para 2 pero con WiFi",
            capacidad=2,  # <3 ❌
            ciudad_id=1,  # Buenos Aires
            anfitrion_id=1,
            tipo_propiedad_id=1,
            servicios=[1],  # WiFi ✅
            amenities=[1],
            reglas=[1],
            generar_calendario=False
        )

        if propiedad_cu3_no_cap.get("success"):
            prop_id_2 = propiedad_cu3_no_cap["property_id"]
            print(f"✅ Propiedad creada: ID {prop_id_2}")
            
            # Verificar que NO se agregó a CU3
            await asyncio.sleep(0.5)
            docs_cu3_no_cap = await find_documents("properties_by_city_wifi_capacity", {"propiedad_id": prop_id_2})
            if not docs_cu3_no_cap:
                print(f"🎯 ✅ Propiedad {prop_id_2} NO agregada a CU3 (correcto, capacidad <3)")
            else:
                print(f"❌ Propiedad {prop_id_2} se agregó incorrectamente a CU3")
        else:
            print(f"❌ Error creando propiedad NO-CU3: {propiedad_cu3_no_cap.get('error')}")

        # Caso 3: Crear propiedad que NO cumple criterios CU3 (sin WiFi)
        print(f"\n🏠 CASO 3: Propiedad que NO cumple CU3 (capacidad=5, WiFi=No)")
        print("-" * 50)

        propiedad_cu3_no_wifi = await property_service.create_property(
            nombre="Casa de Prueba - Sin WiFi",
            descripcion="Casa grande pero sin WiFi",
            capacidad=5,  # ≥3 ✅
            ciudad_id=1,  # Buenos Aires
            anfitrion_id=1,
            tipo_propiedad_id=1,
            servicios=[2, 3],  # Sin WiFi (id=1) ❌
            amenities=[1],
            reglas=[1],
            generar_calendario=False
        )

        if propiedad_cu3_no_wifi.get("success"):
            prop_id_3 = propiedad_cu3_no_wifi["property_id"]
            print(f"✅ Propiedad creada: ID {prop_id_3}")
            
            # Verificar que NO se agregó a CU3
            await asyncio.sleep(0.5)
            docs_cu3_no_wifi = await find_documents("properties_by_city_wifi_capacity", {"propiedad_id": prop_id_3})
            if not docs_cu3_no_wifi:
                print(f"🎯 ✅ Propiedad {prop_id_3} NO agregada a CU3 (correcto, sin WiFi)")
            else:
                print(f"❌ Propiedad {prop_id_3} se agregó incorrectamente a CU3")
        else:
            print(f"❌ Error creando propiedad NO-CU3-WiFi: {propiedad_cu3_no_wifi.get('error')}")

        # Verificar estado final
        print(f"\n📊 RESUMEN FINAL:")
        print("-" * 30)
        docs_final = await find_documents("properties_by_city_wifi_capacity", {}, limit=100)
        propiedades_nuevas = len(docs_final) - len(docs_antes)
        print(f"   Propiedades en CU3 antes: {len(docs_antes)}")
        print(f"   Propiedades en CU3 después: {len(docs_final)}")
        print(f"   Nuevas propiedades agregadas: {propiedades_nuevas}")
        print(f"   Esperado: 1 (solo la que cumple criterios)")

        if propiedades_nuevas == 1:
            print("🎉 ✅ SINCRONIZACIÓN AUTOMÁTICA CU3 FUNCIONANDO CORRECTAMENTE")
        else:
            print("❌ ⚠️  SINCRONIZACIÓN AUTOMÁTICA CU3 TIENE PROBLEMAS")

        print("\n" + "="*70)

    except Exception as e:
        print(f"❌ Error en prueba de sincronización automática: {str(e)}")
        logger.error("Error en prueba sincronización", error=str(e))


if __name__ == "__main__":
    asyncio.run(test_cu3_auto_sync())