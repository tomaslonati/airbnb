#!/usr/bin/env python3
"""
Test rápido del nuevo updateOne con $set
Verificar si funciona excluir las PK del update
"""

import asyncio
from datetime import date
from db.cassandra import _update_ocupacion_ciudad


async def test_update_ocupacion():
    print("🧪 Probando updateOne con $set para ocupacion_por_ciudad")
    print("🔑 Test: Excluir PRIMARY KEY del $set")

    # Probar una actualización (upsert)
    try:
        print("\n1️⃣ Primera actualización (upsert)...")
        await _update_ocupacion_ciudad(
            ciudad_id=999,
            fecha=date(2025, 12, 25),  # Fecha específica para test
            occupied_delta=2,
            available_delta=10
        )
        print("✅ Primera actualización funcionó")

        # Probar otra actualización sobre la misma fecha
        print("\n2️⃣ Segunda actualización (update)...")
        await _update_ocupacion_ciudad(
            ciudad_id=999,
            fecha=date(2025, 12, 25),  # Misma fecha
            occupied_delta=1,
            available_delta=-2
        )
        print("✅ Segunda actualización funcionó (read-compute-write)")
        print("🎉 El patrón funciona!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_update_ocupacion())
