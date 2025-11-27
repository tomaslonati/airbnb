#!/usr/bin/env python3
"""
Demo del CU1: Tasa de ocupación por ciudad usando solo Cassandra.
Soporta dos modos:
  1. Rango de fechas (modo original)
  2. Fecha específica (modo nuevo con tabla pre-calculada)
"""

from utils.logging import configure_logging, get_logger
from db.cassandra import get_astra_client, find_documents, get_occupancy_rate_by_date
import asyncio
from datetime import datetime
import sys
from pathlib import Path
import argparse

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))


# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def demo_cu1_single_date(ciudad_id: int = 1, fecha: str = "2025-01-01"):
    """
    Demo del CU1 (Modo Single Date): Consulta de ocupación para una fecha específica.
    Usa la tabla pre-calculada tasa_ocupacion_ciudad_fecha.
    """
    try:
        print("\n🏙️ DEMO: CU1 - TASA DE OCUPACIÓN (FECHA ESPECÍFICA)")
        print("=" * 80)

        await get_astra_client()

        print(f"🔍 CONSULTA:")
        print(f"   🏙️ Ciudad ID: {ciudad_id} (Buenos Aires)")
        print(f"   📅 Fecha: {fecha}")
        print(f"   🗄️ Fuente: tasa_ocupacion_ciudad_fecha (tabla pre-calculada)")
        print(f"   ⚡ Complejidad: O(1) - Lookup directo por clave")

        print(f"\n⏱️  EJECUTANDO CONSULTA CASSANDRA...")
        inicio = datetime.now()

        # ========== CONSULTA DIRECTA ==========
        result = await get_occupancy_rate_by_date(ciudad_id, fecha)

        fin = datetime.now()
        tiempo_consulta = (fin - inicio).total_seconds()

        print(f"⚡ Consulta ejecutada en: {tiempo_consulta:.3f} segundos")

        if result and result.get('total_propiedades', 0) > 0:
            print(f"\n📊 RESULTADO DIRECTO (SIN AGREGACIÓN):")
            print("="*50)
            print(f"🏙️ Ciudad: Buenos Aires (ID: {ciudad_id})")
            print(f"📅 Fecha: {fecha}")
            print(f"🏠 Total propiedades: {result.get('total_propiedades', 0)}")
            print(f"🏠 Propiedades ocupadas: {result.get('propiedades_ocupadas', 0)}")
            print(f"🏠 Propiedades disponibles: {result.get('propiedades_disponibles', 0)}")
            print(f"📈 TASA DE OCUPACIÓN: {result.get('tasa_ocupacion', 0):.2f}%")
            print(f"⏰ Última actualización: {result.get('updated_at', 'N/A')}")
            print(f"⚡ Tiempo de consulta: {tiempo_consulta:.3f}s")

            # Análisis del resultado
            tasa = result.get('tasa_ocupacion', 0)
            print(f"\n💡 ANÁLISIS:")
            if tasa == 100:
                print("   🔥 ¡Ocupación TOTAL! Todas las propiedades están reservadas")
            elif tasa >= 80:
                print("   📈 Ocupación MUY ALTA - Excelente demanda")
            elif tasa >= 50:
                print("   📊 Ocupación MODERADA - Demanda regular")
            else:
                print("   📉 Ocupación BAJA - Oportunidad de mejora")

        else:
            print(f"\n📭 No se encontraron datos para:")
            print(f"   🏙️ Ciudad {ciudad_id}")
            print(f"   📅 Fecha {fecha}")

        print(f"\n🎯 VENTAJAS DEL MODO SINGLE DATE:")
        print(f"   ✅ Consulta O(1) - Lookup directo por clave primaria")
        print(f"   ✅ Sin agregación en memoria (pre-calculado)")
        print(f"   ✅ Datos siempre actualizados en tiempo real")
        print(f"   ✅ Performance ultra-rápida (sub-milisegundos)")
        print(f"   ✅ Ideal para dashboards y consultas frecuentes")

        print("\n" + "="*80)

    except Exception as e:
        print(f"❌ Error en demo CU1 (single date): {str(e)}")
        logger.error("Error en demo CU1 (single date)", error=str(e))


async def demo_cu1_date_range(ciudad_id: int = 1, fecha_inicio: str = "2025-01-01", fecha_fin: str = "2025-01-05"):
    """
    Demo del CU1 (Modo Range): Consulta de ocupación para un rango de fechas.
    Usa la tabla ocupacion_por_ciudad y agrega en memoria.
    """
    try:
        print("\n🏙️ DEMO: CU1 - TASA DE OCUPACIÓN (RANGO DE FECHAS)")
        print("=" * 80)

        await get_astra_client()

        print(f"🔍 CONSULTA:")
        print(f"   🏙️ Ciudad ID: {ciudad_id} (Buenos Aires)")
        print(f"   📅 Rango: {fecha_inicio} a {fecha_fin}")
        print(f"   🗄️ Fuente: ocupacion_por_ciudad (agregación en memoria)")

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
    parser = argparse.ArgumentParser(description='Demo CU1: Tasa de ocupación por ciudad')
    parser.add_argument('--mode', type=str, choices=['single', 'range', 'both'], default='both',
                        help='Modo de consulta: single (fecha específica), range (rango de fechas), both (ambos)')
    parser.add_argument('--ciudad', type=int, default=1, help='ID de la ciudad')
    parser.add_argument('--fecha', type=str, default='2025-01-01', help='Fecha específica (modo single)')
    parser.add_argument('--fecha-inicio', type=str, default='2025-01-01', help='Fecha inicio (modo range)')
    parser.add_argument('--fecha-fin', type=str, default='2025-01-05', help='Fecha fin (modo range)')

    args = parser.parse_args()

    async def run_demos():
        if args.mode == 'single':
            await demo_cu1_single_date(args.ciudad, args.fecha)
        elif args.mode == 'range':
            await demo_cu1_date_range(args.ciudad, args.fecha_inicio, args.fecha_fin)
        else:  # both
            await demo_cu1_single_date(args.ciudad, args.fecha)
            await demo_cu1_date_range(args.ciudad, args.fecha_inicio, args.fecha_fin)

    asyncio.run(run_demos())
