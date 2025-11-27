#!/usr/bin/env python3
"""
Script de prueba para la nueva funcionalidad CU1 (single date).
Verifica que la tabla tasa_ocupacion_ciudad_fecha funcione correctamente.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from db.cassandra import (
    get_astra_client,
    get_occupancy_rate_by_date,
    _update_tasa_ocupacion_ciudad,
    find_documents
)
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def test_insert_and_query():
    """Prueba de inserción y consulta de tasa de ocupación."""
    try:
        print("\n🧪 TEST: Funcionalidad CU1 Single Date")
        print("=" * 80)

        # Conectar a AstraDB
        print("\n1️⃣  Conectando a AstraDB...")
        await get_astra_client()
        print("✅ Conectado exitosamente")

        # Datos de prueba
        ciudad_id = 1
        fecha_test = (datetime.now() + timedelta(days=30)).date()
        fecha_str = fecha_test.isoformat()

        print(f"\n2️⃣  Insertando datos de prueba...")
        print(f"   Ciudad ID: {ciudad_id}")
        print(f"   Fecha: {fecha_str}")

        # Simular inserción de datos (como si se creara una reserva)
        # Inicialmente: 10 propiedades disponibles, 0 ocupadas
        print("\n   📝 Paso 1: Inicializar 10 propiedades disponibles")
        await _update_tasa_ocupacion_ciudad(ciudad_id, fecha_str, occupied_delta=0, available_delta=10)

        # Hacer una reserva (1 propiedad ocupada, 1 menos disponible)
        print("   📝 Paso 2: Marcar 3 propiedades como ocupadas")
        await _update_tasa_ocupacion_ciudad(ciudad_id, fecha_str, occupied_delta=3, available_delta=-3)

        print("✅ Datos insertados correctamente")

        # Esperar un momento para que se sincronice
        await asyncio.sleep(1)

        # Consultar los datos
        print(f"\n3️⃣  Consultando tasa de ocupación...")
        result = await get_occupancy_rate_by_date(ciudad_id, fecha_str)

        if result:
            print("\n✅ RESULTADO DE LA CONSULTA:")
            print("=" * 50)
            print(f"   🏙️  Ciudad ID: {result.get('ciudad_id')}")
            print(f"   📅 Fecha: {result.get('fecha')}")
            print(f"   🏠 Total propiedades: {result.get('total_propiedades')}")
            print(f"   🏠 Propiedades ocupadas: {result.get('propiedades_ocupadas')}")
            print(f"   🏠 Propiedades disponibles: {result.get('propiedades_disponibles')}")
            print(f"   📈 Tasa de ocupación: {result.get('tasa_ocupacion')}%")
            print(f"   ⏰ Última actualización: {result.get('updated_at')}")
            print("=" * 50)

            # Validar resultados
            expected_total = 10
            expected_occupied = 3
            expected_available = 7
            expected_rate = 30.0

            print(f"\n4️⃣  Validando resultados...")
            assert result.get('total_propiedades') == expected_total, \
                f"Total propiedades incorrecto: esperado {expected_total}, obtenido {result.get('total_propiedades')}"
            assert result.get('propiedades_ocupadas') == expected_occupied, \
                f"Propiedades ocupadas incorrecto: esperado {expected_occupied}, obtenido {result.get('propiedades_ocupadas')}"
            assert result.get('propiedades_disponibles') == expected_available, \
                f"Propiedades disponibles incorrecto: esperado {expected_available}, obtenido {result.get('propiedades_disponibles')}"
            assert result.get('tasa_ocupacion') == expected_rate, \
                f"Tasa de ocupación incorrecta: esperado {expected_rate}%, obtenido {result.get('tasa_ocupacion')}%"

            print("✅ Todas las validaciones pasaron correctamente")

        else:
            print("❌ No se encontraron resultados")
            return False

        # Verificar que la colección fue creada
        print(f"\n5️⃣  Verificando que la colección existe...")
        docs = await find_documents("tasa_ocupacion_ciudad_fecha", {"ciudad_id": ciudad_id}, limit=5)
        print(f"✅ Encontrados {len(docs)} documentos en la colección")

        print("\n" + "=" * 80)
        print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
        print("=" * 80)
        print("\n✅ La funcionalidad CU1 Single Date está funcionando correctamente")
        print("✅ La tabla tasa_ocupacion_ciudad_fecha se crea y actualiza correctamente")
        print("✅ Las consultas devuelven resultados precisos")
        print("✅ La tasa de ocupación se calcula correctamente")

        return True

    except AssertionError as e:
        print(f"\n❌ ERROR DE VALIDACIÓN: {str(e)}")
        return False

    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {str(e)}")
        logger.error(f"Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_updates():
    """Prueba múltiples actualizaciones para verificar que la lógica read-compute-write funciona."""
    try:
        print("\n\n🧪 TEST 2: Múltiples Actualizaciones")
        print("=" * 80)

        ciudad_id = 2
        fecha_test = (datetime.now() + timedelta(days=31)).date().isoformat()

        print(f"\n   Ciudad ID: {ciudad_id}")
        print(f"   Fecha: {fecha_test}")

        # Serie de actualizaciones
        print("\n   📝 Simulando múltiples operaciones:")

        print("   1. Inicializar 20 propiedades disponibles")
        await _update_tasa_ocupacion_ciudad(ciudad_id, fecha_test, occupied_delta=0, available_delta=20)

        print("   2. Reservar 5 propiedades")
        await _update_tasa_ocupacion_ciudad(ciudad_id, fecha_test, occupied_delta=5, available_delta=-5)

        print("   3. Reservar 3 propiedades más")
        await _update_tasa_ocupacion_ciudad(ciudad_id, fecha_test, occupied_delta=3, available_delta=-3)

        print("   4. Cancelar 2 reservas")
        await _update_tasa_ocupacion_ciudad(ciudad_id, fecha_test, occupied_delta=-2, available_delta=2)

        await asyncio.sleep(1)

        # Consultar resultado final
        result = await get_occupancy_rate_by_date(ciudad_id, fecha_test)

        print("\n✅ RESULTADO FINAL:")
        print(f"   Total: {result.get('total_propiedades')} propiedades")
        print(f"   Ocupadas: {result.get('propiedades_ocupadas')}")
        print(f"   Disponibles: {result.get('propiedades_disponibles')}")
        print(f"   Tasa: {result.get('tasa_ocupacion')}%")

        # Validar: 20 total, 6 ocupadas (5+3-2), 14 disponibles, 30% ocupación
        assert result.get('total_propiedades') == 20
        assert result.get('propiedades_ocupadas') == 6
        assert result.get('propiedades_disponibles') == 14
        assert result.get('tasa_ocupacion') == 30.0

        print("\n✅ Test de múltiples actualizaciones PASÓ")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Ejecuta todos los tests."""
    print("\n🚀 Iniciando suite de tests para CU1 Single Date")
    print("=" * 80)

    success = True

    # Test 1: Inserción y consulta básica
    if not await test_insert_and_query():
        success = False

    # Test 2: Múltiples actualizaciones
    if not await test_multiple_updates():
        success = False

    # Resumen
    print("\n\n" + "=" * 80)
    if success:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("=" * 80)

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
