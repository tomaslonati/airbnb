#!/usr/bin/env python3
"""
Script para encontrar IP alternativa de Neo4j AuraDB cuando falla DNS.
"""

import subprocess
import socket
import sys
import time

def ping_host(hostname):
    """Hace ping a un hostname para obtener su IP."""
    try:
        result = subprocess.run(['ping', '-n', '1', hostname], 
                              capture_output=True, text=True, timeout=10)
        output = result.stdout
        
        # Buscar la IP en la salida del ping
        import re
        match = re.search(r'\[(\d+\.\d+\.\d+\.\d+)\]', output)
        if match:
            ip = match.group(1)
            print(f"✅ Ping exitoso: {hostname} -> {ip}")
            return ip
        else:
            print(f"❌ Ping falló: {hostname}")
            return None
            
    except Exception as e:
        print(f"❌ Error en ping: {e}")
        return None

def nslookup_host(hostname):
    """Usa nslookup para resolver hostname."""
    try:
        result = subprocess.run(['nslookup', hostname], 
                              capture_output=True, text=True, timeout=10)
        output = result.stdout
        
        # Buscar IPs en la salida
        import re
        addresses = re.findall(r'Address:\s+(\d+\.\d+\.\d+\.\d+)', output)
        
        if addresses:
            for addr in addresses:
                print(f"✅ nslookup: {hostname} -> {addr}")
            return addresses[0]  # Retornar la primera IP
        else:
            print(f"❌ nslookup falló: {hostname}")
            return None
            
    except Exception as e:
        print(f"❌ Error en nslookup: {e}")
        return None

def test_socket_connection(ip, port=7687):
    """Prueba conexión socket directa."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Socket conectado: {ip}:{port}")
            return True
        else:
            print(f"❌ Socket falló: {ip}:{port} (código: {result})")
            return False
            
    except Exception as e:
        print(f"❌ Error en socket: {e}")
        return False

def main():
    """Función principal."""
    print("🔍 RESOLUCIÓN DE IP PARA Neo4j AuraDB")
    print("=" * 50)
    
    hostname = "26ff39e3.databases.neo4j.io"
    print(f"🎯 Hostname objetivo: {hostname}")
    print()
    
    # Método 1: Ping
    print("📡 Método 1: PING")
    print("-" * 20)
    ip_ping = ping_host(hostname)
    
    # Método 2: nslookup
    print("\n📡 Método 2: NSLOOKUP")  
    print("-" * 25)
    ip_nslookup = nslookup_host(hostname)
    
    # Recopilar IPs únicas
    ips_found = []
    if ip_ping:
        ips_found.append(ip_ping)
    if ip_nslookup and ip_nslookup not in ips_found:
        ips_found.append(ip_nslookup)
    
    # Probar conectividad
    print(f"\n🔌 PRUEBA CONECTIVIDAD")
    print("-" * 25)
    
    working_ips = []
    
    for ip in ips_found:
        print(f"Probando {ip}...")
        if test_socket_connection(ip):
            working_ips.append(ip)
    
    # Resultado final
    print(f"\n📋 RESULTADO FINAL")
    print("=" * 25)
    
    if working_ips:
        print("✅ IPs funcionando:")
        for ip in working_ips:
            print(f"   📍 {ip}")
        print(f"\n🎯 IP recomendada: {working_ips[0]}")
        
        # Generar configuración
        print(f"\n📝 CONFIGURACIÓN .ENV:")
        print(f"NEO4J_FALLBACK_IP={working_ips[0]}")
        print(f"NEO4J_ENABLE_FALLBACK=true")
        
    else:
        print("❌ No se encontraron IPs funcionando")
        print("🔧 Posibles soluciones:")
        print("   1. Verificar credenciales Neo4j")
        print("   2. Verificar firewall/proxy")
        print("   3. Contactar soporte AuraDB")

if __name__ == "__main__":
    main()