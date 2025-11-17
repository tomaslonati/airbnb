#!/usr/bin/env python3
"""
Script para diagnosticar y arreglar problemas con la secuencia de la tabla resenia
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from db.postgres import execute_query
import structlog

logger = structlog.get_logger(__name__)


async def diagnose_and_fix_sequence():
    """Diagnostica y arregla problemas con la secuencia resenia_id_seq"""

    print("🔍 Diagnosticando tabla resenia...")

    # 1. Verificar datos actuales
    count_query = """
        SELECT COUNT(*) as count, 
               COALESCE(MAX(id), 0) as max_id,
               COALESCE(MIN(id), 0) as min_id
        FROM resenia
    """
    current_data = await execute_query(count_query)

    print(f"📊 Datos actuales:")
    print(f"   Total registros: {current_data[0]['count']}")
    print(f"   ID máximo: {current_data[0]['max_id']}")
    print(f"   ID mínimo: {current_data[0]['min_id']}")

    # 2. Verificar estado de la secuencia
    seq_query = "SELECT last_value, is_called FROM resenia_id_seq"
    seq_status = await execute_query(seq_query)

    print(f"🔢 Estado de secuencia:")
    print(f"   Último valor: {seq_status[0]['last_value']}")
    print(f"   Is called: {seq_status[0]['is_called']}")

    # 3. Verificar si hay conflicto
    max_id = current_data[0]['max_id']
    last_value = seq_status[0]['last_value']

    if last_value <= max_id:
        print("⚠️ ¡PROBLEMA DETECTADO! La secuencia está desactualizada")
        print(f"   Secuencia en: {last_value}")
        print(f"   MAX ID real: {max_id}")

        # Calcular nuevo valor para la secuencia
        new_value = max_id + 1
        print(f"🔧 Ajustando secuencia a: {new_value}")

        # Arreglar la secuencia
        fix_query = f"SELECT setval('resenia_id_seq', {new_value}, false)"
        await execute_query(fix_query)

        # Verificar que se arregló
        new_seq_status = await execute_query(seq_query)
        print(
            f"✅ Secuencia ajustada. Nuevo valor: {new_seq_status[0]['last_value']}")

    else:
        print("✅ La secuencia está correcta")

    # 4. Mostrar registros existentes
    existing_query = """
        SELECT r.id, r.reserva_id, r.huesped_id, r.anfitrion_id, r.puntaje, r.comentario
        FROM resenia r
        ORDER BY r.id
    """
    existing = await execute_query(existing_query)

    print(f"\n📋 Reseñas existentes ({len(existing)}):")
    for review in existing:
        print(f"   ID {review['id']}: Reserva {review['reserva_id']} | "
              f"Huésped {review['huesped_id']} → Anfitrión {review['anfitrion_id']} | "
              f"★{review['puntaje']} | {review['comentario'] or '(sin comentario)'}")


async def test_insert():
    """Prueba insertar una reseña de prueba"""
    print("\n🧪 Probando INSERT...")

    try:
        # Intentar insertar una reseña de prueba (debe fallar si no hay reservas válidas)
        test_query = """
            INSERT INTO resenia (reserva_id, huesped_id, anfitrion_id, puntaje, comentario)
            VALUES (999, 999, 999, 5, 'Test - se puede borrar')
            RETURNING id
        """

        result = await execute_query(test_query)

        if result:
            new_id = result[0]['id']
            print(f"✅ INSERT exitoso. Nuevo ID generado: {new_id}")

            # Limpiar test
            cleanup_query = "DELETE FROM resenia WHERE id = $1"
            await execute_query(cleanup_query, new_id)
            print(f"🧹 Registro de prueba eliminado")
        else:
            print("❌ INSERT falló sin excepción")

    except Exception as e:
        print(f"❌ Error en INSERT de prueba: {str(e)}")


async def main():
    """Función principal"""
    print("🏥 DIAGNÓSTICO Y REPARACIÓN - Tabla resenia")
    print("=" * 60)

    await diagnose_and_fix_sequence()
    await test_insert()

    print("\n✅ Diagnóstico completado")
    print("💡 Ahora puedes intentar crear reseñas nuevamente")

if __name__ == "__main__":
    asyncio.run(main())

