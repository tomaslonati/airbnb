"""
Test de optimización de Neo4j con quick check y timeouts rápidos.
"""

import asyncio
import time
from db import neo4j
from utils.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("test_neo4j_optimization")


async def test_neo4j_optimized():
    """Test de las optimizaciones de Neo4j"""

    print("🚀 TESTING OPTIMIZACIONES DE NEO4J")
    print("=" * 50)

    # Test 1: Quick check (solo DNS)
    print("\n🔍 Test 1: Quick Check (DNS only)")
    start_time = time.time()
    quick_result = neo4j.quick_check()
    quick_time = time.time() - start_time

    print(f"   ⏱️ Quick check: {quick_time:.3f}s")
    print(f"   📊 Resultado: {'✅ DNS OK' if quick_result else '❌ DNS Fail'}")

    # Test 2: is_available (conexión real con timeout)
    print("\n🔗 Test 2: Full Connection Check")
    start_time = time.time()
    try:
        available = neo4j.is_available()
        full_time = time.time() - start_time
        print(f"   ⏱️ Full check: {full_time:.3f}s")
        print(
            f"   📊 Resultado: {'✅ Disponible' if available else '❌ No disponible'}")
    except Exception as e:
        full_time = time.time() - start_time
        print(f"   ⏱️ Full check: {full_time:.3f}s")
        print(f"   ❌ Error: {e}")

    # Test 3: Comparación de tiempos
    print(f"\n📈 COMPARACIÓN:")
    print(f"   🚀 Quick check: {quick_time:.3f}s")
    print(f"   🐌 Full check: {full_time:.3f}s")
    if quick_time > 0:
        mejora = (full_time / quick_time)
        print(f"   📊 Mejora de velocidad: {mejora:.1f}x más rápido")

    # Test 4: Simulador de reserva rápida
    print(f"\n📅 Test 4: Reserva con optimización")
    start_time = time.time()

    try:
        from services.reservations import ReservationService
        service = ReservationService()

        # Simular quick check en reserva
        if neo4j.quick_check():
            print("   🔗 Neo4j disponible por quick check, intentando conexión real...")
        else:
            print("   ⚡ Quick check falló, usando simulador inmediatamente")

        reservation_time = time.time() - start_time
        print(f"   ⏱️ Tiempo total simulación: {reservation_time:.3f}s")

    except Exception as e:
        print(f"   ❌ Error en test de reserva: {e}")

    print("\n" + "=" * 50)
    print("✅ Test de optimizaciones completado")
    print("🎯 Objetivo: Reducir timeouts de ~40s a ~2-3s")

if __name__ == "__main__":
    asyncio.run(test_neo4j_optimized())
