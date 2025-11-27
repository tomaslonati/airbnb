#!/usr/bin/env python3
"""
Script para backfill de la tabla tasa_ocupacion_ciudad_fecha.
Migra datos históricos desde ocupacion_por_ciudad y calcula la tasa de ocupación.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from db.cassandra import (
    get_astra_client,
    find_documents,
    get_collection
)
from utils.logging import configure_logging, get_logger
from config import db_config

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def backfill_tasa_ocupacion():
    """
    Migra datos desde ocupacion_por_ciudad a tasa_ocupacion_ciudad_fecha.
    Lee todos los documentos existentes y crea documentos con tasa pre-calculada.
    """
    try:
        print("\n🔄 BACKFILL: Migrando datos a tasa_ocupacion_ciudad_fecha")
        print("=" * 80)

        # Conectar a AstraDB
        print("\n🔌 Conectando a AstraDB...")
        await get_astra_client()

        # Obtener colecciones
        source_collection = await get_collection("ocupacion_por_ciudad")
        target_collection = await get_collection("tasa_ocupacion_ciudad_fecha")

        print("✅ Conectado a AstraDB")

        # Leer todos los documentos de la tabla fuente
        print("\n📊 Leyendo datos de ocupacion_por_ciudad...")
        # Usar find con límite alto para obtener todos los documentos
        source_docs = await find_documents("ocupacion_por_ciudad", {}, limit=10000)

        print(f"📋 Encontrados {len(source_docs)} documentos en ocupacion_por_ciudad")

        if not source_docs:
            print("⚠️  No hay datos para migrar")
            return

        # Agrupar por ciudad y fecha para procesar
        print("\n🔄 Procesando y transformando datos...")

        migrated_count = 0
        errors_count = 0
        batch_docs = []

        for doc in source_docs:
            try:
                ciudad_id = doc.get('ciudad_id')
                fecha = doc.get('fecha')
                noches_ocupadas = doc.get('noches_ocupadas', 0)
                noches_disponibles = doc.get('noches_disponibles', 0)

                # Calcular total y tasa
                total_propiedades = noches_ocupadas + noches_disponibles

                if total_propiedades > 0:
                    tasa_ocupacion = round((noches_ocupadas / total_propiedades) * 100, 2)
                else:
                    tasa_ocupacion = 0.0

                # Crear nuevo documento para la tabla target
                new_doc = {
                    "ciudad_id": ciudad_id,
                    "fecha": fecha,
                    "total_propiedades": total_propiedades,
                    "propiedades_ocupadas": noches_ocupadas,
                    "propiedades_disponibles": noches_disponibles,
                    "tasa_ocupacion": tasa_ocupacion,
                    "updated_at": datetime.utcnow().isoformat()
                }

                batch_docs.append(new_doc)
                migrated_count += 1

                # Mostrar progreso cada 100 documentos
                if migrated_count % 100 == 0:
                    print(f"   ✓ Procesados {migrated_count} documentos...")

            except Exception as e:
                errors_count += 1
                logger.error(f"Error procesando documento: {e}")
                continue

        # Insertar en lotes
        if batch_docs:
            print(f"\n💾 Insertando {len(batch_docs)} documentos en tasa_ocupacion_ciudad_fecha...")

            # Insertar en lotes de 100
            batch_size = 100
            for i in range(0, len(batch_docs), batch_size):
                batch = batch_docs[i:i + batch_size]
                try:
                    # Insertar cada documento individualmente con upsert
                    for doc_to_insert in batch:
                        filter_doc = {
                            "ciudad_id": doc_to_insert["ciudad_id"],
                            "fecha": doc_to_insert["fecha"]
                        }
                        target_collection.update_one(
                            filter_doc,
                            {"$set": doc_to_insert},
                            upsert=True
                        )

                    print(f"   ✓ Insertado lote {i // batch_size + 1} ({len(batch)} documentos)")

                except Exception as e:
                    logger.error(f"Error insertando lote: {e}")
                    errors_count += len(batch)

        # Resumen
        print("\n" + "=" * 80)
        print("✅ BACKFILL COMPLETADO")
        print("=" * 80)
        print(f"📊 Documentos procesados: {migrated_count}")
        print(f"✅ Documentos migrados exitosamente: {migrated_count - errors_count}")
        print(f"❌ Errores: {errors_count}")
        print()

        # Verificación
        print("🔍 Verificando migración...")
        target_docs = await find_documents("tasa_ocupacion_ciudad_fecha", {}, limit=10)
        print(f"📋 Documentos en tasa_ocupacion_ciudad_fecha: {len(target_docs)}")

        if target_docs:
            print("\n📄 Ejemplo de documento migrado:")
            print(target_docs[0])

        print("\n🎉 ¡Migración completada exitosamente!")

    except Exception as e:
        print(f"\n❌ Error en backfill: {str(e)}")
        logger.error(f"Error en backfill: {e}")
        raise


async def verify_backfill():
    """Verifica que el backfill se haya completado correctamente."""
    try:
        print("\n🔍 VERIFICACIÓN: Comparando datos entre tablas")
        print("=" * 80)

        await get_astra_client()

        # Contar documentos en ambas tablas
        source_docs = await find_documents("ocupacion_por_ciudad", {}, limit=10000)
        target_docs = await find_documents("tasa_ocupacion_ciudad_fecha", {}, limit=10000)

        print(f"\n📊 Documentos en ocupacion_por_ciudad: {len(source_docs)}")
        print(f"📊 Documentos en tasa_ocupacion_ciudad_fecha: {len(target_docs)}")

        if len(source_docs) == len(target_docs):
            print("\n✅ ¡Verificación exitosa! Ambas tablas tienen el mismo número de documentos.")
        else:
            print(f"\n⚠️  Advertencia: Diferencia de {abs(len(source_docs) - len(target_docs))} documentos")

        # Mostrar algunos ejemplos
        if target_docs:
            print("\n📄 Ejemplos de documentos migrados:")
            for i, doc in enumerate(target_docs[:3], 1):
                print(f"\n   Ejemplo {i}:")
                print(f"      Ciudad ID: {doc.get('ciudad_id')}")
                print(f"      Fecha: {doc.get('fecha')}")
                print(f"      Total propiedades: {doc.get('total_propiedades')}")
                print(f"      Tasa de ocupación: {doc.get('tasa_ocupacion')}%")

    except Exception as e:
        print(f"\n❌ Error en verificación: {str(e)}")
        logger.error(f"Error en verificación: {e}")


async def main():
    """Función principal del script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Backfill de datos históricos para tasa_ocupacion_ciudad_fecha'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Solo verifica el backfill sin ejecutar la migración'
    )

    args = parser.parse_args()

    if args.verify_only:
        await verify_backfill()
    else:
        await backfill_tasa_ocupacion()
        print("\n" + "=" * 80)
        await verify_backfill()


if __name__ == "__main__":
    print("🚀 Iniciando script de backfill para tasa_ocupacion_ciudad_fecha...")
    asyncio.run(main())
