#!/usr/bin/env python3
"""
Script para verificar todas las tablas disponibles en PostgreSQL.
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


async def verificar_tablas_postgresql():
    """Verificar todas las tablas disponibles en PostgreSQL."""
    try:
        print("\n🔍 VERIFICANDO TODAS LAS TABLAS POSTGRESQL")
        print("=" * 60)

        # Listar todas las tablas
        print("📊 Tablas disponibles:")
        query_tables = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """

        tables = await execute_query(query_tables)

        if tables:
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print("❌ No se encontraron tablas")

        # Verificar datos de ejemplo de propiedad
        print("\n📄 Datos de ejemplo de la tabla 'propiedad':")
        query_example = """
            SELECT p.*, c.nombre as ciudad_nombre 
            FROM propiedad p
            JOIN ciudad c ON p.ciudad_id = c.id
            LIMIT 3;
        """

        examples = await execute_query(query_example)

        if examples:
            for i, ex in enumerate(examples, 1):
                print(f"\n  🏠 Propiedad {i}:")
                for key, value in ex.items():
                    if key != 'imagenes':  # Skip array field for readability
                        print(f"    {key}: {value}")
        else:
            print("❌ No se encontraron propiedades")

        print("\n" + "="*60)

    except Exception as e:
        print(f"❌ Error verificando tablas: {str(e)}")
        logger.error("Error verificando tablas", error=str(e))


if __name__ == "__main__":
    asyncio.run(verificar_tablas_postgresql())
