#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla propiedad en PostgreSQL.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from db.postgres import execute_query
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def verificar_estructura_postgresql():
    """Verificar la estructura de las tablas en PostgreSQL."""
    try:
        print("\n🔍 VERIFICANDO ESTRUCTURA DE TABLAS POSTGRESQL")
        print("=" * 60)

        # Verificar estructura de la tabla propiedad
        print("📊 Estructura de la tabla 'propiedad':")
        query_propiedad = """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'propiedad' 
            ORDER BY ordinal_position;
        """
        
        columns = await execute_query(query_propiedad)
        
        if columns:
            print("-" * 60)
            print(f"{'Columna':<20} {'Tipo':<20} {'Nullable':<10}")
            print("-" * 60)
            for col in columns:
                print(f"{col['column_name']:<20} {col['data_type']:<20} {col['is_nullable']:<10}")
        else:
            print("❌ No se encontraron columnas para la tabla 'propiedad'")

        print("\n📊 Estructura de la tabla 'ciudad':")
        query_ciudad = """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'ciudad' 
            ORDER BY ordinal_position;
        """
        
        columns = await execute_query(query_ciudad)
        
        if columns:
            print("-" * 60)
            print(f"{'Columna':<20} {'Tipo':<20} {'Nullable':<10}")
            print("-" * 60)
            for col in columns:
                print(f"{col['column_name']:<20} {col['data_type']:<20} {col['is_nullable']:<10}")
        else:
            print("❌ No se encontraron columnas para la tabla 'ciudad'")

        # Verificar algunos datos de ejemplo
        print("\n📄 Datos de ejemplo de propiedades con capacidad ≥ 3:")
        query_example = """
            SELECT p.id, p.capacidad_huespedes, p.wifi, c.nombre as ciudad_nombre 
            FROM propiedad p
            JOIN ciudad c ON p.ciudad_id = c.id
            WHERE p.capacidad_huespedes >= 3
            LIMIT 5;
        """
        
        examples = await execute_query(query_example)
        
        if examples:
            print("-" * 60)
            print(f"{'ID':<5} {'Capacidad':<10} {'WiFi':<6} {'Ciudad':<20}")
            print("-" * 60)
            for ex in examples:
                wifi_str = "Sí" if ex['wifi'] else "No"
                print(f"{ex['id']:<5} {ex['capacidad_huespedes']:<10} {wifi_str:<6} {ex['ciudad_nombre']:<20}")
        else:
            print("❌ No se encontraron propiedades con capacidad ≥ 3")

        print("\n" + "="*60)

    except Exception as e:
        print(f"❌ Error verificando estructura: {str(e)}")
        logger.error("Error verificando estructura", error=str(e))


if __name__ == "__main__":
    asyncio.run(verificar_estructura_postgresql())