#!/usr/bin/env python3
"""
Script para probar el mecanismo corregido de eliminación de disponibilidad.
"""

import asyncio
from datetime import datetime, date
from db.cassandra import cassandra_mark_unavailable, get_astra_client, find_documents
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def probar_eliminacion_corregida():
    """Prueba la función corregida de eliminar disponibilidad."""
    try:
        print("🧪 PROBANDO MECANISMO CORREGIDO DE ELIMINACIÓN")
        print("="*60)

        await get_astra_client()

        # Verificar estado ANTES de eliminar
        # Fecha diferente para no interferir con reserva existente
        fecha_prueba = "2025-12-15"
        print(f"📅 Probando con fecha: {fecha_prueba}")

        docs_antes = await find_documents("propiedades_disponibles_por_fecha", {"fecha": fecha_prueba}, limit=10)
        print(f"📊 Documentos ANTES: {len(docs_antes)}")

        propiedades_antes = set()
        for doc in docs_antes:
            props = doc.get("propiedades_disponibles", [])
            propiedades_antes.update(props)

        print(
            f"🏠 Propiedades disponibles ANTES: {sorted(list(propiedades_antes))}")

        if 46 not in propiedades_antes:
            print(
                "❌ La propiedad 46 no está disponible en esta fecha, no se puede probar")
            return

        # Marcar propiedad 46 como no disponible
        print("\\n🔄 Marcando propiedad 46 como NO DISPONIBLE...")
        await cassandra_mark_unavailable(46, [date.fromisoformat(fecha_prueba)], ciudad_id=1)

        # Verificar estado DESPUÉS de eliminar
        docs_despues = await find_documents("propiedades_disponibles_por_fecha", {"fecha": fecha_prueba}, limit=10)
        print(f"📊 Documentos DESPUÉS: {len(docs_despues)}")

        propiedades_despues = set()
        for doc in docs_despues:
            props = doc.get("propiedades_disponibles", [])
            propiedades_despues.update(props)

        print(
            f"🏠 Propiedades disponibles DESPUÉS: {sorted(list(propiedades_despues))}")

        # Verificar si la eliminación funcionó
        if 46 in propiedades_despues:
            print("❌ PROBLEMA: La propiedad 46 todavía aparece como disponible")
        else:
            print("✅ ÉXITO: La propiedad 46 fue eliminada correctamente")

        # Mostrar diferencia
        eliminadas = propiedades_antes - propiedades_despues
        print(f"🗑️ Propiedades eliminadas: {sorted(list(eliminadas))}")

        if eliminadas == {46}:
            print("✅ El mecanismo de eliminación funciona correctamente!")
        else:
            print(
                f"❌ Problema en eliminación. Esperado: {{46}}, Real: {eliminadas}")

    except Exception as e:
        logger.error(f"Error en prueba: {e}")

if __name__ == "__main__":
    asyncio.run(probar_eliminacion_corregida())
