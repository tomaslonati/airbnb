#!/usr/bin/env python3
"""
Demo del CU1: Tasa de ocupación por ciudad usando solo Cassandra.
"""

from utils.logging import configure_logging, get_logger
from db.cassandra import get_astra_client, find_documents
import asyncio
from datetime import datetime
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))


# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def demo_cu1_ocupacion():
    """Demo del CU1: Consulta de ocupación usando solo Cassandra."""
    try:
        print("\n🏙️ DEMO: CU1 - TASA DE OCUPACIÓN POR CIUDAD (SOLO CASSANDRA)")
        print("=" * 80)

        await get_astra_client()

        # Parámetros de ejemplo
        ciudad_id = 1
        fecha_inicio = "2025-01-01"
        fecha_fin = "2025-01-05"

        print(f"🔍 CONSULTA:")
        print(f"   🏙️ Ciudad ID: {ciudad_id} (Buenos Aires)")
        print(f"   📅 Rango: {fecha_inicio} a {fecha_fin}")
        print(f"   🗄️ Fuente: Solo Cassandra (ocupacion_por_ciudad)")

        print(f"\n⏱️  EJECUTANDO CONSULTA CASSANDRA...")
        inicio = datetime.now()

        # ========== PASO 1: CONSULTA FILTRADA ==========
        filter_doc = {
            "ciudad_id": ciudad_id,
            "fecha": {"$gte": fecha_inicio, "$lte": fecha_fin}
        }

        print(f"📋 Filtro aplicado: {filter_doc}")

        results = await find_documents("ocupacion_por_ciudad", filter_doc, limit=100)

        fin = datetime.now()
        tiempo_consulta = (fin - inicio).total_seconds()

        print(f"⚡ Consulta ejecutada en: {tiempo_consulta:.3f} segundos")
        print(f"📊 Documentos encontrados: {len(results)}")

        if results:
            print(f"\n📋 DATOS RAW DE CASSANDRA:")
            print("-" * 50)
            for i, doc in enumerate(results, 1):
                print(f"   {i}. {doc}")

            # ========== PASO 2: AGREGACIÓN EN MEMORIA ==========
            print(f"\n🧮 AGREGACIÓN EN MEMORIA:")
            print("-" * 30)

            total_noches_ocupadas = 0
            total_noches_disponibles = 0
            dias_con_datos = len(results)

            print(f"📊 Procesando {dias_con_datos} documentos...")

            for i, data in enumerate(results, 1):
                ocupadas = data.get('noches_ocupadas', 0)
                disponibles = data.get('noches_disponibles', 0)

                total_noches_ocupadas += ocupadas
                total_noches_disponibles += disponibles

                print(
                    f"   Día {i}: +{ocupadas} ocupadas, +{disponibles} disponibles")

            total_noches = total_noches_ocupadas + total_noches_disponibles

            print(f"\n📊 TOTALES AGREGADOS:")
            print(f"   🏠 Total noches ocupadas: {total_noches_ocupadas}")
            print(f"   🏠 Total noches disponibles: {total_noches_disponibles}")
            print(f"   🏠 Total noches: {total_noches}")

            # ========== PASO 3: CÁLCULO DE TASA ==========
            if total_noches > 0:
                tasa_ocupacion = (total_noches_ocupadas / total_noches) * 100

                print(f"\n📈 CÁLCULO DE TASA DE OCUPACIÓN:")
                print(f"   Formula: (noches_ocupadas / total_noches) × 100")
                print(
                    f"   Cálculo: ({total_noches_ocupadas} / {total_noches}) × 100")
                print(f"   Resultado: {tasa_ocupacion:.2f}%")

                print(f"\n✅ RESULTADO FINAL:")
                print("="*50)
                print(f"🏙️ Ciudad: Buenos Aires (ID: {ciudad_id})")
                print(f"📅 Período: {fecha_inicio} a {fecha_fin}")
                print(f"📊 Días con datos: {dias_con_datos}")
                print(f"🏠 Noches ocupadas: {total_noches_ocupadas}")
                print(f"🏠 Noches disponibles: {total_noches_disponibles}")
                print(f"📈 TASA DE OCUPACIÓN: {tasa_ocupacion:.2f}%")
                print(f"⚡ Tiempo de consulta: {tiempo_consulta:.3f}s")

                # Análisis del resultado
                print(f"\n💡 ANÁLISIS:")
                if tasa_ocupacion == 100:
                    print("   🔥 ¡Ocupación TOTAL! Todas las noches están reservadas")
                elif tasa_ocupacion >= 80:
                    print("   📈 Ocupación MUY ALTA - Excelente demanda")
                elif tasa_ocupacion >= 50:
                    print("   📊 Ocupación MODERADA - Demanda regular")
                else:
                    print("   📉 Ocupación BAJA - Oportunidad de mejora")

            else:
                print(
                    f"\n⚠️ No hay datos de capacidad para ciudad {ciudad_id}")
        else:
            print(f"\n📭 No se encontraron datos para:")
            print(f"   🏙️ Ciudad {ciudad_id}")
            print(f"   📅 Rango {fecha_inicio} - {fecha_fin}")

        print(f"\n🎯 VENTAJAS DE USAR SOLO CASSANDRA:")
        print(f"   ✅ 1 sola consulta (sin JOINs complejos)")
        print(f"   ✅ Filtrado nativo por ciudad y fechas")
        print(f"   ✅ Datos pre-agregados listos para calcular")
        print(f"   ✅ Performance sub-segundo")
        print(f"   ✅ Escalabilidad automática")

        print("\n" + "="*80)

    except Exception as e:
        print(f"❌ Error en demo CU1: {str(e)}")
        logger.error("Error en demo CU1", error=str(e))


if __name__ == "__main__":
    asyncio.run(demo_cu1_ocupacion())
