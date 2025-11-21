#!/usr/bin/env python3
"""
Script para analizar la estructura actual de Cassandra y determinar si necesitamos reestructurar.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from db.cassandra import get_astra_client, find_documents
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def analizar_estructura_cassandra():
    """Analizar la estructura actual de Cassandra para el CU3."""
    try:
        print("\n🔍 ANALIZANDO ESTRUCTURA ACTUAL DE CASSANDRA")
        print("=" * 70)

        # Conectar a Cassandra
        database = await get_astra_client()
        
        # Listar todas las colecciones
        collections = database.list_collection_names()
        print(f"📊 Colecciones disponibles: {collections}")
        
        print("\n🏠 ANÁLISIS PARA CU3: Propiedades por ciudad con capacidad ≥3 y WiFi")
        print("-" * 70)
        
        # Analizar la colección actual
        print("\n1️⃣ ESTRUCTURA ACTUAL 'propiedades_disponibles_por_fecha':")
        docs = await find_documents("propiedades_disponibles_por_fecha", {}, limit=3)
        
        if docs:
            print(f"   📄 Ejemplo de documento:")
            for key, value in docs[0].items():
                if key != '_id':
                    print(f"     {key}: {value} ({type(value).__name__})")
        
        print(f"\n   ❌ LIMITACIONES ACTUALES:")
        print(f"     • Solo tiene IDs de propiedades, no los detalles")
        print(f"     • No incluye capacidad, WiFi, precios")
        print(f"     • Requiere consulta adicional a PostgreSQL")
        print(f"     • No es eficiente para búsquedas por criterios")

        print(f"\n2️⃣ PROPUESTA DE NUEVA ESTRUCTURA:")
        print(f"   🎯 COLECCIÓN 'propiedades_por_ciudad_filtros':")
        
        nueva_estructura = {
            "ciudad_id": 1,
            "ciudad_nombre": "Buenos Aires",
            "propiedades": [
                {
                    "propiedad_id": 29,
                    "nombre": "Departamento Palermo",
                    "capacidad": 4,
                    "wifi": True,
                    "precio_noche": 75.0,
                    "servicios": ["Wifi", "Aire acondicionado"],
                    "disponible": True
                },
                {
                    "propiedad_id": 30,
                    "nombre": "Casa San Telmo",
                    "capacidad": 6,
                    "wifi": True,
                    "precio_noche": 95.0,
                    "servicios": ["Wifi", "Cocina"],
                    "disponible": True
                }
            ],
            "total_propiedades": 2,
            "actualizado_en": "2025-11-21T04:40:00Z"
        }
        
        print(f"   📄 Estructura propuesta:")
        for key, value in nueva_estructura.items():
            if key == "propiedades":
                print(f"     {key}: [")
                print(f"       {{")
                for sub_key, sub_value in value[0].items():
                    print(f"         {sub_key}: {sub_value}")
                print(f"       }}, ...")
                print(f"     ]")
            else:
                print(f"     {key}: {value}")

        print(f"\n   ✅ VENTAJAS DE LA NUEVA ESTRUCTURA:")
        print(f"     • Consulta simple: filter por ciudad_id")
        print(f"     • Filtro en memoria: capacidad ≥ 3 y wifi = true")
        print(f"     • Sin consultas adicionales a PostgreSQL")
        print(f"     • Respuesta inmediata")
        print(f"     • Datos desnormalizados optimizados para lectura")

        print(f"\n3️⃣ CONSULTA CU3 CON NUEVA ESTRUCTURA:")
        print(f"   🔍 Filtro Cassandra: {{\"ciudad_id\": ciudad_id}}")
        print(f"   🔍 Filtro aplicación:")
        print(f"     prop.capacidad >= 3 AND prop.wifi == true")

        print(f"\n4️⃣ ¿NECESITAMOS REESTRUCTURAR?")
        print(f"   🎯 SÍ - Para cumplir requisitos del CU3:")
        print(f"     • CU3 debe ser una consulta Cassandra simple")
        print(f"     • No debe depender de PostgreSQL")
        print(f"     • Debe filtrar por ciudad + criterios")
        
        print("\n" + "="*70)
        print("💡 CONCLUSIÓN: Necesitamos crear la nueva colección")
        print("   'propiedades_por_ciudad_filtros' para CU3 óptimo")

    except Exception as e:
        print(f"❌ Error analizando estructura: {str(e)}")
        logger.error("Error analizando estructura", error=str(e))


if __name__ == "__main__":
    asyncio.run(analizar_estructura_cassandra())