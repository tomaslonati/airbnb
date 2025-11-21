#!/usr/bin/env python3
"""
Demo del CU4: Propiedades disponibles por fecha usando Cassandra + PostgreSQL.
"""

import asyncio
from datetime import datetime, date
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from services.reservations import ReservationService
from utils.logging import configure_logging, get_logger

# Configurar logging
configure_logging()
logger = get_logger(__name__)


async def demo_cu4_propiedades_disponibles():
    """Demo del CU4: Propiedades disponibles por fecha."""
    try:
        print("\n🏠 DEMO: CU4 - PROPIEDADES DISPONIBLES POR FECHA")
        print("=" * 70)
        
        # Inicializar servicio
        service = ReservationService()
        
        # Fecha de ejemplo (la que tenía datos en Cassandra)
        fecha_demo = date(2025, 12, 12)
        
        print(f"🔍 CONSULTA:")
        print(f"   📅 Fecha: {fecha_demo.isoformat()}")
        print(f"   🗄️ Fuente: Solo Cassandra (propiedades_disponibles_por_fecha)")
        
        print(f"\n⏱️  EJECUTANDO CONSULTA CU4...")
        inicio = datetime.now()
        
        result = await service.get_propiedades_disponibles_fecha(fecha_demo)
        
        fin = datetime.now()
        tiempo_consulta = (fin - inicio).total_seconds()
        
        print(f"⚡ Consulta ejecutada en: {tiempo_consulta:.3f} segundos")
        
        if result.get("success"):
            propiedades = result.get("propiedades", [])
            total = result.get("total", 0)
            
            print(f"📊 Propiedades encontradas: {total}")
            
            if propiedades:
                print(f"\n📋 DETALLES DE PROPIEDADES DISPONIBLES:")
                print("-" * 80)
                print(f"{'ID':<8} {'Ciudad':<20} {'Precio/noche':<15} {'Capacidad':<12} {'WiFi':<6}")
                print("-" * 80)
                
                for i, prop in enumerate(propiedades, 1):
                    prop_id = prop.get('propiedad_id', 'N/A')
                    ciudad = prop.get('ciudad_nombre', 'N/A')[:19]
                    precio = f"${prop.get('precio_noche', 0):.2f}"
                    capacidad = prop.get('capacidad_huespedes', 'N/A')
                    wifi = "Sí" if prop.get('wifi', False) else "No"
                    
                    print(f"{prop_id:<8} {ciudad:<20} {precio:<15} {capacidad:<12} {wifi:<6}")
                    
                    # Mostrar detalles adicionales de las primeras 3
                    if i <= 3:
                        print(f"         Nombre: {prop.get('propiedad_nombre', 'N/A')}")
                        print()
                
                print(f"\n📊 ESTADÍSTICAS:")
                # Agrupar por ciudad
                ciudades_count = {}
                precio_promedio = 0
                capacidad_total = 0
                wifi_count = 0
                
                for prop in propiedades:
                    ciudad = prop.get('ciudad_nombre', 'Sin ciudad')
                    ciudades_count[ciudad] = ciudades_count.get(ciudad, 0) + 1
                    precio_promedio += prop.get('precio_noche', 0)
                    capacidad_total += prop.get('capacidad_huespedes', 0)
                    if prop.get('wifi', False):
                        wifi_count += 1
                
                print(f"   🏙️ Ciudades con disponibilidad:")
                for ciudad, count in ciudades_count.items():
                    print(f"      • {ciudad}: {count} propiedades")
                
                print(f"   💰 Precio promedio: ${precio_promedio/len(propiedades):.2f}/noche")
                print(f"   👥 Capacidad promedio: {capacidad_total/len(propiedades):.1f} huéspedes")
                print(f"   📶 Con WiFi: {wifi_count}/{len(propiedades)} ({(wifi_count/len(propiedades)*100):.1f}%)")
                
            else:
                print(f"\n📭 No hay propiedades disponibles para {fecha_demo}")
        else:
            print(f"\n❌ Error en CU4: {result.get('error')}")
        
        print(f"\n🎯 FLUJO TÉCNICO CU4 (SOLO CASSANDRA):")
        print(f"   1️⃣ Cassandra: Buscar documentos por fecha")
        print(f"   2️⃣ Procesar: Extraer IDs de propiedades disponibles")
        print(f"   3️⃣ Mapear: Información básica (nombre, precio, capacidad)")
        print(f"   ⚡ Tiempo total: {tiempo_consulta:.3f}s")
        
        print("\n" + "="*70)

    except Exception as e:
        print(f"❌ Error en demo CU4: {str(e)}")
        logger.error("Error en demo CU4", error=str(e))


if __name__ == "__main__":
    asyncio.run(demo_cu4_propiedades_disponibles())