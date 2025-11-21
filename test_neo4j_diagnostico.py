#!/usr/bin/env python3
"""
Script de diagnóstico para Neo4j - Verifica conectividad y resuelve problemas DNS.
"""

from db.neo4j import get_client, is_available, resolve_neo4j_uri
from utils.logging import configure_logging, get_logger
from config import db_config
import sys
import socket
import asyncio
import time
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))


configure_logging()
logger = get_logger(__name__)


def test_dns_resolution():
    """Prueba la resolución DNS del hostname de Neo4j."""
    print("\n🔍 DIAGNÓSTICO DNS Neo4j")
    print("=" * 50)

    if not db_config.neo4j_uri:
        print("❌ NEO4J_URI no configurada")
        return False

    # Extraer hostname
    import re
    match = re.match(r'neo4j\+s?://([^:]+)', db_config.neo4j_uri)
    if not match:
        print(f"❌ URI inválida: {db_config.neo4j_uri}")
        return False

    hostname = match.group(1)
    print(f"🌐 Hostname: {hostname}")

    try:
        # Resolver DNS
        ip_address = socket.gethostbyname(hostname)
        print(f"✅ DNS resuelto: {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"❌ Error DNS: {e}")
        print(f"🔄 Fallback IP configurada: {db_config.neo4j_fallback_ip}")
        return False


def test_network_connectivity():
    """Prueba conectividad de red al puerto 7687."""
    print("\n🔌 PRUEBA CONECTIVIDAD RED")
    print("=" * 50)

    # Obtener URI resuelta
    uri = resolve_neo4j_uri()
    if not uri:
        print("❌ No se pudo resolver URI")
        return False

    print(f"🎯 URI a probar: {uri}")

    # Extraer hostname e IP
    import re
    match = re.match(r'neo4j\+s?://([^:]+)', uri)
    if not match:
        print(f"❌ URI inválida: {uri}")
        return False

    host = match.group(1)
    port = 7687

    try:
        # Crear socket con timeout
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        print(f"🔍 Probando conexión a {host}:{port}")
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"✅ Puerto {port} accesible")
            return True
        else:
            print(f"❌ Puerto {port} no accesible (código: {result})")
            return False

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False


async def test_neo4j_connection():
    """Prueba la conexión completa a Neo4j."""
    print("\n🔗 PRUEBA CONEXIÓN Neo4j")
    print("=" * 50)

    try:
        print("🚀 Iniciando conexión...")
        start_time = time.time()

        driver = await get_client()

        if driver:
            elapsed = time.time() - start_time
            print(f"✅ Conexión exitosa en {elapsed:.2f}s")

            # Ejecutar consulta simple
            result = driver.execute_query("RETURN 'Hello Neo4j!' as message")
            records = result[0]

            if records:
                message = records[0]["message"]
                print(f"✅ Consulta ejecutada: {message}")
                return True
            else:
                print("⚠️ Conexión establecida pero consulta falló")
                return False
        else:
            print("❌ No se pudo establecer conexión")
            return False

    except Exception as e:
        print(f"❌ Error en conexión: {e}")
        return False


def test_is_available():
    """Prueba la función is_available."""
    print("\n📊 PRUEBA is_available()")
    print("=" * 50)

    try:
        available = is_available()
        if available:
            print("✅ Neo4j reportado como disponible")
        else:
            print("❌ Neo4j reportado como NO disponible")
        return available
    except Exception as e:
        print(f"❌ Error en is_available(): {e}")
        return False


async def main():
    """Función principal del diagnóstico."""
    print("🏥 DIAGNÓSTICO COMPLETO Neo4j")
    print("=" * 60)
    print(f"📅 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 URI original: {db_config.neo4j_uri}")
    print(f"🔧 Fallback habilitado: {db_config.neo4j_enable_fallback}")
    print(f"🔧 IP Fallback: {db_config.neo4j_fallback_ip}")

    # Ejecutar todas las pruebas
    tests = [
        ("DNS Resolution", test_dns_resolution),
        ("Network Connectivity", test_network_connectivity),
        ("is_available()", test_is_available),
        ("Full Connection", test_neo4j_connection),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results[test_name] = False

    # Resumen final
    print("\n📋 RESUMEN DIAGNÓSTICO")
    print("=" * 50)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n🎯 Resultado final: {passed}/{total} pruebas exitosas")

    if passed == total:
        print("🎉 ¡Neo4j funcionando perfectamente!")
        return True
    elif passed >= total - 1:
        print("⚠️ Neo4j funcionando con problemas menores")
        return True
    else:
        print("🚨 Neo4j tiene problemas serios de conectividad")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Diagnóstico interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error fatal en diagnóstico: {e}")
        sys.exit(1)
