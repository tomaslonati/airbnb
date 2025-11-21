#!/usr/bin/env python3
"""
Test rápido del CU4 desde CLI.
"""

import asyncio
from datetime import date
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from services.reservations import ReservationService
from utils.logging import configure_logging

configure_logging()

async def test_cu4_cli():
    """Test rápido del CU4."""
    try:
        print("🏠 TEST CU4 - PROPIEDADES DISPONIBLES POR FECHA")
        print("="*60)
        
        service = ReservationService()
        fecha = date(2025, 12, 12)
        
        print(f"📅 Probando fecha: {fecha}")
        
        result = await service.get_propiedades_disponibles_fecha(fecha)
        
        if result.get("success"):
            propiedades = result.get("propiedades", [])
            print(f"\n✅ Éxito: {len(propiedades)} propiedades encontradas")
            
            if propiedades:
                print("\n📋 Lista de propiedades:")
                print("-"*60)
                print(f"{'ID':<8} {'Ciudad':<15} {'Precio':<10} {'Capacidad':<10}")
                print("-"*60)
                
                for prop in propiedades[:5]:  # Mostrar primeras 5
                    print(f"{prop.get('propiedad_id'):<8} {prop.get('ciudad_nombre', 'N/A'):<15} ${prop.get('precio_noche', 0):<9.2f} {prop.get('capacidad_huespedes', 'N/A'):<10}")
            
        else:
            print(f"\n❌ Error: {result.get('error')}")
            
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_cu4_cli())