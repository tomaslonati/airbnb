#!/usr/bin/env python3
"""
Test script para verificar CU1 - Tasa de ocupación por ciudad
Después del nuevo diseño read-compute-write
"""

import asyncio
from datetime import date
from cli.commands import CU1Command


async def test_cu1():
    print("🔍 Probando CU1 - Tasa de ocupación por ciudad")
    print("=" * 50)

    # Probar con Rosario (donde acabamos de crear reservas)
    cmd = CU1Command()

    # Mes actual
    print("\n📊 Ocupación en Rosario - Diciembre 2025:")
    result = await cmd.execute_async("Rosario", 2025, 12)

    if result:
        print(f"✅ Resultado obtenido: {result}")
    else:
        print("❌ No se obtuvo resultado")

if __name__ == "__main__":
    asyncio.run(test_cu1())
