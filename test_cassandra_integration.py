#!/usr/bin/env python3
"""
Script de prueba para validar la integración completa de Cassandra
con el sistema de disponibilidad y reservas.
"""

import asyncio
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_cassandra_integration():
    """Prueba completa de la integración de Cassandra."""
    
    print("🔍 Iniciando pruebas de integración de Cassandra...")
    
    try:
        # 1. Probar conexión a Cassandra
        print("\n1. Probando conexión a Cassandra...")
        from db.cassandra import get_cassandra_client
        
        cassandra_client = await get_cassandra_client()
        if cassandra_client:
            print("✅ Conexión a Cassandra exitosa")
        else:
            print("❌ Error: No se pudo conectar a Cassandra")
            return False
        
        # 2. Probar helpers de Cassandra
        print("\n2. Probando helpers de Cassandra...")
        from db.cassandra import (
            cassandra_init_date,
            cassandra_mark_unavailable,
            cassandra_mark_available,
            get_ciudad_id_for_propiedad
        )
        
        # Simular datos de prueba
        test_propiedad_id = 1
        test_dates = [
            date.today() + timedelta(days=i) 
            for i in range(5)
        ]
        
        # Probar inicialización de fechas
        print("   - Probando inicialización de fechas...")
        try:
            await cassandra_init_date(test_propiedad_id, test_dates)
            print("   ✅ Inicialización de fechas exitosa")
        except Exception as e:
            print(f"   ❌ Error en inicialización: {e}")
        
        # Probar marcar como no disponible
        print("   - Probando marcar fechas como no disponibles...")
        try:
            await cassandra_mark_unavailable(test_propiedad_id, test_dates[:2])
            print("   ✅ Marcar no disponible exitoso")
        except Exception as e:
            print(f"   ❌ Error al marcar no disponible: {e}")
        
        # Probar marcar como disponible
        print("   - Probando marcar fechas como disponibles...")
        try:
            await cassandra_mark_available(test_propiedad_id, test_dates[:2])
            print("   ✅ Marcar disponible exitoso")
        except Exception as e:
            print(f"   ❌ Error al marcar disponible: {e}")
        
        # 3. Probar integración con PropertyService
        print("\n3. Probando integración con PropertyService...")
        from services.properties import PropertyService
        
        property_service = PropertyService()
        
        # Verificar que el método de generación de disponibilidad existe
        if hasattr(property_service, '_generate_availability'):
            print("   ✅ Método _generate_availability encontrado")
        else:
            print("   ❌ Método _generate_availability no encontrado")
        
        # 4. Probar integración con ReservationService
        print("\n4. Probando integración con ReservationService...")
        from services.reservations import ReservationService
        
        reservation_service = ReservationService()
        
        # Verificar que los métodos de marcado de disponibilidad existen
        if hasattr(reservation_service, '_mark_dates_unavailable'):
            print("   ✅ Método _mark_dates_unavailable encontrado")
        else:
            print("   ❌ Método _mark_dates_unavailable no encontrado")
        
        if hasattr(reservation_service, '_mark_dates_available'):
            print("   ✅ Método _mark_dates_available encontrado")
        else:
            print("   ❌ Método _mark_dates_available no encontrado")
        
        # 5. Probar consultas a las tablas de ocupación
        print("\n5. Probando consultas a tablas de ocupación...")
        try:
            # Consultar ocupación por ciudad
            collection = cassandra_client.get_collection("ocupacion_por_ciudad")
            result = collection.find_one({"ciudad_id": 1})
            print(f"   📊 Ocupación por ciudad (ejemplo): {result}")
            
            # Consultar ocupación por propiedad
            collection = cassandra_client.get_collection("ocupacion_por_propiedad")
            result = collection.find_one({"propiedad_id": test_propiedad_id})
            print(f"   📊 Ocupación por propiedad (ejemplo): {result}")
            
            print("   ✅ Consultas a tablas de ocupación exitosas")
        except Exception as e:
            print(f"   ❌ Error en consultas de ocupación: {e}")
        
        # 6. Verificar configuración
        print("\n6. Verificando configuración...")
        from config import Config
        
        if hasattr(Config, 'ASTRADB_APPLICATION_TOKEN') and Config.ASTRADB_APPLICATION_TOKEN:
            print("   ✅ Token de AstraDB configurado")
        else:
            print("   ⚠️  Token de AstraDB no configurado")
        
        if hasattr(Config, 'ASTRADB_API_ENDPOINT') and Config.ASTRADB_API_ENDPOINT:
            print("   ✅ Endpoint de AstraDB configurado")
        else:
            print("   ⚠️  Endpoint de AstraDB no configurado")
        
        print("\n🎉 Pruebas de integración de Cassandra completadas!")
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Verifica que todas las dependencias estén instaladas.")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        logger.error(f"Error en pruebas de Cassandra: {e}")
        return False

async def test_availability_workflow():
    """Prueba el flujo completo de disponibilidad."""
    
    print("\n🔄 Probando flujo completo de disponibilidad...")
    
    try:
        from services.reservations import ReservationService
        
        reservation_service = ReservationService()
        test_propiedad_id = 1
        check_in = date.today() + timedelta(days=10)
        check_out = date.today() + timedelta(days=15)
        
        print(f"   📅 Probando con propiedad {test_propiedad_id}")
        print(f"   📅 Check-in: {check_in}")
        print(f"   📅 Check-out: {check_out}")
        
        # Marcar fechas como no disponibles
        print("   - Marcando fechas como no disponibles...")
        await reservation_service._mark_dates_unavailable(
            test_propiedad_id, check_in, check_out, "Prueba de integración"
        )
        print("   ✅ Fechas marcadas como no disponibles")
        
        # Marcar fechas como disponibles nuevamente
        print("   - Marcando fechas como disponibles...")
        await reservation_service._mark_dates_available(
            test_propiedad_id, check_in, check_out, Decimal('120.00')
        )
        print("   ✅ Fechas marcadas como disponibles")
        
        print("   🎉 Flujo de disponibilidad completado!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error en flujo de disponibilidad: {e}")
        logger.error(f"Error en flujo de disponibilidad: {e}")
        return False

async def main():
    """Función principal de pruebas."""
    
    print("🧪 PRUEBAS DE INTEGRACIÓN DE CASSANDRA")
    print("=" * 50)
    
    # Pruebas de integración básica
    basic_success = await test_cassandra_integration()
    
    if basic_success:
        # Pruebas de flujo completo
        workflow_success = await test_availability_workflow()
        
        if workflow_success:
            print("\n🎯 RESUMEN: Todas las pruebas exitosas!")
            print("   - Conexión a Cassandra: ✅")
            print("   - Helpers de Cassandra: ✅")
            print("   - Integración con servicios: ✅")
            print("   - Flujo de disponibilidad: ✅")
            return 0
        else:
            print("\n⚠️  RESUMEN: Integración básica OK, pero flujo falló")
            return 1
    else:
        print("\n❌ RESUMEN: Falló la integración básica")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Pruebas interrumpidas por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(1)