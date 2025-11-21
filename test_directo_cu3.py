#!/usr/bin/env python3
"""
Test directo de la función de Cassandra para CU3.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from db.cassandra import get_propiedades_ciudad_capacidad_wifi
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def test_directo():
    """
    Test directo de la función.
    """
    try:
        print("\n🔍 TEST DIRECTO DE LA FUNCIÓN CU3")
        print("=" * 50)

        # Test con Buenos Aires
        print("\n🌆 Probando Buenos Aires (ID: 1)")
        propiedades = await get_propiedades_ciudad_capacidad_wifi(
            ciudad_id=1,
            min_capacidad=3,
            wifi_required=True
        )
        
        print(f"📊 Resultado: {len(propiedades)} propiedades encontradas")
        
        if propiedades:
            print("\n🏠 PROPIEDADES ENCONTRADAS:")
            for prop in propiedades:
                print(f"   ID: {prop['propiedad_id']} - {prop['propiedad_nombre']}")
                print(f"      Capacidad: {prop['capacidad_huespedes']}, WiFi: {prop['wifi']}")
                print(f"      Precio: ${prop['precio_noche']:.2f}")

        # Test sin filtro de WiFi
        print("\n🌆 Probando Buenos Aires SIN filtro de WiFi")
        propiedades_sin_wifi = await get_propiedades_ciudad_capacidad_wifi(
            ciudad_id=1,
            min_capacidad=3,
            wifi_required=False
        )
        
        print(f"📊 Resultado: {len(propiedades_sin_wifi)} propiedades encontradas")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error("Error en test directo", error=str(e))


async def main():
    """Función principal."""
    print("🚀 Iniciando test directo...")
    await test_directo()


if __name__ == "__main__":
    asyncio.run(main())