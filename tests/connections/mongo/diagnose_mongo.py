#!/usr/bin/env python3
"""
Script para diagnosticar datos de MongoDB para el caso de uso 2
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from db.mongo import get_collection
import structlog

logger = structlog.get_logger(__name__)


async def diagnose_mongodb():
    """Diagnostica datos de MongoDB para el caso de uso 2"""

    print("🔍 Diagnosticando MongoDB - host_statistics...")

    try:
        collection = get_collection("host_statistics")

        # 1. Contar documentos totales
        total_docs = collection.count_documents({})
        print(f"📊 Total documentos en host_statistics: {total_docs}")

        if total_docs == 0:
            print("❌ No hay documentos en la colección host_statistics")
            print("💡 Necesitas crear algunas reseñas para generar estadísticas")
            return

        # 2. Ver estructura de documentos
        print("\n📋 Primeros documentos (estructura):")
        sample_docs = list(collection.find().limit(3))
        for i, doc in enumerate(sample_docs, 1):
            print(f"\nDocumento {i}:")
            for key, value in doc.items():
                if key != '_id':
                    print(f"  {key}: {value}")

        # 3. Verificar cuántos tienen average_rating
        with_avg_rating = collection.count_documents(
            {"stats.average_rating": {"$exists": True}})
        print(f"\n⭐ Documentos con average_rating: {with_avg_rating}")

        # 4. Verificar cuántos tienen ratings array
        with_ratings = collection.count_documents(
            {"ratings": {"$exists": True, "$ne": []}})
        print(f"📝 Documentos con ratings: {with_ratings}")

        # 5. Ver algunos documentos con datos
        if with_avg_rating > 0:
            print(f"\n✅ Documentos con average_rating:")
            docs_with_avg = list(collection.find(
                {"stats.average_rating": {"$exists": True}},
                {"host_id": 1, "stats": 1, "ratings": 1}
            ).limit(5))

            for doc in docs_with_avg:
                host_id = doc.get('host_id')
                stats = doc.get('stats', {})
                ratings_count = len(doc.get('ratings', []))
                avg_rating = stats.get('average_rating')
                total_reviews = stats.get('total_reviews')

                print(
                    f"  Host {host_id}: avg={avg_rating}, reviews={total_reviews}, ratings={ratings_count}")

        # 6. Si no hay average_rating, intentar calcular desde ratings
        if with_avg_rating == 0 and with_ratings > 0:
            print(f"\n🔧 Intentando calcular promedios desde ratings...")

            pipeline = [
                {"$match": {"ratings": {"$exists": True, "$ne": []}}},
                {"$project": {
                    "host_id": 1,
                    "ratings": 1,
                    "calculated_avg": {"$avg": "$ratings.rating"},
                    "total_ratings": {"$size": "$ratings"}
                }}
            ]

            results = list(collection.aggregate(pipeline))
            print(f"📊 Calculados {len(results)} promedios:")

            for result in results[:5]:  # Mostrar los primeros 5
                host_id = result.get('host_id')
                calc_avg = result.get('calculated_avg', 0)
                total_ratings = result.get('total_ratings', 0)
                print(
                    f"  Host {host_id}: {calc_avg:.2f}/5 ({total_ratings} ratings)")

        # 7. Mostrar un documento completo de ejemplo
        if sample_docs:
            print(f"\n📄 Documento completo de ejemplo:")
            example = sample_docs[0]
            print(f"Host ID: {example.get('host_id')}")
            if 'stats' in example:
                print(f"Stats: {example['stats']}")
            if 'ratings' in example:
                print(
                    f"Ratings ({len(example.get('ratings', []))}): {example['ratings'][:2]}...")

    except Exception as e:
        print(f"❌ Error consultando MongoDB: {str(e)}")
        logger.error("Error diagnosticando MongoDB", error=str(e))


async def main():
    """Función principal"""
    print("🏥 DIAGNÓSTICO MONGODB - Caso de Uso 2")
    print("=" * 60)

    await diagnose_mongodb()

    print("\n✅ Diagnóstico completado")

if __name__ == "__main__":
    asyncio.run(main())

