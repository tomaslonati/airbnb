#!/usr/bin/env python3
"""
Script para validar que el CU3 encuentra las propiedades recién creadas.
"""

from utils.logging import configure_logging, get_logger
from services.reservations import ReservationService
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))


# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def test_cu3_encuentra_nuevas_propiedades():
    """Probar que CU3 encuentra las propiedades recién agregadas."""
    try:
        print("\n🔍 PRUEBA: CU3 ENCUENTRA PROPIEDADES NUEVAS")
        print("=" * 60)

        # Inicializar servicio
        reservation_service = ReservationService()

        # Probar CU3 con Buenos Aires (ciudad_id=1)
        print("🏙️  Buscando propiedades en Buenos Aires (ciudad_id=1)")
        print("   Criterios: capacidad ≥3 y WiFi")
        print("-" * 45)

        resultado_cu3 = await reservation_service.get_propiedades_ciudad_capacidad_wifi(ciudad_id=1)

        if resultado_cu3.get("success"):
            propiedades_cu3 = resultado_cu3.get("propiedades", [])
            total = resultado_cu3.get("total", 0)

            print(f"📊 Encontradas {total} propiedades:")

            for i, propiedad in enumerate(propiedades_cu3, 1):
                print(f"   {i}. ID: {propiedad.get('propiedad_id')}")
                print(f"      Nombre: {propiedad.get('propiedad_nombre')}")
                print(
                    f"      Capacidad: {propiedad.get('capacidad_huespedes')}")
                print(f"      WiFi: {propiedad.get('wifi')}")
                print(f"      Ciudad: {propiedad.get('ciudad_nombre')}")

                # Verificar que cumple criterios
                capacidad = propiedad.get('capacidad_huespedes', 0)
                tiene_wifi = propiedad.get('wifi', False)

                if capacidad >= 3 and tiene_wifi:
                    print(f"      ✅ Cumple criterios CU3")
                else:
                    print(
                        f"      ❌ NO cumple criterios CU3 (cap:{capacidad}, wifi:{tiene_wifi})")
                print()

            # Verificar que se incluye la propiedad recién creada (ID 49)
            ids_encontrados = [p.get('propiedad_id') for p in propiedades_cu3]
            if 49 in ids_encontrados:
                print(
                    "🎯 ✅ La propiedad recién creada (ID 49) aparece en los resultados CU3")
            else:
                print(
                    "❌ La propiedad recién creada (ID 49) NO aparece en los resultados CU3")
                print(f"   IDs encontrados: {ids_encontrados}")

        else:
            print(f"❌ Error en CU3: {resultado_cu3.get('error')}")

        print("\n" + "="*60)

    except Exception as e:
        print(f"❌ Error en prueba CU3: {str(e)}")
        logger.error("Error en prueba CU3", error=str(e))


if __name__ == "__main__":
    asyncio.run(test_cu3_encuentra_nuevas_propiedades())
