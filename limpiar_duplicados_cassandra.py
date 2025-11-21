#!/usr/bin/env python3
"""
Script para limpiar documentos duplicados en propiedades_disponibles_por_fecha.
Consolida propiedades de documentos duplicados para la misma fecha.
"""

import asyncio
from collections import defaultdict
from db.cassandra import get_astra_client, find_documents, get_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def limpiar_duplicados():
    """Limpia documentos duplicados consolidando propiedades por fecha."""
    try:
        print("🧹 LIMPIANDO DUPLICADOS EN PROPIEDADES_DISPONIBLES_POR_FECHA")
        print("="*70)
        
        await get_astra_client()
        collection = await get_collection("propiedades_disponibles_por_fecha")
        
        # Obtener todos los documentos
        docs = await find_documents("propiedades_disponibles_por_fecha", {}, limit=1000)
        print(f"📊 Total documentos encontrados: {len(docs)}")
        
        # Agrupar por fecha
        documentos_por_fecha = defaultdict(list)
        for doc in docs:
            fecha = doc.get('fecha')
            documentos_por_fecha[fecha].append(doc)
        
        # Encontrar fechas con duplicados
        fechas_duplicadas = {fecha: docs for fecha, docs in documentos_por_fecha.items() if len(docs) > 1}
        
        print(f"🔍 Fechas con duplicados: {len(fechas_duplicadas)}")
        
        for fecha, docs_fecha in fechas_duplicadas.items():
            print(f"\n📅 Procesando fecha: {fecha}")
            print(f"   Documentos duplicados: {len(docs_fecha)}")
            
            # Consolidar propiedades y ciudades
            todas_propiedades = set()
            todas_ciudades = set()
            
            for doc in docs_fecha:
                propiedades = doc.get('propiedades_disponibles', [])
                ciudades = doc.get('ciudad_ids', [])
                todas_propiedades.update(propiedades)
                todas_ciudades.update(ciudades)
                
                # Eliminar este documento duplicado
                collection.delete_one({"_id": doc["_id"]})
            
            # Crear un nuevo documento consolidado
            doc_consolidado = {
                "fecha": fecha,
                "propiedades_disponibles": sorted(list(todas_propiedades)),
                "ciudad_ids": sorted(list(todas_ciudades))
            }
            
            collection.insert_one(doc_consolidado)
            
            print(f"   ✅ Consolidado: {len(todas_propiedades)} propiedades, {len(todas_ciudades)} ciudades")
            print(f"   Propiedades: {sorted(list(todas_propiedades))}")
        
        print(f"\n🎉 Limpieza completada. {len(fechas_duplicadas)} fechas procesadas")
        
        # Verificar resultado
        docs_final = await find_documents("propiedades_disponibles_por_fecha", {}, limit=1000)
        print(f"📊 Total documentos después de limpieza: {len(docs_final)}")
        
    except Exception as e:
        logger.error(f"Error limpiando duplicados: {e}")

if __name__ == "__main__":
    asyncio.run(limpiar_duplicados())