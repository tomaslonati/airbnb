#!/usr/bin/env python3
"""
Script para verificar qué datos existen en la colección de propiedades.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from db.cassandra import find_documents, get_astra_client
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def verificar_datos():
    """Verificar qué datos existen en la colección."""
    try:
        print("\n🔍 VERIFICANDO DATOS EN CASSANDRA")
        print("=" * 50)

        # Conectar a Cassandra
        await get_astra_client()

        # Obtener una muestra de documentos de la colección
        print("📊 Obteniendo una muestra de datos de 'propiedades_disponibles_por_fecha'...")
        documents = await find_documents("propiedades_disponibles_por_fecha", {}, limit=20)

        if documents:
            print(f"✅ Encontrados {len(documents)} documentos. Mostrando estructura:")
            print("-" * 50)

            for i, doc in enumerate(documents[:5], 1):  # Mostrar solo los primeros 5
                print(f"\n📄 Documento {i}:")
                for key, value in doc.items():
                    if key != '_id':  # Omitir el _id
                        print(f"  {key}: {value}")
                
                # Verificar campos específicos que necesitamos
                ciudad_id = doc.get('ciudad_id')
                capacidad = doc.get('capacidad_huespedes')
                wifi = doc.get('wifi')
                
                print(f"  ➤ Ciudad ID: {ciudad_id} (tipo: {type(ciudad_id)})")
                print(f"  ➤ Capacidad: {capacidad} (tipo: {type(capacidad)})")
                print(f"  ➤ WiFi: {wifi} (tipo: {type(wifi)})")
                
        else:
            print("❌ No se encontraron documentos en la colección")

        print("\n" + "="*50)

        # Verificar también si hay documentos con ciudad específica
        print("🔍 Probando búsqueda por ciudades específicas...")
        
        for ciudad_id in ['1', '2', 1, 2]:
            filter_doc = {"ciudad_id": ciudad_id}
            docs = await find_documents("propiedades_disponibles_por_fecha", filter_doc, limit=5)
            print(f"Ciudad {ciudad_id} ({type(ciudad_id).__name__}): {len(docs)} documentos")

    except Exception as e:
        print(f"❌ Error verificando datos: {str(e)}")
        logger.error("Error verificando datos", error=str(e))


if __name__ == "__main__":
    asyncio.run(verificar_datos())