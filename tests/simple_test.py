"""
Prueba simple de conexión a AstraDB.
"""

import asyncio
import os
from astrapy import DataAPIClient

# Obtener credenciales desde variables de entorno
ASTRA_DB_TOKEN = os.getenv("ASTRA_DB_TOKEN", "")
ASTRA_DB_ENDPOINT = os.getenv("ASTRA_DB_ENDPOINT", "")

if not ASTRA_DB_TOKEN or not ASTRA_DB_ENDPOINT:
    print("❌ Error: ASTRA_DB_TOKEN y ASTRA_DB_ENDPOINT deben estar configurados")
    print("💡 Tip: Crea un archivo .env con tus credenciales o configura las variables de entorno")
    print("   export ASTRA_DB_TOKEN='tu_token_aqui'")
    print("   export ASTRA_DB_ENDPOINT='tu_endpoint_aqui'")
    exit(1)


async def test_connection():
    """Prueba simple de conexión a AstraDB."""
    try:
        print("🚀 Conectando a AstraDB...")
        
        # Crear cliente
        client = DataAPIClient(ASTRA_DB_TOKEN)
        db = client.get_database_by_api_endpoint(ASTRA_DB_ENDPOINT)
        
        # Verificar conexión
        collections = db.list_collection_names()
        print(f"✅ ¡Conexión exitosa!")
        print(f"📋 Colecciones existentes: {collections}")
        
        # Crear una colección de prueba
        collection_name = "airbnb_test"
        
        try:
            collection = db.create_collection(collection_name)
            print(f"✅ Colección '{collection_name}' creada")
        except Exception as e:
            if "already exists" in str(e).lower():
                collection = db.get_collection(collection_name)
                print(f"ℹ️  Colección '{collection_name}' ya existe")
            else:
                print(f"❌ Error: {e}")
                return
        
        # Insertar un documento
        test_doc = {
            "property_id": "test_property_001",
            "timestamp": "2024-11-14T10:30:00Z",
            "event": "view",
            "user_id": "user_123",
            "location": "Barcelona"
        }
        
        result = collection.insert_one(test_doc)
        print(f"✅ Documento insertado con ID: {result.inserted_id}")
        
        # Buscar documentos
        docs = list(collection.find({"event": "view"}, limit=5))
        print(f"📄 Documentos encontrados: {len(docs)}")
        
        for doc in docs:
            print(f"   - {doc.get('property_id')} | {doc.get('event')} | {doc.get('location')}")
        
        print("\n🎉 ¡Prueba completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🌟 PRUEBA SIMPLE DE ASTRADB")
    print("=" * 60)
    
    asyncio.run(test_connection())