"""
Script para ver datos de la tabla ocupacion_por_ciudad en Astra DB
"""

import asyncio
from db.cassandra import find_documents
import json


async def ver_tabla_ocupacion():
    """Ver contenido de la tabla ocupacion_por_ciudad."""
    try:
        print("🔍 Consultando tabla 'ocupacion_por_ciudad' en Astra DB...")

        # Obtener todos los documentos
        docs = await find_documents('ocupacion_por_ciudad', {}, limit=1000)

        print(f"\n📊 Total de documentos encontrados: {len(docs)}")

        if docs:
            print("\n📋 Primeros 10 documentos:")
            print("=" * 80)

            for i, doc in enumerate(docs[:10], 1):
                print(f"{i:2d}. Ciudad: {doc.get('ciudad_id', 'N/A'):>3} | "
                      f"Fecha: {doc.get('fecha', 'N/A')} | "
                      f"Ocupadas: {doc.get('noches_ocupadas', 0):>2} | "
                      f"Disponibles: {doc.get('noches_disponibles', 0):>2}")

            if len(docs) > 10:
                print(f"    ... y {len(docs) - 10} documentos más")

            # Agrupar por ciudad para estadísticas
            print("\n📈 Estadísticas por ciudad:")
            print("=" * 50)

            ciudades = {}
            for doc in docs:
                ciudad_id = doc.get('ciudad_id')
                if ciudad_id:
                    if ciudad_id not in ciudades:
                        ciudades[ciudad_id] = {
                            'fechas': 0,
                            'total_ocupadas': 0,
                            'total_disponibles': 0
                        }
                    ciudades[ciudad_id]['fechas'] += 1
                    ciudades[ciudad_id]['total_ocupadas'] += doc.get(
                        'noches_ocupadas', 0)
                    ciudades[ciudad_id]['total_disponibles'] += doc.get(
                        'noches_disponibles', 0)

            for ciudad_id, stats in sorted(ciudades.items()):
                total_noches = stats['total_ocupadas'] + \
                    stats['total_disponibles']
                tasa = (stats['total_ocupadas'] / total_noches *
                        100) if total_noches > 0 else 0
                print(f"Ciudad {ciudad_id:>2}: {stats['fechas']:>3} fechas | "
                      f"Ocupadas: {stats['total_ocupadas']:>4} | "
                      f"Disponibles: {stats['total_disponibles']:>4} | "
                      f"Tasa: {tasa:>6.2f}%")

        else:
            print("⚠️ No se encontraron documentos en la tabla")

    except Exception as e:
        print(f"❌ Error consultando tabla: {e}")

if __name__ == "__main__":
    asyncio.run(ver_tabla_ocupacion())
