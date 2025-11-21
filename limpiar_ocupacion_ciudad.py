"""
Script para limpiar y recrear datos de ocupación por ciudad.
Implementa el diseño correcto: una fila por (ciudad_id, fecha) con noches agregadas.
"""

import asyncio
from datetime import datetime, date, timedelta
from db.cassandra import get_collection, find_documents, delete_collection_data
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def limpiar_y_recrear_ocupacion():
    """Limpia y recrea ocupación por ciudad desde datos de disponibilidad existentes."""
    try:
        logger.info("🧹 Limpiando ocupacion_por_ciudad...")

        # Eliminar todos los datos existentes
        await delete_collection_data("ocupacion_por_ciudad")

        logger.info(
            "🔄 Recreando ocupacion_por_ciudad desde propiedades_disponibles_por_fecha...")

        # Obtener todos los documentos de disponibilidad
        disponibilidad_docs = await find_documents(
            "propiedades_disponibles_por_fecha",
            {},
            limit=1000
        )

        logger.info(
            f"📊 Procesando {len(disponibilidad_docs)} documentos de disponibilidad...")

        # Agrupar por (ciudad_id, fecha) y contar noches disponibles
        ocupacion_agregada = {}

        for doc in disponibilidad_docs:
            fecha = doc.get('fecha')
            propiedades_disponibles = doc.get('propiedades_disponibles', [])
            ciudad_ids = doc.get('ciudad_ids', [])

            if not fecha or not propiedades_disponibles or not ciudad_ids:
                continue

            # Para cada ciudad en este documento
            for ciudad_id in ciudad_ids:
                key = (ciudad_id, fecha)

                if key not in ocupacion_agregada:
                    ocupacion_agregada[key] = {
                        'noches_disponibles': 0,
                        'noches_ocupadas': 0
                    }

                # Cada propiedad disponible = 1 noche disponible
                ocupacion_agregada[key]['noches_disponibles'] += len(
                    propiedades_disponibles)

        # Insertar documentos agregados en ocupacion_por_ciudad
        collection = await get_collection("ocupacion_por_ciudad")
        documentos_creados = 0

        for (ciudad_id, fecha), datos in ocupacion_agregada.items():
            try:
                new_doc = {
                    "ciudad_id": ciudad_id,
                    "fecha": fecha,
                    "noches_ocupadas": datos['noches_ocupadas'],
                    "noches_disponibles": datos['noches_disponibles']
                }

                collection.insert_one(new_doc)
                documentos_creados += 1

            except Exception as e:
                logger.error(f"Error insertando {ciudad_id}, {fecha}: {e}")
                continue

        logger.info(
            f"✅ Recreados {documentos_creados} documentos en ocupacion_por_ciudad")

        # Mostrar algunos resultados para verificar
        sample_docs = await find_documents("ocupacion_por_ciudad", {}, limit=5)

        logger.info("📋 Muestra de documentos recreados:")
        for doc in sample_docs:
            logger.info(f"  Ciudad {doc.get('ciudad_id')}, Fecha {doc.get('fecha')}: "
                        f"{doc.get('noches_ocupadas', 0)} ocupadas, "
                        f"{doc.get('noches_disponibles', 0)} disponibles")

    except Exception as e:
        logger.error(f"Error en la recreación: {e}")
        raise


async def main():
    """Función principal para ejecutar la limpieza y recreación."""
    try:
        logger.info(
            "🚀 Iniciando limpieza y recreación de ocupación por ciudad...")

        await limpiar_y_recrear_ocupacion()

        logger.info("🎉 Limpieza y recreación completadas exitosamente!")

    except Exception as e:
        logger.error(f"Error en el proceso: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
