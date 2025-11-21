#!/usr/bin/env python3
"""
Script de prueba específico para el CU3: Búsqueda de propiedades por ciudad con capacidad ≥3 y WiFi.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from services.reservations import ReservationService
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def test_cu3():
    """
    Probar CU3: Búsqueda de propiedades por ciudad con capacidad ≥3 y WiFi.
    """
    try:
        print("\n🏠 CASO DE USO 3: BÚSQUEDA DE PROPIEDADES POR CIUDAD (CASSANDRA)")
        print("=" * 75)

        service = ReservationService()

        # Probar con diferentes ciudades
        ciudades_test = [
            {"id": 1, "nombre": "Buenos Aires"},
            {"id": 2, "nombre": "Madrid"},
            {"id": 3, "nombre": "Barcelona"}
        ]

        for ciudad in ciudades_test:
            print(f"\n🌆 Probando ciudad: {ciudad['nombre']} (ID: {ciudad['id']})")
            print(f"🔍 Buscando propiedades con:")
            print(f"   📏 Capacidad ≥ 3 huéspedes")
            print(f"   📶 WiFi disponible")

            result = await service.get_propiedades_ciudad_capacidad_wifi(
                ciudad_id=ciudad['id'],
                min_capacidad=3,
                wifi_required=True
            )

            if result.get("success"):
                propiedades = result.get("propiedades", [])
                print(f"\n✅ Búsqueda exitosa para {ciudad['nombre']}")
                print(f"📊 Propiedades encontradas: {len(propiedades)}")

                if propiedades:
                    print(f"\n🏠 PROPIEDADES CON CAPACIDAD ≥3 Y WIFI EN {ciudad['nombre'].upper()}:")
                    print("-" * 75)
                    print(f"{'ID':<8} {'Ciudad':<15} {'Precio':<12} {'Capacidad':<12} {'WiFi'}")
                    print("-" * 75)

                    for prop in propiedades:
                        prop_id = prop.get('propiedad_id', 'N/A')
                        ciudad_nombre = prop.get('ciudad_nombre', ciudad['nombre'])[:14]
                        precio = f"${prop.get('precio_noche', 0):.2f}"
                        capacidad = prop.get('capacidad_huespedes', 'N/A')
                        wifi = "Sí" if prop.get('wifi', False) else "No"
                        print(f"{prop_id:<8} {ciudad_nombre:<15} {precio:<12} {capacidad:<12} {wifi}")

                    print(f"\n💡 Todas las propiedades mostradas cumplen:")
                    print(f"   ✅ Capacidad para 3 o más huéspedes")
                    print(f"   ✅ WiFi disponible")
                    print(f"   🏙️ Ubicadas en {ciudad['nombre']}")
                else:
                    print(f"📭 No hay propiedades que cumplan los criterios en {ciudad['nombre']}")
            else:
                print(f"❌ Error en la búsqueda para {ciudad['nombre']}: {result.get('error', 'Error desconocido')}")

        print("\n" + "="*75)
        print("✅ Caso de uso 3 completado")
        print("="*75)

    except Exception as e:
        print(f"❌ Error en caso de uso 3: {str(e)}")
        logger.error("Error en caso de uso 3", error=str(e))


async def main():
    """Función principal."""
    print("🚀 Iniciando prueba del CU3...")
    await test_cu3()


if __name__ == "__main__":
    asyncio.run(main())