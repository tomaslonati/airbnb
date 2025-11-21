#!/usr/bin/env python3
"""
Script para verificar y poblar la colección properties_by_city_wifi_capacity.
"""

from utils.logging import configure_logging, get_logger
from db.postgres import execute_query
from db.cassandra import get_astra_client, find_documents, insert_document, create_collection
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))


# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def verificar_y_poblar_coleccion_cu3():
    """Verificar y poblar la colección optimizada para CU3."""
    try:
        print("\n🔍 VERIFICANDO COLECCIÓN EXISTENTE PARA CU3")
        print("=" * 70)

        # Verificar si la colección properties_by_city_wifi_capacity tiene datos
        print("📊 Verificando 'properties_by_city_wifi_capacity'...")
        docs = await find_documents("properties_by_city_wifi_capacity", {}, limit=5)

        if docs:
            print(
                f"✅ Colección existe con {len(docs)} documentos. Estructura:")
            for i, doc in enumerate(docs[:2], 1):
                print(f"\n📄 Documento {i}:")
                for key, value in doc.items():
                    if key != '_id':
                        print(f"   {key}: {value}")
        else:
            print("❌ Colección vacía. Poblando con datos de PostgreSQL...")
            await poblar_coleccion_cu3()

    except Exception as e:
        print(f"❌ Error verificando colección: {str(e)}")
        logger.error("Error verificando colección", error=str(e))


async def poblar_coleccion_cu3():
    """Poblar la colección con datos optimizados para CU3."""
    try:
        print("\n🏗️ POBLANDO COLECCIÓN PARA CU3")
        print("-" * 50)

        # Obtener datos de PostgreSQL
        query = """
            SELECT 
                c.id as ciudad_id,
                c.nombre as ciudad_nombre,
                p.id as propiedad_id,
                p.nombre as propiedad_nombre,
                p.capacidad,
                CASE 
                    WHEN ps.servicio_id = 1 THEN true 
                    ELSE false 
                END as wifi,
                COALESCE(pd.price_per_night, 50.0) as precio_noche
            FROM ciudad c
            JOIN propiedad p ON p.ciudad_id = c.id
            LEFT JOIN propiedad_servicio ps ON ps.propiedad_id = p.id AND ps.servicio_id = 1
            LEFT JOIN propiedad_disponibilidad pd ON pd.propiedad_id = p.id
            ORDER BY c.id, p.id;
        """

        rows = await execute_query(query)

        if not rows:
            print("❌ No se encontraron datos en PostgreSQL")
            return

        # Agrupar por ciudad
        ciudades = {}
        for row in rows:
            ciudad_id = row['ciudad_id']
            if ciudad_id not in ciudades:
                ciudades[ciudad_id] = {
                    'ciudad_id': ciudad_id,
                    'ciudad_nombre': row['ciudad_nombre'],
                    'propiedades': [],
                    'total_propiedades': 0,
                    'con_wifi': 0,
                    'capacidad_3_o_mas': 0
                }

            propiedad = {
                'propiedad_id': row['propiedad_id'],
                'nombre': row['propiedad_nombre'],
                'capacidad': row['capacidad'],
                'wifi': bool(row['wifi']),
                'precio_noche': float(row['precio_noche']) if row['precio_noche'] else 50.0
            }

            ciudades[ciudad_id]['propiedades'].append(propiedad)
            ciudades[ciudad_id]['total_propiedades'] += 1

            if propiedad['wifi']:
                ciudades[ciudad_id]['con_wifi'] += 1
            if propiedad['capacidad'] >= 3:
                ciudades[ciudad_id]['capacidad_3_o_mas'] += 1

        # Insertar en Cassandra
        for ciudad_data in ciudades.values():
            print(
                f"📥 Insertando ciudad: {ciudad_data['ciudad_nombre']} ({ciudad_data['total_propiedades']} props)")
            await insert_document("properties_by_city_wifi_capacity", ciudad_data)

        print(f"\n✅ Colección poblada con {len(ciudades)} ciudades")

        # Verificar datos insertados
        print(f"\n🔍 Verificando datos insertados...")
        docs = await find_documents("properties_by_city_wifi_capacity", {}, limit=3)

        for doc in docs:
            ciudad_nombre = doc.get('ciudad_nombre')
            total = doc.get('total_propiedades', 0)
            wifi = doc.get('con_wifi', 0)
            cap3 = doc.get('capacidad_3_o_mas', 0)
            print(
                f"   🏙️ {ciudad_nombre}: {total} props, {wifi} con WiFi, {cap3} con capacidad ≥3")

    except Exception as e:
        print(f"❌ Error poblando colección: {str(e)}")
        logger.error("Error poblando colección", error=str(e))


if __name__ == "__main__":
    asyncio.run(verificar_y_poblar_coleccion_cu3())
