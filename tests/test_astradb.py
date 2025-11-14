"""
Script de prueba para verificar la conexión con AstraDB.
"""

import asyncio
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.cassandra import get_astra_client, create_collection, insert_document, find_documents
from utils.logging import get_logger

logger = get_logger(__name__)


async def test_astradb_connection():
    """Prueba la conexión con AstraDB."""
    try:
        print("🚀 Iniciando prueba de conexión con AstraDB...")
        
        # Conectar a AstraDB
        database = await get_astra_client()
        print("✅ Conexión exitosa!")
        
        # Listar colecciones existentes
        collections = database.list_collection_names()
        print(f"📋 Colecciones existentes: {collections}")
        
        # Crear una colección de prueba si no existe
        test_collection = "test_metrics"
        
        try:
            # Intentar crear la colección
            collection = await create_collection(test_collection)
            print(f"✅ Colección '{test_collection}' creada")
        except Exception as e:
            # Si ya existe, obtenerla
            if "already exists" in str(e).lower():
                from db.cassandra import get_collection
                collection = await get_collection(test_collection)
                print(f"ℹ️  Colección '{test_collection}' ya existe")
            else:
                print(f"❌ Error creando colección: {e}")
                return
        
        # Insertar un documento de prueba
        test_document = {
            "property_id": "test_123",
            "timestamp": "2024-11-14T10:00:00Z",
            "views": 100,
            "clicks": 10,
            "conversion_rate": 0.1,
            "test": True
        }
        
        result = await insert_document(test_collection, test_document)
        print(f"✅ Documento insertado: {result.inserted_id}")
        
        # Buscar documentos
        documents = await find_documents(test_collection, {"test": True})
        print(f"📄 Documentos encontrados: {len(documents)}")
        
        for doc in documents[:3]:  # Mostrar solo los primeros 3
            print(f"   - ID: {doc.get('_id')}, Property: {doc.get('property_id')}")
        
        print("\n🎉 ¡Prueba de AstraDB completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()


async def test_astradb_operations():
    """Prueba operaciones CRUD con AstraDB."""
    try:
        print("\n🔄 Probando operaciones CRUD...")
        
        collection_name = "airbnb_metrics"
        
        # Crear la colección principal si no existe
        try:
            await create_collection(collection_name)
            print(f"✅ Colección '{collection_name}' lista")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"ℹ️  Colección '{collection_name}' ya existe")
            else:
                print(f"⚠️  Advertencia: {e}")
        
        # Insertar múltiples documentos de ejemplo
        sample_docs = [
            {
                "property_id": "prop_001",
                "timestamp": "2024-11-14T09:00:00Z",
                "event_type": "view",
                "user_id": "user_123",
                "location": "Barcelona",
                "price": 120.0
            },
            {
                "property_id": "prop_002", 
                "timestamp": "2024-11-14T09:30:00Z",
                "event_type": "booking",
                "user_id": "user_456",
                "location": "Madrid",
                "price": 95.0
            },
            {
                "property_id": "prop_001",
                "timestamp": "2024-11-14T10:00:00Z", 
                "event_type": "favorite",
                "user_id": "user_789",
                "location": "Barcelona",
                "price": 120.0
            }
        ]
        
        for doc in sample_docs:
            result = await insert_document(collection_name, doc)
            print(f"   ✅ Insertado: {doc['property_id']} - {doc['event_type']}")
        
        # Buscar por diferentes filtros
        print("\n🔍 Probando búsquedas...")
        
        # Buscar por ubicación
        barcelona_docs = await find_documents(collection_name, {"location": "Barcelona"})
        print(f"   📍 Documentos en Barcelona: {len(barcelona_docs)}")
        
        # Buscar por tipo de evento
        bookings = await find_documents(collection_name, {"event_type": "booking"})
        print(f"   🏠 Reservas: {len(bookings)}")
        
        # Buscar por property_id
        prop_docs = await find_documents(collection_name, {"property_id": "prop_001"})
        print(f"   🏢 Eventos para prop_001: {len(prop_docs)}")
        
        print("\n✨ ¡Operaciones CRUD completadas exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en operaciones: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🌟 PRUEBA DE CONEXIÓN ASTRADB - AIRBNB BACKEND")
    print("=" * 60)
    
    # Ejecutar pruebas
    asyncio.run(test_astradb_connection())
    asyncio.run(test_astradb_operations())
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas!")
    print("=" * 60)