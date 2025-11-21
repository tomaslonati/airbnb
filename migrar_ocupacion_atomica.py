"""
Script para migrar a la nueva lógica de ocupacion_por_ciudad.
Elimina la tabla actual y crea la nueva con lógica de UPDATE atómico.
"""

import asyncio
from datetime import datetime, date, timedelta
from db.cassandra import get_collection, find_documents, delete_collection_data
from utils.logging import get_logger

logger = get_logger(__name__)


async def migrar_ocupacion_ciudad():
    """Migra a la nueva lógica de ocupacion_por_ciudad con UPDATEs atómicos."""
    try:
        logger.info("🧹 Eliminando tabla ocupacion_por_ciudad actual...")

        # Paso 1: Eliminar todos los datos existentes
        await delete_collection_data("ocupacion_por_ciudad")

        logger.info("🔄 La nueva tabla se poblará automáticamente cuando:")
        logger.info("  • Se creen nuevas propiedades (disponibilidad inicial)")
        logger.info("  • Se confirmen reservas (ocupación)")
        logger.info("  • Se cancelen reservas (liberación)")

        logger.info(
            "✅ Migración completada - tabla lista para lógica de UPDATE")

    except Exception as e:
        logger.error(f"Error en la migración: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrar_ocupacion_ciudad())
