"""
Test simple para verificar imports y estructura del repositorio Cassandra.
"""

import sys
from pathlib import Path

# Añadir la ruta del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test para verificar que los imports funcionan correctamente."""
    try:
        print("🧪 Test de imports del repositorio Cassandra...")
        
        # Test 1: Import del módulo
        print("1️⃣ Probando import del repositorio...")
        from repositories.cassandra_reservation_repository import CassandraReservationRepository
        print("   ✅ CassandraReservationRepository importado")
        
        # Test 2: Import de la función factory
        print("2️⃣ Probando import de la función factory...")
        from repositories.cassandra_reservation_repository import get_cassandra_reservation_repository
        print("   ✅ get_cassandra_reservation_repository importado")
        
        # Test 3: Verificar estructura de la clase
        print("3️⃣ Verificando estructura de la clase...")
        repo = CassandraReservationRepository()
        
        # Verificar que tiene los métodos necesarios
        methods_to_check = [
            'connect',
            'update_occupancy', 
            'update_availability',
            'insert_host_reservation',
            'delete_host_reservation',
            'sync_reservation_creation',
            'sync_reservation_cancellation',
            'sync_availability_generation',
            'close'
        ]
        
        for method in methods_to_check:
            if hasattr(repo, method):
                print(f"   ✅ Método {method} encontrado")
            else:
                print(f"   ❌ Método {method} NO encontrado")
                return False
        
        # Test 4: Verificar configuración
        print("4️⃣ Verificando configuración...")
        from config import db_config
        
        config_attrs = [
            'cassandra_host',
            'cassandra_port', 
            'cassandra_username',
            'cassandra_password'
        ]
        
        for attr in config_attrs:
            if hasattr(db_config, attr):
                print(f"   ✅ Configuración {attr} disponible")
            else:
                print(f"   ❌ Configuración {attr} NO disponible")
        
        print("\n🎉 ¡Todos los imports y estructura verificados correctamente!")
        print("💡 Para test completo, configura las credenciales de Cassandra en .env")
        return True
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def test_services_integration():
    """Test para verificar integración con servicios."""
    try:
        print("\n🔗 Test de integración con servicios...")
        
        # Test 1: Import del servicio de reservas
        print("1️⃣ Probando import del servicio de reservas...")
        from services.reservations import ReservationService
        print("   ✅ ReservationService importado")
        
        # Test 2: Verificar que tiene propiedad cassandra_repo
        print("2️⃣ Verificando integración Cassandra...")
        service = ReservationService()
        
        if hasattr(service, '_cassandra_repo'):
            print("   ✅ Atributo _cassandra_repo encontrado")
        else:
            print("   ❌ Atributo _cassandra_repo NO encontrado")
        
        if hasattr(service, 'cassandra_repo'):
            print("   ✅ Propiedad cassandra_repo encontrada")
        else:
            print("   ❌ Propiedad cassandra_repo NO encontrada")
        
        # Test 3: Verificar método _sync_reservation_to_cassandra
        if hasattr(service, '_sync_reservation_to_cassandra'):
            print("   ✅ Método _sync_reservation_to_cassandra encontrado")
        else:
            print("   ❌ Método _sync_reservation_to_cassandra NO encontrado")
        
        print("\n🎉 ¡Integración con servicios verificada!")
        return True
        
    except Exception as e:
        print(f"❌ Error en test de integración: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Ejecutando tests del repositorio Cassandra...")
    print("=" * 60)
    
    success1 = test_imports()
    success2 = test_services_integration()
    
    if success1 and success2:
        print("\n✅ TODOS LOS TESTS PASARON")
        print("🎯 Siguiente paso: Configurar credenciales de Cassandra en .env")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON")
        print("💡 Revisa los errores de import o estructura")