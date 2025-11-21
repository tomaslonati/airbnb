#!/usr/bin/env python3
"""
Script para verificar datos disponibles en PostgreSQL para el CU3.
"""

from utils.logging import configure_logging, get_logger
from db.postgres import execute_query
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))


# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def verificar_datos_cu3():
    """
    Verificar qué datos tenemos para el CU3.
    """
    try:
        print("\n🔍 VERIFICANDO DATOS DISPONIBLES PARA CU3")
        print("=" * 60)

        # 1. Verificar ciudades disponibles
        print("\n1. 🌆 CIUDADES DISPONIBLES:")
        ciudades_query = "SELECT id, nombre FROM ciudad ORDER BY id LIMIT 10"
        ciudades = await execute_query(ciudades_query)
        if ciudades:
            for ciudad in ciudades:
                print(f"   ID: {ciudad['id']} - {ciudad['nombre']}")
        else:
            print("   ❌ No hay ciudades en la base de datos")

        # 2. Verificar propiedades por ciudad
        print("\n2. 🏠 PROPIEDADES POR CIUDAD:")
        propiedades_query = """
            SELECT c.nombre as ciudad, COUNT(p.id) as cantidad
            FROM ciudad c
            LEFT JOIN propiedad p ON c.id = p.ciudad_id
            GROUP BY c.id, c.nombre
            ORDER BY cantidad DESC
            LIMIT 10
        """
        prop_stats = await execute_query(propiedades_query)
        if prop_stats:
            for stat in prop_stats:
                print(f"   {stat['ciudad']}: {stat['cantidad']} propiedades")

        # 3. Verificar servicios disponibles
        print("\n3. 📶 SERVICIOS DISPONIBLES:")
        servicios_query = "SELECT id, descripcion FROM servicios ORDER BY id"
        servicios = await execute_query(servicios_query)
        if servicios:
            wifi_found = False
            for servicio in servicios:
                print(f"   ID: {servicio['id']} - {servicio['descripcion']}")
                if 'wifi' in servicio['descripcion'].lower() or 'internet' in servicio['descripcion'].lower():
                    wifi_found = True
            if not wifi_found:
                print("\n   ⚠️ No se encontraron servicios de WiFi/Internet")
        else:
            print("   ❌ No hay servicios en la base de datos")

        # 4. Verificar propiedades con servicios
        print("\n4. 🔗 PROPIEDADES CON SERVICIOS:")
        prop_serv_query = """
            SELECT COUNT(*) as total_relaciones,
                   COUNT(DISTINCT propiedad_id) as propiedades_con_servicios
            FROM propiedad_servicio
        """
        prop_serv = await execute_query(prop_serv_query)
        if prop_serv:
            print(
                f"   Total relaciones propiedad-servicio: {prop_serv[0]['total_relaciones']}")
            print(
                f"   Propiedades con servicios: {prop_serv[0]['propiedades_con_servicios']}")

        # 5. Verificar disponibilidad y precios
        print("\n5. 💰 DISPONIBILIDAD Y PRECIOS:")
        disp_query = """
            SELECT COUNT(*) as total_registros,
                   COUNT(DISTINCT propiedad_id) as propiedades_con_precios,
                   AVG(price_per_night) as precio_promedio
            FROM propiedad_disponibilidad
            WHERE disponible = true
        """
        disp_stats = await execute_query(disp_query)
        if disp_stats:
            stats = disp_stats[0]
            print(
                f"   Registros de disponibilidad: {stats['total_registros']}")
            print(
                f"   Propiedades con precios: {stats['propiedades_con_precios']}")
            print(
                f"   Precio promedio: ${float(stats['precio_promedio'] or 0):.2f}")

        # 6. Ejemplo de propiedades con capacidad ≥ 3 en cada ciudad
        print("\n6. 📊 PROPIEDADES CON CAPACIDAD ≥ 3 POR CIUDAD:")
        capacity_query = """
            SELECT c.nombre as ciudad, c.id as ciudad_id, COUNT(p.id) as propiedades_cap_3_plus
            FROM ciudad c
            LEFT JOIN propiedad p ON c.id = p.ciudad_id AND p.capacidad >= 3
            GROUP BY c.id, c.nombre
            HAVING COUNT(p.id) > 0
            ORDER BY propiedades_cap_3_plus DESC
        """
        cap_stats = await execute_query(capacity_query)
        if cap_stats:
            for stat in cap_stats:
                print(
                    f"   {stat['ciudad']} (ID: {stat['ciudad_id']}): {stat['propiedades_cap_3_plus']} propiedades")

        print("\n" + "="*60)
        print("✅ Verificación completada")

    except Exception as e:
        print(f"❌ Error verificando datos: {str(e)}")
        logger.error("Error verificando datos", error=str(e))


async def main():
    """Función principal."""
    print("🚀 Iniciando verificación de datos...")
    await verificar_datos_cu3()


if __name__ == "__main__":
    asyncio.run(main())
