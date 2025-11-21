"""
Script de prueba para verificar búsqueda de propiedades usando Supabase.
"""
import asyncio
from services.search import SearchService

async def test_search():
    """Prueba la búsqueda de propiedades desde Supabase."""
    search_service = SearchService()

    print("\n🔍 PROBANDO BÚSQUEDA DE PROPIEDADES DESDE SUPABASE")
    print("=" * 70)

    # Test 1: Búsqueda simple por ciudad
    print("\n📍 Test 1: Búsqueda en Buenos Aires (sin filtros)")
    result1 = await search_service.search_properties(ciudad="Buenos Aires")

    if result1.get("success"):
        print(f"   ✅ Éxito: {result1['count']} propiedades encontradas")
        print(f"   📊 Cached: {result1.get('cached', False)}")

        if result1['count'] > 0:
            print(f"\n   Primeras 5 propiedades:")
            for i, prop in enumerate(result1['properties'][:5], 1):
                print(f"   {i}. ID: {prop.get('propiedad_id')} | "
                      f"Nombre: {prop.get('propiedad_nombre', 'N/A')[:30]} | "
                      f"Capacidad: {prop.get('capacidad_huespedes')} | "
                      f"Precio: ${prop.get('precio_noche', 0):.2f}")
    else:
        print(f"   ❌ Error: {result1.get('error')}")
        return

    # Test 2: Misma búsqueda para verificar cache
    print("\n📍 Test 2: Misma búsqueda (debería venir de cache)")
    result2 = await search_service.search_properties(ciudad="Buenos Aires")

    if result2.get("success"):
        print(f"   ✅ Éxito: {result2['count']} propiedades encontradas")
        print(f"   📊 Cached: {result2.get('cached', False)}")
        if result2.get('cached'):
            print("   🎉 ¡CACHE HIT! Datos servidos desde Redis")
        else:
            print("   ⚠️  No se usó cache (puede ser normal en primera ejecución)")
    else:
        print(f"   ❌ Error: {result2.get('error')}")

    # Test 3: Búsqueda con filtros
    print("\n📍 Test 3: Buenos Aires con filtros (capacidad >= 4, precio <= 150)")
    result3 = await search_service.search_properties(
        ciudad="Buenos Aires",
        capacidad_minima=4,
        precio_maximo=150
    )

    if result3.get("success"):
        print(f"   ✅ Éxito: {result3['count']} propiedades encontradas")
        print(f"   📊 Cached: {result3.get('cached', False)}")

        if result3['count'] > 0:
            print(f"\n   Propiedades filtradas:")
            for i, prop in enumerate(result3['properties'][:5], 1):
                print(f"   {i}. Nombre: {prop.get('propiedad_nombre', 'N/A')[:30]} | "
                      f"Capacidad: {prop.get('capacidad_huespedes')} | "
                      f"Precio: ${prop.get('precio_noche', 0):.2f}")
    else:
        print(f"   ❌ Error: {result3.get('error')}")

    print("\n" + "=" * 70)
    print("✅ Test completado\n")

if __name__ == "__main__":
    asyncio.run(test_search())
